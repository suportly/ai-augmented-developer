/**
 * Debounced file-system watcher for aiadev spec artefacts.
 *
 * The implementation is dependency-injected so unit tests can drive it with
 * a fake clock and fake VS Code FileSystemWatcher (see test/unit/watcher.spec.ts).
 * In production, callers wire `createFileSystemWatcher` to
 * `vscode.workspace.createFileSystemWatcher` and `setTimeout`/`clearTimeout`
 * to the global timers.
 */

export interface FileSystemWatcherLike {
  onDidChange(listener: (uri: { fsPath: string }) => unknown): { dispose(): void };
  onDidCreate(listener: (uri: { fsPath: string }) => unknown): { dispose(): void };
  onDidDelete(listener: (uri: { fsPath: string }) => unknown): { dispose(): void };
  dispose(): void;
}

export interface WatcherCtors {
  createFileSystemWatcher(pattern: string): FileSystemWatcherLike;
  setTimeout(cb: () => void, ms: number): number;
  clearTimeout(handle: number): void;
}

export interface SpecWatcherOptions {
  pattern: string;
  debounceMs?: number;
  onChange: (changedFsPath: string) => void;
}

const DEFAULT_DEBOUNCE_MS = 100;

export function createSpecWatcher(
  ctors: WatcherCtors,
  opts: SpecWatcherOptions,
): { dispose(): void } {
  const debounceMs = opts.debounceMs ?? DEFAULT_DEBOUNCE_MS;
  const watcher = ctors.createFileSystemWatcher(opts.pattern);

  let pendingHandle: number | null = null;
  let lastPath: string | null = null;
  let disposed = false;

  const schedule = (uri: { fsPath: string }): void => {
    if (disposed) {
      return;
    }
    lastPath = uri.fsPath;
    if (pendingHandle !== null) {
      ctors.clearTimeout(pendingHandle);
      pendingHandle = null;
    }
    pendingHandle = ctors.setTimeout(() => {
      pendingHandle = null;
      const path = lastPath;
      lastPath = null;
      if (disposed || path === null) {
        return;
      }
      opts.onChange(path);
    }, debounceMs);
  };

  const subs = [
    watcher.onDidChange(schedule),
    watcher.onDidCreate(schedule),
    watcher.onDidDelete(schedule),
  ];

  return {
    dispose(): void {
      if (disposed) {
        return;
      }
      disposed = true;
      if (pendingHandle !== null) {
        ctors.clearTimeout(pendingHandle);
        pendingHandle = null;
      }
      for (const s of subs) {
        s.dispose();
      }
      watcher.dispose();
    },
  };
}
