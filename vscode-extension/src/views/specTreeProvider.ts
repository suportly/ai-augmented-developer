/**
 * Tree-data provider for the aiadev Spec Explorer activity-bar view.
 *
 * T015 narrow scope: only the SpecNode parent rows are rendered. Subsequent
 * tasks expand the union:
 *   - TaskNode children → T017
 *   - EmptyStateNode → T016
 *   - ClarificationGroupNode → T020
 *   - Pipeline-state badge refinement → T022 (T015 just shows the SpecStatus
 *     text in the description)
 *   - Folder prefix for multi-root → T023
 *   - Branch highlight → T024
 *
 * The module follows the same factory pattern as `views/icons.ts`: the VS Code
 * constructors (`TreeItem`, `TreeItemCollapsibleState`, `EventEmitter`) are
 * injected so this file can be exercised by Node-only unit tests with stub
 * doubles. The real `vscode` module is bound at the activation site.
 *
 * Plan deviation: plan.md Phase 4 originally called for `@vscode/test-electron`
 * integration tests for this module. We are deliberately pivoting to
 * stub-based unit tests (mirroring T014 / icons.ts). A follow-up task will
 * layer real Extension Host integration tests on top once a stable surface
 * across T015–T024 is in place.
 */

import { assertNever, type SpecModel, type SpecStatus } from '../parser/types';

export interface SpecNode {
  readonly kind: 'spec';
  readonly model: SpecModel;
}

/**
 * Discriminated-union node type for the tree. Currently only `SpecNode` is
 * implemented; future tasks add `TaskNode`, `ClarificationGroupNode`,
 * `EmptyStateNode` etc.
 */
export type Node = SpecNode;

/**
 * Subset of `vscode.TreeItem` that this provider mutates. Kept structural so
 * stub doubles in tests do not need to implement the full host surface.
 */
export interface MutableTreeItem {
  label: string;
  description?: string;
  tooltip?: string;
  iconPath?: unknown;
  contextValue?: string;
  collapsibleState?: number;
}

export interface TreeItemCtors {
  TreeItem: new (label: string, collapsibleState: number) => MutableTreeItem;
  TreeItemCollapsibleState: { None: number; Collapsed: number; Expanded: number };
  EventEmitter: new <T>() => {
    event: unknown;
    fire(value: T): void;
    dispose(): void;
  };
}

export class SpecTreeProvider {
  private specs: readonly SpecModel[];
  private readonly emitter: {
    event: unknown;
    fire(value: undefined): void;
    dispose(): void;
  };

  public readonly onDidChangeTreeData: unknown;

  constructor(private readonly ctors: TreeItemCtors, specs: readonly SpecModel[]) {
    this.specs = specs;
    this.emitter = new ctors.EventEmitter<undefined>();
    this.onDidChangeTreeData = this.emitter.event;
  }

  setSpecs(next: readonly SpecModel[]): void {
    this.specs = next;
    this.emitter.fire(undefined);
  }

  getChildren(element?: Node): Node[] {
    if (!element) {
      return this.specs.map((model) => ({ kind: 'spec', model }));
    }
    switch (element.kind) {
      case 'spec':
        // T017 will replace this with TaskNode children.
        return [];
      default:
        return assertNever(element.kind);
    }
  }

  getTreeItem(element: Node): MutableTreeItem {
    switch (element.kind) {
      case 'spec':
        return this.renderSpec(element.model);
      default:
        return assertNever(element.kind);
    }
  }

  private renderSpec(model: SpecModel): MutableTreeItem {
    const label = model.title
      ? `${model.specId} — ${model.title}`
      : model.specDirName;

    const item = new this.ctors.TreeItem(
      label,
      this.ctors.TreeItemCollapsibleState.Collapsed,
    );
    item.description = formatStatus(model.status);
    item.tooltip = model.parseError
      ? model.parseError
      : `${model.specDirName} · ${model.specPath}`;
    item.contextValue = 'aiadev.spec';
    // iconPath intentionally left unset; T022 sets the pipeline-state icon.
    return item;
  }
}

/**
 * Maps a {@link SpecStatus} to the human-readable description badge shown
 * next to the spec label. Exhaustive over the union so adding a new status
 * is a `tsc` error until handled here.
 */
function formatStatus(status: SpecStatus): string {
  switch (status) {
    case 'draft':
      return 'Draft';
    case 'in review':
      return 'In review';
    case 'approved':
      return 'Approved';
    case 'implemented':
      return 'Implemented';
    case 'pr open':
      return 'PR Open';
    case 'unknown':
      return 'Unknown';
    default:
      return assertNever(status);
  }
}
