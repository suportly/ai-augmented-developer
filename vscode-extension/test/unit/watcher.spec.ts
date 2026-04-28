import { expect } from 'chai';
import {
  createSpecWatcher,
  FileSystemWatcherLike,
  WatcherCtors,
} from '../../src/watcher';

class FakeClock {
  private handle = 0;
  private pending = new Map<number, { cb: () => void; due: number }>();
  private now = 0;

  setTimeout = (cb: () => void, ms: number): number => {
    const h = ++this.handle;
    this.pending.set(h, { cb, due: this.now + ms });
    return h;
  };

  clearTimeout = (h: number): void => {
    this.pending.delete(h);
  };

  advance(ms: number): void {
    this.now += ms;
    for (const [h, p] of [...this.pending]) {
      if (p.due <= this.now) {
        this.pending.delete(h);
        p.cb();
      }
    }
  }

  pendingCount(): number {
    return this.pending.size;
  }
}

interface FakeWatcherHarness {
  watcher: FileSystemWatcherLike;
  fire: (kind: 'change' | 'create' | 'delete', fsPath: string) => void;
  disposed: boolean;
  capturedPattern: string;
}

function makeFakeWatcher(): { watcher: FileSystemWatcherLike; fire: FakeWatcherHarness['fire']; isDisposed: () => boolean } {
  const listeners: { [k: string]: ((uri: { fsPath: string }) => void)[] } = {
    change: [],
    create: [],
    delete: [],
  };
  let disposed = false;
  const fire = (kind: 'change' | 'create' | 'delete', fsPath: string) => {
    listeners[kind].forEach((l) => l({ fsPath }));
  };
  const watcher: FileSystemWatcherLike = {
    onDidChange(l) {
      listeners.change.push(l);
      return { dispose() {} };
    },
    onDidCreate(l) {
      listeners.create.push(l);
      return { dispose() {} };
    },
    onDidDelete(l) {
      listeners.delete.push(l);
      return { dispose() {} };
    },
    dispose() {
      disposed = true;
    },
  };
  return { watcher, fire, isDisposed: () => disposed };
}

function makeCtors(clock: FakeClock, harness: { watcher: FileSystemWatcherLike }, captured: { pattern?: string }): WatcherCtors {
  return {
    createFileSystemWatcher(pattern: string) {
      captured.pattern = pattern;
      return harness.watcher;
    },
    setTimeout: clock.setTimeout,
    clearTimeout: clock.clearTimeout,
  };
}

describe('createSpecWatcher', () => {
  it('fires onChange exactly once after debounce window for a single change event', () => {
    const clock = new FakeClock();
    const harness = makeFakeWatcher();
    const captured: { pattern?: string } = {};
    const calls: string[] = [];

    const sub = createSpecWatcher(makeCtors(clock, harness, captured), {
      pattern: '**/specs/*/{spec,plan,tasks}.md',
      debounceMs: 100,
      onChange: (p) => calls.push(p),
    });

    harness.fire('change', '/repo/specs/0001/spec.md');
    expect(calls).to.deep.equal([]);

    clock.advance(99);
    expect(calls).to.deep.equal([]);

    clock.advance(1);
    expect(calls).to.deep.equal(['/repo/specs/0001/spec.md']);

    sub.dispose();
  });

  it('collapses two events within debounceMs into a single onChange with the LAST path', () => {
    const clock = new FakeClock();
    const harness = makeFakeWatcher();
    const captured: { pattern?: string } = {};
    const calls: string[] = [];

    const sub = createSpecWatcher(makeCtors(clock, harness, captured), {
      pattern: '**/specs/*/{spec,plan,tasks}.md',
      debounceMs: 100,
      onChange: (p) => calls.push(p),
    });

    harness.fire('change', '/repo/specs/0001/spec.md');
    clock.advance(50);
    harness.fire('change', '/repo/specs/0001/plan.md');
    clock.advance(99);
    expect(calls).to.deep.equal([]);
    clock.advance(1);
    expect(calls).to.deep.equal(['/repo/specs/0001/plan.md']);

    sub.dispose();
  });

  it('dispose() prevents a pending callback from firing', () => {
    const clock = new FakeClock();
    const harness = makeFakeWatcher();
    const captured: { pattern?: string } = {};
    const calls: string[] = [];

    const sub = createSpecWatcher(makeCtors(clock, harness, captured), {
      pattern: '**/specs/*/{spec,plan,tasks}.md',
      debounceMs: 100,
      onChange: (p) => calls.push(p),
    });

    harness.fire('change', '/repo/specs/0001/spec.md');
    sub.dispose();
    clock.advance(500);
    expect(calls).to.deep.equal([]);
    expect(clock.pendingCount()).to.equal(0);
    expect(harness.isDisposed()).to.equal(true);
  });

  it('debounces onDidCreate events', () => {
    const clock = new FakeClock();
    const harness = makeFakeWatcher();
    const captured: { pattern?: string } = {};
    const calls: string[] = [];

    const sub = createSpecWatcher(makeCtors(clock, harness, captured), {
      pattern: '**/specs/*/{spec,plan,tasks}.md',
      debounceMs: 100,
      onChange: (p) => calls.push(p),
    });

    harness.fire('create', '/repo/specs/0002/spec.md');
    clock.advance(50);
    harness.fire('create', '/repo/specs/0002/plan.md');
    clock.advance(100);
    expect(calls).to.deep.equal(['/repo/specs/0002/plan.md']);

    sub.dispose();
  });

  it('debounces onDidDelete events', () => {
    const clock = new FakeClock();
    const harness = makeFakeWatcher();
    const captured: { pattern?: string } = {};
    const calls: string[] = [];

    const sub = createSpecWatcher(makeCtors(clock, harness, captured), {
      pattern: '**/specs/*/{spec,plan,tasks}.md',
      debounceMs: 100,
      onChange: (p) => calls.push(p),
    });

    harness.fire('delete', '/repo/specs/0003/tasks.md');
    clock.advance(100);
    expect(calls).to.deep.equal(['/repo/specs/0003/tasks.md']);

    sub.dispose();
  });

  it('uses default debounceMs of 100 when not provided', () => {
    const clock = new FakeClock();
    const harness = makeFakeWatcher();
    const captured: { pattern?: string } = {};
    const calls: string[] = [];

    const sub = createSpecWatcher(makeCtors(clock, harness, captured), {
      pattern: '**/specs/*/{spec,plan,tasks}.md',
      onChange: (p) => calls.push(p),
    });

    harness.fire('change', '/repo/specs/0001/spec.md');
    clock.advance(99);
    expect(calls).to.deep.equal([]);
    clock.advance(1);
    expect(calls).to.deep.equal(['/repo/specs/0001/spec.md']);

    sub.dispose();
  });

  it('passes the configured pattern to createFileSystemWatcher', () => {
    const clock = new FakeClock();
    const harness = makeFakeWatcher();
    const captured: { pattern?: string } = {};

    const sub = createSpecWatcher(makeCtors(clock, harness, captured), {
      pattern: '**/specs/*/{spec,plan,tasks}.md',
      onChange: () => {},
    });

    expect(captured.pattern).to.equal('**/specs/*/{spec,plan,tasks}.md');
    sub.dispose();
  });
});
