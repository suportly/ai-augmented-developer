/**
 * Walk every workspace folder, enumerate spec directories beneath the
 * configured `specsRoot`, and build the in-memory `SpecModel[]` the tree-data
 * provider renders. Pure aside from the injected `FileSystem`.
 */

import type { FileSystem } from '../io/filesystem';
import { extractClarifications } from '../parser/clarifications';
import { parseSpec } from '../parser/spec';
import { parseTasks } from '../parser/tasks';
import type { SpecModel, Task } from '../parser/types';

import { computePipelineState } from './pipelineState';

export interface WorkspaceFolderInput {
  /** Display name of the workspace folder, e.g. `framework`. */
  name: string;
  /** Absolute fs path of the workspace folder. */
  fsPath: string;
}

const SPEC_ID_FROM_DIR = /^(\d+)-/;
const ABSOLUTE_PATH = /^(?:\/|[A-Za-z]:)/;

/** Last path segment of a POSIX path. Inputs without `/` are treated as one segment. */
function basename(path: string): string {
  const idx = path.lastIndexOf('/');
  return idx === -1 ? path : path.slice(idx + 1);
}

/** Parent directory of a POSIX path. Returns `''` for inputs without `/`. */
function dirname(path: string): string {
  const idx = path.lastIndexOf('/');
  if (idx === -1) return '';
  if (idx === 0) return '/';
  return path.slice(0, idx);
}

function specIdSortKey(specId: string): number {
  if (!/^\d+$/.test(specId)) {
    return Number.POSITIVE_INFINITY;
  }
  return Number.parseInt(specId, 10);
}

export async function buildSpecModels(
  fs: FileSystem,
  folders: readonly WorkspaceFolderInput[],
  specsRoot: string,
): Promise<SpecModel[]> {
  if (typeof specsRoot !== 'string' || specsRoot.length === 0) {
    throw new TypeError('specsRoot must be a non-empty workspace-relative path');
  }
  if (ABSOLUTE_PATH.test(specsRoot)) {
    throw new TypeError(
      `specsRoot must be workspace-relative, got absolute path: ${specsRoot}`,
    );
  }
  if (specsRoot.split(/[\\/]/).some((seg) => seg === '..')) {
    throw new TypeError(
      `specsRoot must not contain '..' segments, got: ${specsRoot}`,
    );
  }

  const models: SpecModel[] = [];

  for (const folder of folders) {
    const pattern = specsRoot + '/*/spec.md';
    const specPaths = await fs.findFiles(folder.fsPath, pattern);

    for (const specPath of specPaths) {
      const specDir = dirname(specPath);
      const specDirName = basename(specDir);

      const specText = await fs.readFileText(specPath);
      const header = parseSpec(specText);
      const clarifications = extractClarifications(specText);

      // planPath is used only for the existence probe; intentionally not stored on the model.
      const planPath = specDir + '/plan.md';
      const tasksPath = specDir + '/tasks.md';
      const [hasPlan, hasTasks] = await Promise.all([
        fs.exists(planPath),
        fs.exists(tasksPath),
      ]);

      let tasks: Task[] = [];
      if (hasTasks) {
        const tasksText = await fs.readFileText(tasksPath);
        tasks = parseTasks(tasksText);
      }

      const anyTaskInProgress = tasks.some((t) => t.status === 'in_progress');
      const allTasksDone =
        hasTasks && tasks.length > 0 && tasks.every((t) => t.status === 'done');

      const pipelineState = computePipelineState({
        hasSpec: true,
        hasPlan,
        hasTasks,
        anyTaskInProgress,
        allTasksDone,
      });

      const dirMatch = SPEC_ID_FROM_DIR.exec(specDirName);
      const specId = dirMatch
        ? dirMatch[1]
        : header.specId ?? specDirName;

      const model: SpecModel = {
        workspaceFolderName: folder.name,
        workspaceFolderUri: folder.fsPath,
        specDirName,
        specId,
        title: header.title ?? '',
        branch: header.branch,
        language: header.language,
        status: header.status,
        hasSpec: true,
        hasPlan,
        hasTasks,
        tasks,
        clarifications,
        pipelineState,
        specPath,
        tasksPath: hasTasks ? tasksPath : undefined,
      };
      if (header.parseError !== undefined) {
        model.parseError = header.parseError;
      }
      models.push(model);
    }
  }

  models.sort((a, b) => {
    const ka = specIdSortKey(a.specId);
    const kb = specIdSortKey(b.specId);
    const aNumeric = Number.isFinite(ka);
    const bNumeric = Number.isFinite(kb);
    if (aNumeric && bNumeric) {
      if (ka !== kb) {
        return kb - ka;
      }
    } else if (aNumeric !== bNumeric) {
      return aNumeric ? -1 : 1;
    }
    return a.workspaceFolderName.localeCompare(b.workspaceFolderName);
  });

  return models;
}
