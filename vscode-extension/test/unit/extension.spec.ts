import { expect } from 'chai';
import { wireExtension, type ExtensionHost } from '../../src/extension';
import { FakeFileSystem } from '../support/fakeFileSystem';
import { FakeGitHeadProvider } from '../support/fakeGitHeadProvider';
import {
  StubEventEmitter,
  StubRange,
  StubThemeColor,
  StubThemeIcon,
  StubTreeItem,
  StubTreeItemCollapsibleState,
  StubUri,
} from '../support/vscodeStub';
import type { TreeItemCtors, IconFactories } from '../../src/views/specTreeProvider';
import type { FileSystemWatcherLike, WatcherCtors } from '../../src/watcher';
import { makeStatusIcon } from '../../src/views/icons';
import { createSpecWatcher } from '../../src/watcher';

interface DisposableRecord {
  kind: string;
  disposed: boolean;
}

interface FakeWatcherHandle {
  fire: (kind: 'change' | 'create' | 'delete', fsPath: string) => void;
  isDisposed: () => boolean;
}

interface FakeHostState {
  registeredTreeProviders: { viewId: string; provider: unknown }[];
  registeredCommands: Map<string, () => unknown>;
  outputChannels: { name: string; lines: string[]; disposed: boolean }[];
  workspaceFolderHandlers: (() => void)[];
  disposables: DisposableRecord[];
  fakeWatcher: FakeWatcherHandle | null;
  watcherCtorsCalledWith: { pattern?: string } | null;
}

const ctors: TreeItemCtors = {
  TreeItem: StubTreeItem as unknown as TreeItemCtors['TreeItem'],
  TreeItemCollapsibleState: StubTreeItemCollapsibleState,
  EventEmitter: StubEventEmitter as unknown as TreeItemCtors['EventEmitter'],
  Uri: StubUri as unknown as TreeItemCtors['Uri'],
  Range: StubRange as unknown as TreeItemCtors['Range'],
  ThemeIcon: StubThemeIcon as unknown as TreeItemCtors['ThemeIcon'],
};

const iconFactories: IconFactories = {
  statusIcon: makeStatusIcon({
    ThemeIcon: StubThemeIcon as unknown as new (id: string, color?: unknown) => unknown,
    ThemeColor: StubThemeColor,
  }),
};

interface BuildHostInput {
  folders: { name: string; fsPath: string }[];
  files: Record<string, string>;
  branches: Record<string, string | undefined>;
  specsRoot?: string;
  fsThrowOnFindFiles?: boolean;
}

function buildFakeHost(input: BuildHostInput): {
  host: ExtensionHost;
  state: FakeHostState;
  fs: FakeFileSystem;
  git: FakeGitHeadProvider;
} {
  const baseFs = new FakeFileSystem(input.files);
  const fs = input.fsThrowOnFindFiles
    ? ({
        findFiles: async (): Promise<string[]> => {
          throw new Error('boom');
        },
        readFileText: baseFs.readFileText.bind(baseFs),
        exists: baseFs.exists.bind(baseFs),
      } as unknown as FakeFileSystem)
    : baseFs;
  const git = new FakeGitHeadProvider(input.branches);

  const state: FakeHostState = {
    registeredTreeProviders: [],
    registeredCommands: new Map(),
    outputChannels: [],
    workspaceFolderHandlers: [],
    disposables: [],
    fakeWatcher: null,
    watcherCtorsCalledWith: null,
  };

  const trackDisposable = (kind: string): DisposableRecord => {
    const record: DisposableRecord = { kind, disposed: false };
    state.disposables.push(record);
    return record;
  };

  // Fake createSpecWatcher injected through host so tests can drive it.
  const fakeCreateSpecWatcher: typeof createSpecWatcher = (
    _watcherCtors,
    opts,
  ): { dispose(): void } => {
    let disposed = false;
    const handle: FakeWatcherHandle = {
      fire: (_kind, fsPath) => {
        if (!disposed) {
          opts.onChange(fsPath);
        }
      },
      isDisposed: () => disposed,
    };
    state.fakeWatcher = handle;
    const record = trackDisposable('watcher');
    return {
      dispose() {
        disposed = true;
        record.disposed = true;
      },
    };
  };

  // Stub watcher ctors — only used to be passed through.
  const watcherCtors: WatcherCtors = {
    createFileSystemWatcher(_pattern: string): FileSystemWatcherLike {
      return {
        onDidChange: () => ({ dispose() {} }),
        onDidCreate: () => ({ dispose() {} }),
        onDidDelete: () => ({ dispose() {} }),
        dispose() {},
      };
    },
    setTimeout: ((cb: () => void, _ms: number) => {
      // immediately invoke; not used in fake path but typesafe
      void cb;
      return 0;
    }) as unknown as WatcherCtors['setTimeout'],
    clearTimeout: () => {},
  };

  const host: ExtensionHost = {
    ctors,
    fs: fs as unknown as ExtensionHost['fs'],
    git,
    iconFactories,
    registerTreeDataProvider(viewId, provider) {
      state.registeredTreeProviders.push({ viewId, provider });
      const record = trackDisposable('treeProvider');
      return {
        dispose() {
          record.disposed = true;
        },
      };
    },
    registerCommand(commandId, handler) {
      state.registeredCommands.set(commandId, handler);
      const record = trackDisposable('command');
      return {
        dispose() {
          record.disposed = true;
        },
      };
    },
    createOutputChannel(name) {
      const channel = { name, lines: [] as string[], disposed: false };
      state.outputChannels.push(channel);
      return {
        appendLine(s: string) {
          channel.lines.push(s);
        },
        dispose() {
          channel.disposed = true;
        },
      };
    },
    getConfigurationValue<T>(_section: string, _key: string, defaultValue: T): T {
      if (input.specsRoot !== undefined) {
        return input.specsRoot as unknown as T;
      }
      return defaultValue;
    },
    getWorkspaceFolders() {
      return input.folders;
    },
    onDidChangeWorkspaceFolders(handler) {
      state.workspaceFolderHandlers.push(handler);
      const record = trackDisposable('wsFoldersListener');
      return {
        dispose() {
          record.disposed = true;
        },
      };
    },
    createSpecWatcher: fakeCreateSpecWatcher,
    watcherCtors,
  };

  return { host, state, fs: baseFs, git };
}

const SPEC_ONE = `# Feature specification: Alpha

**Branch:** \`feature/alpha\`
**Status:** Draft
**Spec ID:** 0001

---
`;

const SPEC_TWO = `# Feature specification: Beta

**Branch:** \`feature/beta\`
**Status:** Draft
**Spec ID:** 0002

---
`;

const TASKS_TWO = `# Tasks

- [ ] T001 — first task
- [ ] T002 — second task
`;

function makeTwoSpecFiles(repoPath: string): Record<string, string> {
  return {
    [`${repoPath}/specs/0001-alpha/spec.md`]: SPEC_ONE,
    [`${repoPath}/specs/0002-beta/spec.md`]: SPEC_TWO,
    [`${repoPath}/specs/0002-beta/tasks.md`]: TASKS_TWO,
  };
}

async function flush(): Promise<void> {
  // Allow microtasks to settle (initial refresh runs as a Promise).
  await new Promise((r) => setImmediate(r));
  await new Promise((r) => setImmediate(r));
  await new Promise((r) => setImmediate(r));
}

describe('wireExtension', () => {
  it('registers the tree provider for aiadev.specExplorer', async () => {
    const { host, state } = buildFakeHost({
      folders: [{ name: 'repo', fsPath: '/repo' }],
      files: makeTwoSpecFiles('/repo'),
      branches: { '/repo': 'feature/alpha' },
    });

    const wired = wireExtension(host);
    await flush();

    expect(state.registeredTreeProviders).to.have.lengthOf(1);
    expect(state.registeredTreeProviders[0].viewId).to.equal('aiadev.specExplorer');
    wired.dispose();
  });

  it('registers the aiadev.specExplorer.refresh command', async () => {
    const { host, state } = buildFakeHost({
      folders: [{ name: 'repo', fsPath: '/repo' }],
      files: makeTwoSpecFiles('/repo'),
      branches: { '/repo': 'feature/alpha' },
    });

    const wired = wireExtension(host);
    await flush();

    expect(state.registeredCommands.has('aiadev.specExplorer.refresh')).to.equal(true);
    wired.dispose();
  });

  it("creates an output channel named 'aiadev Spec Explorer'", async () => {
    const { host, state } = buildFakeHost({
      folders: [{ name: 'repo', fsPath: '/repo' }],
      files: makeTwoSpecFiles('/repo'),
      branches: { '/repo': 'feature/alpha' },
    });

    const wired = wireExtension(host);
    await flush();

    expect(state.outputChannels).to.have.lengthOf(1);
    expect(state.outputChannels[0].name).to.equal('aiadev Spec Explorer');
    wired.dispose();
  });

  it('after initial refresh getChildren returns two SpecNodes', async () => {
    const { host } = buildFakeHost({
      folders: [{ name: 'repo', fsPath: '/repo' }],
      files: makeTwoSpecFiles('/repo'),
      branches: { '/repo': 'feature/alpha' },
    });

    const wired = wireExtension(host);
    await flush();

    const children = wired.provider.getChildren();
    expect(children).to.have.lengthOf(2);
    expect(children.every((c) => c.kind === 'spec')).to.equal(true);
    wired.dispose();
  });

  it('calls git.getCurrentBranch once per workspace folder; current branch surfaces as ● current', async () => {
    const calls: string[] = [];
    const { host } = buildFakeHost({
      folders: [{ name: 'repo', fsPath: '/repo' }],
      files: makeTwoSpecFiles('/repo'),
      branches: { '/repo': 'feature/alpha' },
    });
    const originalGet = host.git.getCurrentBranch.bind(host.git);
    host.git.getCurrentBranch = async (path: string) => {
      calls.push(path);
      return originalGet(path);
    };

    const wired = wireExtension(host);
    await flush();

    expect(calls).to.deep.equal(['/repo']);

    const children = wired.provider.getChildren();
    const specOne = children.find((n) => n.kind === 'spec' && n.model.specId === '0001');
    expect(specOne).to.not.equal(undefined);
    const item = wired.provider.getTreeItem(specOne!);
    expect(item.description ?? '').to.contain('● current');

    const specTwo = children.find((n) => n.kind === 'spec' && n.model.specId === '0002');
    const itemTwo = wired.provider.getTreeItem(specTwo!);
    expect(itemTwo.description ?? '').to.not.contain('● current');

    wired.dispose();
  });

  it('triggering watcher onChange re-runs refresh (git.getCurrentBranch called again)', async () => {
    const calls: string[] = [];
    const { host, state } = buildFakeHost({
      folders: [{ name: 'repo', fsPath: '/repo' }],
      files: makeTwoSpecFiles('/repo'),
      branches: { '/repo': 'feature/alpha' },
    });
    const originalGet = host.git.getCurrentBranch.bind(host.git);
    host.git.getCurrentBranch = async (path: string) => {
      calls.push(path);
      return originalGet(path);
    };

    const wired = wireExtension(host);
    await flush();
    expect(calls).to.deep.equal(['/repo']);

    expect(state.fakeWatcher).to.not.equal(null);
    state.fakeWatcher!.fire('change', '/repo/specs/0001-alpha/spec.md');
    await flush();

    expect(calls).to.deep.equal(['/repo', '/repo']);
    wired.dispose();
  });

  it('dispose() disposes every registered disposable', async () => {
    const { host, state } = buildFakeHost({
      folders: [{ name: 'repo', fsPath: '/repo' }],
      files: makeTwoSpecFiles('/repo'),
      branches: { '/repo': 'feature/alpha' },
    });

    const wired = wireExtension(host);
    await flush();

    expect(state.disposables.length).to.be.greaterThan(0);
    wired.dispose();
    for (const d of state.disposables) {
      expect(d.disposed, `disposable ${d.kind}`).to.equal(true);
    }
    expect(state.outputChannels[0].disposed).to.equal(true);
  });

  it('logs an error and does not crash when buildSpecModels throws', async () => {
    const { host, state } = buildFakeHost({
      folders: [{ name: 'repo', fsPath: '/repo' }],
      files: makeTwoSpecFiles('/repo'),
      branches: { '/repo': 'feature/alpha' },
      fsThrowOnFindFiles: true,
    });

    const wired = wireExtension(host);
    await flush();

    expect(state.outputChannels[0].lines.length).to.be.greaterThan(0);
    expect(state.outputChannels[0].lines.join('\n')).to.contain('boom');
    // Provider is still operational and contains no specs.
    const children = wired.provider.getChildren();
    expect(children).to.have.lengthOf(1);
    expect(children[0].kind).to.equal('empty');
    wired.dispose();
  });

  it('with two workspace folders, SpecNode labels carry the [folder] prefix', async () => {
    const files = {
      ...makeTwoSpecFiles('/repoA'),
      ...makeTwoSpecFiles('/repoB'),
    };
    const { host } = buildFakeHost({
      folders: [
        { name: 'repoA', fsPath: '/repoA' },
        { name: 'repoB', fsPath: '/repoB' },
      ],
      files,
      branches: { '/repoA': 'feature/alpha', '/repoB': 'feature/beta' },
    });

    const wired = wireExtension(host);
    await flush();

    const children = wired.provider.getChildren();
    expect(children.length).to.be.greaterThan(0);
    for (const node of children) {
      if (node.kind === 'spec') {
        const item = wired.provider.getTreeItem(node);
        expect(item.label.startsWith('[')).to.equal(
          true,
          `expected multi-root prefix on label, got: ${item.label}`,
        );
      }
    }
    wired.dispose();
  });
});
