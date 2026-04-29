/**
 * Activation entry point for the aiadev Spec Explorer.
 *
 * The body is split into a host-agnostic `wireExtension(host)` factory and a
 * thin `activate()` that builds the real `ExtensionHost` from `vscode.*` and
 * delegates to it. Tests exercise `wireExtension` against an in-memory fake
 * host (see `test/unit/extension.spec.ts`); we deliberately do not run
 * `@vscode/test-electron` for this task — that follow-up lives in plan.md
 * Phase 5.
 */

import type * as vscode from 'vscode';

import type { FileSystem } from './io/filesystem';
import type { GitHeadProvider } from './io/git';
import { buildSpecModels, type WorkspaceFolderInput } from './model/aggregate';
import {
  SpecTreeProvider,
  type IconFactories,
  type TreeItemCtors,
} from './views/specTreeProvider';
import {
  createSpecWatcher,
  type WatcherCtors,
} from './watcher';

export interface ExtensionHost {
  ctors: TreeItemCtors;
  fs: FileSystem;
  git: GitHeadProvider;
  iconFactories: IconFactories;
  registerTreeDataProvider(viewId: string, provider: unknown): { dispose(): void };
  registerCommand(commandId: string, handler: () => unknown): { dispose(): void };
  createOutputChannel(name: string): { appendLine(s: string): void; dispose(): void };
  getConfigurationValue<T>(section: string, key: string, defaultValue: T): T;
  getWorkspaceFolders(): readonly WorkspaceFolderInput[];
  onDidChangeWorkspaceFolders(handler: () => void): { dispose(): void };
  createSpecWatcher: typeof createSpecWatcher;
  watcherCtors: WatcherCtors;
}

export interface WiredExtension {
  provider: SpecTreeProvider;
  refresh(): Promise<void>;
  dispose(): void;
}

const VIEW_ID = 'aiadev.specExplorer';
const REFRESH_COMMAND = 'aiadev.specExplorer.refresh';
const OUTPUT_CHANNEL_NAME = 'aiadev Spec Explorer';
const WATCHER_PATTERN = '**/specs/*/{spec,plan,tasks}.md';
const CONFIG_SECTION = 'aiadev.specExplorer';
const CONFIG_KEY = 'specsRoot';
const CONFIG_DEFAULT = 'specs';

export function wireExtension(host: ExtensionHost): WiredExtension {
  const channel = host.createOutputChannel(OUTPUT_CHANNEL_NAME);
  const initialFolders = host.getWorkspaceFolders();
  const provider = new SpecTreeProvider(
    host.ctors,
    host.iconFactories,
    [],
    { multiRoot: initialFolders.length > 1 },
  );

  let disposed = false;
  const disposables: { dispose(): void }[] = [
    channel,
    host.registerTreeDataProvider(VIEW_ID, provider),
  ];

  async function refresh(): Promise<void> {
    if (disposed) {
      return;
    }
    try {
      const folders = host.getWorkspaceFolders();
      const specsRoot = host.getConfigurationValue<string>(
        CONFIG_SECTION,
        CONFIG_KEY,
        CONFIG_DEFAULT,
      );
      const specs = await buildSpecModels(host.fs, folders, specsRoot);
      if (disposed) {
        return;
      }
      provider.setSpecs(specs);
      provider.setMultiRoot(folders.length > 1);
      await Promise.all(
        folders.map(async (folder) => {
          try {
            const branch = await host.git.getCurrentBranch(folder.fsPath);
            if (!disposed) {
              provider.setCurrentBranch(folder.fsPath, branch);
            }
          } catch (err) {
            channel.appendLine(
              `git head error for folder "${folder.name}": ${(err as Error).message}`,
            );
          }
        }),
      );
    } catch (err) {
      channel.appendLine(`refresh error: ${(err as Error).message}`);
    }
  }

  disposables.push(host.registerCommand(REFRESH_COMMAND, refresh));
  disposables.push(
    host.onDidChangeWorkspaceFolders(() => {
      void refresh();
    }),
  );

  const watcher = host.createSpecWatcher(host.watcherCtors, {
    pattern: WATCHER_PATTERN,
    onChange: () => {
      void refresh();
    },
  });
  disposables.push(watcher);

  // Kick off initial population. Errors are logged inside refresh().
  void refresh();

  return {
    provider,
    refresh,
    dispose() {
      if (disposed) {
        return;
      }
      disposed = true;
      while (disposables.length > 0) {
        const d = disposables.pop()!;
        try {
          d.dispose();
        } catch {
          /* swallow — disposing must never throw out of activate teardown */
        }
      }
    },
  };
}

let wired: WiredExtension | undefined;

/** Test-only escape hatch: returns the wired extension after activation. */
export function getWiredExtension(): WiredExtension | undefined {
  return wired;
}

// activate() must return its exports; VS Code sets ext.exports to this return value,
// not to the CommonJS module.exports object.
export function activate(context: vscode.ExtensionContext): { getWiredExtension: typeof getWiredExtension } {
  wired = wireExtension(buildRealHost());
  context.subscriptions.push({ dispose: () => wired?.dispose() });
  return { getWiredExtension };
}

export function deactivate(): void {
  wired?.dispose();
  wired = undefined;
}

function buildRealHost(): ExtensionHost {
  // Lazy require so unit tests that import wireExtension never trigger the
  // host-only `vscode` module load. esbuild externalises `vscode`, so the
  // bundled output keeps these dynamic requires intact.
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const vscode = require('vscode') as typeof import('vscode');
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { VsCodeFileSystem } = require('./io/filesystem') as typeof import('./io/filesystem');
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { VsCodeGitHeadProvider } = require('./io/git') as typeof import('./io/git');
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { makeStatusIcon } = require('./views/icons') as typeof import('./views/icons');

  const fs = new VsCodeFileSystem();
  const git = new VsCodeGitHeadProvider();
  const ctors: TreeItemCtors = {
    TreeItem: vscode.TreeItem as unknown as TreeItemCtors['TreeItem'],
    TreeItemCollapsibleState: vscode.TreeItemCollapsibleState,
    EventEmitter: vscode.EventEmitter as unknown as TreeItemCtors['EventEmitter'],
    Uri: vscode.Uri as unknown as TreeItemCtors['Uri'],
    Range: vscode.Range as unknown as TreeItemCtors['Range'],
    ThemeIcon: vscode.ThemeIcon as unknown as TreeItemCtors['ThemeIcon'],
  };
  const iconFactories: IconFactories = {
    statusIcon: makeStatusIcon({
      ThemeIcon: vscode.ThemeIcon as unknown as new (id: string, color?: unknown) => unknown,
      ThemeColor: vscode.ThemeColor as unknown as new (id: string) => unknown,
    }),
  };
  const watcherCtors: WatcherCtors = {
    createFileSystemWatcher(pattern: string) {
      return vscode.workspace.createFileSystemWatcher(pattern);
    },
    setTimeout: ((cb: () => void, ms: number): number => {
      return setTimeout(cb, ms) as unknown as number;
    }) as WatcherCtors['setTimeout'],
    clearTimeout: (handle: number): void => {
      clearTimeout(handle as unknown as ReturnType<typeof setTimeout>);
    },
  };
  return {
    ctors,
    fs,
    git,
    iconFactories,
    registerTreeDataProvider(viewId, provider) {
      return vscode.window.registerTreeDataProvider(
        viewId,
        provider as vscode.TreeDataProvider<unknown>,
      );
    },
    registerCommand(commandId, handler) {
      return vscode.commands.registerCommand(commandId, handler);
    },
    createOutputChannel(name) {
      return vscode.window.createOutputChannel(name);
    },
    getConfigurationValue<T>(section: string, key: string, defaultValue: T): T {
      return vscode.workspace
        .getConfiguration(section)
        .get<T>(key, defaultValue);
    },
    getWorkspaceFolders() {
      const folders = vscode.workspace.workspaceFolders ?? [];
      return folders.map((f) => ({ name: f.name, fsPath: f.uri.fsPath }));
    },
    onDidChangeWorkspaceFolders(handler) {
      return vscode.workspace.onDidChangeWorkspaceFolders(() => handler());
    },
    createSpecWatcher,
    watcherCtors,
  };
}
