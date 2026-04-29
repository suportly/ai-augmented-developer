/**
 * Core types for the spec explorer parser layer.
 *
 * These shapes are the contract between the pure parsers (`parser/spec.ts`,
 * `parser/clarifications.ts`, `parser/tasks.ts`) and the tree-data provider
 * that renders them in the activity-bar view.
 */

export type TaskStatus =
  | 'pending'
  | 'in_progress'
  | 'blocked'
  | 'done'
  | 'unknown';

export type SpecStatus =
  | 'draft'
  | 'in review'
  | 'approved'
  | 'implemented'
  | 'pr open'
  | 'unknown';

export interface Task {
  /** Task id, e.g. `T001`. */
  id: string;
  title: string;
  status: TaskStatus;
  /** 1-based line number of the `### T###` heading inside `tasks.md`. */
  line: number;
}

export interface Clarification {
  /** Clarification id, e.g. `cl-1`. */
  id: string;
  question: string;
  /** 1-based line number inside `spec.md`. */
  line: number;
}

export type PipelineState =
  | 'spec'
  | 'spec → plan'
  | 'spec → plan → tasks'
  | 'implementing'
  | 'complete';

export interface SpecModel {
  workspaceFolderName: string;
  /** String form of `vscode.Uri.fsPath` of the workspace folder. */
  workspaceFolderUri: string;
  /** Directory name of the spec, e.g. `0012-vscode-spec-explorer`. */
  specDirName: string;
  /** Numeric prefix of `specDirName`, e.g. `0012`. */
  specId: string;
  /** Human title parsed from `# Feature specification: ...`. */
  title: string;
  branch: string | undefined;
  language: string | undefined;
  /** Parsed from `**Status:**`; `'unknown'` when absent or unparseable. */
  status: SpecStatus;
  hasSpec: boolean;
  hasPlan: boolean;
  hasTasks: boolean;
  tasks: Task[];
  clarifications: Clarification[];
  pipelineState: PipelineState;
  /** Populated when `status === 'unknown'` or another parse failure occurs. */
  parseError?: string;
  /** Absolute filesystem path to `spec.md`. */
  specPath: string;
  /** Absolute filesystem path to `tasks.md`, when present. */
  tasksPath: string | undefined;
}

/**
 * Exhaustiveness helper. Call from a `default:` branch in a `switch` over a
 * tagged-union type — the typechecker rejects the call if the union grows a
 * new tag the switch does not handle.
 */
export function assertNever(x: never): never {
  throw new Error(`Unexpected value: ${String(x)}`);
}
