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
  type Clarification,
  type PipelineState,
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
 * Parent row for the per-spec clarifications group ("Clarifications (N)").
 * Carries a back-reference to the owning {@link SpecModel} so children can
 * be enumerated and so future navigation commands (T021) can locate the
 * source `spec.md`. Only emitted when `specModel.clarifications.length > 0`.
 * Spec Story 3 scenario 1 / task T020.
 */
export interface ClarificationGroupNode {
  readonly kind: 'clGroup';
  readonly specModel: SpecModel;
}

/**
 * One row per clarification under its parent {@link ClarificationGroupNode}.
 * Carries both a back-reference to the owning {@link SpecModel} and the
 * specific {@link Clarification} record so the row can render id + question
 * text without re-querying the aggregate.
 */
export interface ClarificationNode {
  readonly kind: 'cl';
  readonly specModel: SpecModel;
  readonly clarification: Clarification;
}

/**
 * Discriminated-union node type for the tree.
 */
export type Node =
  | SpecNode
  | TaskNode
  | EmptyStateNode
  | ClarificationGroupNode
  | ClarificationNode;

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
  ThemeIcon: new (id: string, color?: unknown) => unknown;
}

/**
 * Bundle of icon-producing factories. Currently a single `statusIcon`; future
 * tasks (T022 pipeline-state badge) will add fields without breaking
 * existing callers.
 */
export interface IconFactories {
  statusIcon: (status: TaskStatus) => unknown;
}

/**
 * Optional constructor settings for the provider. Currently only carries the
 * multi-root flag (T023); future tasks may extend this without breaking
 * existing call sites.
 */
export interface SpecTreeProviderOptions {
  /**
   * When true, SpecNode labels are prefixed with `[<workspaceFolderName>] `.
   * Set from `vscode.workspace.workspaceFolders.length > 1` at the activation
   * site (T025). Defaults to false.
   */
  multiRoot?: boolean;
}

export class SpecTreeProvider {
  private specs: readonly SpecModel[];
  private multiRoot: boolean;
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
    options?: SpecTreeProviderOptions,
  ) {
    this.specs = specs;
    this.multiRoot = options?.multiRoot ?? false;
    this.emitter = new ctors.EventEmitter<undefined>();
    this.onDidChangeTreeData = this.emitter.event;
  }

  setSpecs(next: readonly SpecModel[]): void {
    this.specs = next;
    this.emitter.fire(undefined);
  }

  /**
   * Update the multi-root flag mid-session (e.g. after a folder is added or
   * removed via `vscode.workspace.onDidChangeWorkspaceFolders`). Fires the
   * change event only when the value actually changes so the tree re-renders
   * with or without the `[<folderName>] ` prefix on SpecNode labels.
   */
  setMultiRoot(value: boolean): void {
    if (this.multiRoot === value) {
      return;
    }
    this.multiRoot = value;
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
      case 'spec': {
        const taskNodes: Node[] = element.model.tasks.map((task) => ({
          kind: 'task',
          specModel: element.model,
          task,
        }));
        if (element.model.clarifications.length > 0) {
          taskNodes.push({ kind: 'clGroup', specModel: element.model });
        }
        return taskNodes;
      }
      case 'clGroup':
        return element.specModel.clarifications.map((clarification) => ({
          kind: 'cl',
          specModel: element.specModel,
          clarification,
        }));
      case 'cl':
        return [];
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
      case 'clGroup':
        return this.renderClarificationGroup(element.specModel);
      case 'cl':
        return this.renderClarification(element.clarification, element.specModel);
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
    const baseLabel = model.title
      ? `${model.specId} — ${model.title}`
      : model.specDirName;
    const label = this.multiRoot
      ? `[${model.workspaceFolderName}] ${baseLabel}`
      : baseLabel;

    const item = new this.ctors.TreeItem(
      label,
      this.ctors.TreeItemCollapsibleState.Collapsed,
    );
    item.description = formatSpecDescription(model);
    item.tooltip = model.parseError
      ? model.parseError
      : formatSpecTooltip(model);
    item.contextValue = 'aiadev.spec';
    item.iconPath = new this.ctors.ThemeIcon(
      pipelineStateIconId(model.pipelineState),
    );
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

  private renderClarificationGroup(specModel: SpecModel): MutableTreeItem {
    const count = specModel.clarifications.length;
    const item = new this.ctors.TreeItem(
      `Clarifications (${count})`,
      this.ctors.TreeItemCollapsibleState.Expanded,
    );
    item.tooltip = `${count} unresolved clarification${count === 1 ? '' : 's'}`;
    item.iconPath = new this.ctors.ThemeIcon('question');
    item.contextValue = 'aiadev.clarificationGroup';
    // description intentionally left undefined.
    return item;
  }

  private renderClarification(
    clarification: Clarification,
    specModel: SpecModel,
  ): MutableTreeItem {
    const item = new this.ctors.TreeItem(
      clarification.id,
      this.ctors.TreeItemCollapsibleState.None,
    );
    item.description = truncateQuestion(clarification.question);
    item.tooltip = clarification.question;
    item.contextValue = 'aiadev.clarification';
    // T021: clicking the row opens spec.md and reveals the marker line.
    // VS Code Position is 0-based; clarification.line is 1-based.
    // specPath is always defined: a SpecModel only exists when spec.md was found.
    const markerLine = clarification.line - 1;
    item.command = {
      command: 'vscode.open',
      title: 'Open clarification',
      arguments: [
        this.ctors.Uri.file(specModel.specPath),
        {
          selection: new this.ctors.Range(markerLine, 0, markerLine, 0),
        },
      ],
    };
    return item;
  }
}

/**
 * Truncate a clarification question to {@link CLARIFICATION_DESCRIPTION_LIMIT}
 * characters, appending an ellipsis when the source string was longer. The
 * full text is preserved on `item.tooltip` so users can still read it.
 */
function truncateQuestion(question: string): string {
  if (question.length <= CLARIFICATION_DESCRIPTION_LIMIT) {
    return question;
  }
  return question.slice(0, CLARIFICATION_DESCRIPTION_LIMIT) + '…';
}

const CLARIFICATION_DESCRIPTION_LIMIT = 80;

/**
 * Build the badge text shown next to a spec label. The pipeline-state badge
 * (T022) takes precedence over the SpecStatus, which is now surfaced via the
 * tooltip. The done counter is appended only for the two states where a
 * tasks.md exists with concrete work to track: `spec → plan → tasks` and
 * `implementing`. `complete` deliberately omits the counter — every task is
 * done by definition, so the bare `complete` badge is clearer.
 */
function formatSpecDescription(model: SpecModel): string {
  const badge = model.pipelineState;
  const total = model.tasks.length;
  const showCounter =
    total > 0 &&
    (model.pipelineState === 'spec → plan → tasks' ||
      model.pipelineState === 'implementing');
  if (!showCounter) {
    return badge;
  }
  const done = model.tasks.filter((t) => t.status === 'done').length;
  return `${badge} · ${done} / ${total} done`;
}

/**
 * Build the multi-line tooltip shown on hover. Surfaces the SpecStatus (no
 * longer in the description), the next pipeline action, and the absolute
 * spec path. Callers must skip this when `parseError` is set — the parse
 * error message wins so users see the underlying problem first.
 */
function formatSpecTooltip(model: SpecModel): string {
  return [
    `${model.specDirName} · ${model.pipelineState}`,
    `Status: ${formatStatus(model.status)}`,
    `Next: ${nextActionHint(model.pipelineState)}`,
    model.specPath,
  ].join('\n');
}

function nextActionHint(state: PipelineState): string {
  switch (state) {
    case 'spec':
      return 'run /aiadev:plan';
    case 'spec → plan':
      return 'run /aiadev:tasks';
    case 'spec → plan → tasks':
      return 'run /aiadev:implement';
    case 'implementing':
      return 'continue running /aiadev:implement';
    case 'complete':
      return 'run /aiadev:analyze then /aiadev:requesting-code-review';
    default:
      return assertNever(state);
  }
}

function pipelineStateIconId(state: PipelineState): string {
  switch (state) {
    case 'spec':
    case 'spec → plan':
    case 'spec → plan → tasks':
      return 'symbol-file';
    case 'implementing':
      return 'sync~spin';
    case 'complete':
      return 'check-all';
    default:
      return assertNever(state);
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
