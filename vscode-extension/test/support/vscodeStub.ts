/**
 * Minimal stubs for the `vscode` module surface used by the view layer.
 *
 * Reasoning: the real `vscode` module is provided by the Extension Host at
 * runtime and is unavailable inside Node-only unit tests. esbuild externalises
 * it at build time. The view-layer modules therefore use a factory pattern
 * (see `src/views/icons.ts` / `src/views/specTreeProvider.ts`) where the
 * relevant constructors are injected. These stubs are the doubles passed in
 * from tests.
 *
 * Plan deviation note: plan.md Phase 4 originally called for
 * `@vscode/test-electron` integration tests for the tree provider. We are
 * intentionally pivoting to stub-based unit tests with the same factory
 * pattern T014 introduced for `icons.ts`. A follow-up task will layer real
 * Extension Host integration tests on top.
 *
 * The stubs are deliberately structural rather than nominal — they do not
 * implement the full `vscode` typing surface, only the fields the view code
 * actually reads or writes. Tests cast through `unknown`/`as any` at the
 * factory boundary.
 */

export class StubTreeItem {
  public description?: string;
  public tooltip?: string;
  public iconPath?: unknown;
  public contextValue?: string;
  constructor(public label: string, public collapsibleState: number) {}
}

export const StubTreeItemCollapsibleState = {
  None: 0,
  Collapsed: 1,
  Expanded: 2,
} as const;

/**
 * Captures `.fire()` invocations so tests can assert refresh semantics.
 *
 * The real `vscode.EventEmitter` exposes `event` (a subscribable function)
 * and `fire` / `dispose`. Tests do not subscribe via `event`; they read
 * `fired` directly to verify behaviour.
 */
export class StubEventEmitter<T> {
  public readonly fired: T[] = [];
  public disposed = false;
  public readonly event: unknown = () => {
    /* no-op subscription stub */
  };
  fire(value: T): void {
    this.fired.push(value);
  }
  dispose(): void {
    this.disposed = true;
  }
}

export class StubThemeIcon {
  constructor(public id: string, public color?: StubThemeColor) {}
}

export class StubThemeColor {
  constructor(public id: string) {}
}

export class StubUri {
  private constructor(public fsPath: string) {}
  static file(path: string): StubUri {
    return new StubUri(path);
  }
}
