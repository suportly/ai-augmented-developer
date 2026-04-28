/**
 * Tree-data provider for the aiadev Spec Explorer activity-bar view.
 *
 * Scope grows incrementally with the pipeline tasks:
 *   - SpecNode parent rows → T015
 *   - EmptyStateNode → T016
 *   - TaskNode children + done counter → T017 (this file)
 *   - ClarificationGroupNode → T020
 *   - Pipeline-state badge refinement → T022
 *   - Folder prefix for multi-root → T023
 *   - Branch highlight → T024
 *
 * The module follows the same factory pattern as `views/icons.ts`: the VS Code
 * constructors (`TreeItem`, `TreeItemCollapsibleState`, `EventEmitter`) are
 * injected so this file can be exercised by Node-only unit tests with stub
 * doubles. The real `vscode` module is bound at the activation site.
 *
 * The status-icon factory is also injected (rather than imported from
 * `./icons`) so the provider has no compile-time dependency on the live VS
 * Code module surface and tests can stub the icon production wholesale.
 *
 * Plan deviation: plan.md Phase 4 originally called for `@vscode/test-electron`
 * integration tests for this module. We are deliberately pivoting to
 * stub-based unit tests (mirroring T014 / icons.ts). A follow-up task will
 * layer real Extension Host integration tests on top once a stable surface
 * across T015–T024 is in place.
 */

import {
  assertNever,
  type SpecModel,
  type SpecStatus,
  type Task,
  type TaskStatus,
} from '../parser/types';

export interface SpecNode {
  readonly kind: 'spec';
  readonly model: SpecModel;
}

/**
 * One row per task under its parent SpecNode. Carries a back-reference to the
 * owning {@link SpecModel} so commands wired to the tree item can locate
 * the source `tasks.md` without re-querying the aggregate.
 */
export interface TaskNode {
  readonly kind: 'task';
  readonly specModel: SpecModel;
  readonly task: Task;
}

/**
 * Placeholder row shown when the workspace contains zero parseable specs.
 * Spec Story 1 scenario 2 / task T016.
 */
export interface EmptyStateNode {
  readonly kind: 'empty';
}

/**
 * Discriminated-union node type for the tree. Future tasks add
 * `ClarificationGroupNode` etc.
 */
export type Node = SpecNode | TaskNode | EmptyStateNode;

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
  command?: TreeItemCommand;
}

/**
 * Subset of `vscode.Command` we set on tree items. The `arguments` array is
 * intentionally `unknown[]` — the structural shape varies per command id.
 */
export interface TreeItemCommand {
  command: string;
  title: string;
  arguments?: unknown[];
}

export interface TreeItemCtors {
  TreeItem: new (label: string, collapsibleState: number) => MutableTreeItem;
  TreeItemCollapsibleState: { None: number; Collapsed: number; Expanded: number };
  EventEmitter: new <T>() => {
    event: unknown;
    fire(value: T): void;
    dispose(): void;
  };
  Uri: { file(path: string): unknown };
  Range: new (
    startLine: number,
    startChar: number,
    endLine: number,
    endChar: number,
  ) => unknown;
}

/**
 * Bundle of icon-producing factories. Currently a single `statusIcon`; future
 * tasks (T022 pipeline-state badge) will add fields without breaking
 * existing callers.
 */
export interface IconFactories {
  statusIcon: (status: TaskStatus) => unknown;
}

export class SpecTreeProvider {
  private specs: readonly SpecModel[];
  private readonly emitter: {
    event: unknown;
    fire(value: undefined): void;
    dispose(): void;
  };

  public readonly onDidChangeTreeData: unknown;

  constructor(
    private readonly ctors: TreeItemCtors,
    private readonly iconFactories: IconFactories,
    specs: readonly SpecModel[],
  ) {
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
      if (this.specs.length === 0) {
        return [{ kind: 'empty' }];
      }
      return this.specs.map((model) => ({ kind: 'spec', model }));
    }
    switch (element.kind) {
      case 'spec':
        return element.model.tasks.map((task) => ({
          kind: 'task',
          specModel: element.model,
          task,
        }));
      case 'task':
        return [];
      case 'empty':
        return [];
      default:
        return assertNever(element);
    }
  }

  getTreeItem(element: Node): MutableTreeItem {
    switch (element.kind) {
      case 'spec':
        return this.renderSpec(element.model);
      case 'task':
        return this.renderTask(element.task, element.specModel);
      case 'empty':
        return this.renderEmpty();
      default:
        return assertNever(element);
    }
  }

  private renderEmpty(): MutableTreeItem {
    const item = new this.ctors.TreeItem(
      'No aiadev specs found in this workspace',
      this.ctors.TreeItemCollapsibleState.None,
    );
    item.tooltip =
      'Create a spec with /aiadev:specify in the integrated terminal.';
    item.contextValue = 'aiadev.empty';
    // description and iconPath intentionally left undefined.
    return item;
  }

  private renderSpec(model: SpecModel): MutableTreeItem {
    const label = model.title
      ? `${model.specId} — ${model.title}`
      : model.specDirName;

    const item = new this.ctors.TreeItem(
      label,
      this.ctors.TreeItemCollapsibleState.Collapsed,
    );
    item.description = formatSpecDescription(model);
    item.tooltip = model.parseError
      ? model.parseError
      : `${model.specDirName} · ${model.specPath}`;
    item.contextValue = 'aiadev.spec';
    // iconPath intentionally left unset; T022 sets the pipeline-state icon.
    return item;
  }

  private renderTask(task: Task, specModel: SpecModel): MutableTreeItem {
    const item = new this.ctors.TreeItem(
      `${task.id} — ${task.title}`,
      this.ctors.TreeItemCollapsibleState.None,
    );
    // description left undefined; T022 may surface a per-task hint here.
    item.tooltip = `${task.id} · status: ${task.status}`;
    item.iconPath = this.iconFactories.statusIcon(task.status);
    item.contextValue = 'aiadev.task';
    // T018: clicking the row opens tasks.md and reveals the heading line.
    // VS Code Position is 0-based; task.line is 1-based.
    if (specModel.tasksPath !== undefined) {
      const headingLine = task.line - 1;
      item.command = {
        command: 'vscode.open',
        title: 'Open task',
        arguments: [
          this.ctors.Uri.file(specModel.tasksPath),
          {
            selection: new this.ctors.Range(headingLine, 0, headingLine, 0),
          },
        ],
      };
    }
    return item;
  }
}

/**
 * Build the badge text shown next to a spec label. Always carries the status;
 * appends `D / N done` when the spec has at least one task.
 */
function formatSpecDescription(model: SpecModel): string {
  const status = formatStatus(model.status);
  const total = model.tasks.length;
  if (total === 0) {
    return status;
  }
  const done = model.tasks.filter((t) => t.status === 'done').length;
  return `${status} · ${done} / ${total} done`;
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
