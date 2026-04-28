import type { PipelineState } from '../parser/types';

/**
 * Inputs for the pure pipeline-state derivation.
 *
 * The flags are independent booleans the caller computes from the parsed
 * SpecModel: presence of the three artifact files plus aggregated task
 * status.
 */
export interface PipelineStateInput {
  hasSpec: boolean;
  hasPlan: boolean;
  hasTasks: boolean;
  anyTaskInProgress: boolean;
  allTasksDone: boolean;
}

/**
 * Derive the 5-state pipeline badge for a spec, per spec Story 4.
 *
 * Decision table (top-to-bottom, first match wins):
 *   1. hasSpec && hasPlan && hasTasks && allTasksDone  → 'complete'
 *   2. hasSpec && hasPlan && hasTasks && anyTaskInProgress → 'implementing'
 *   3. hasSpec && hasPlan && hasTasks                  → 'spec → plan → tasks'
 *   4. hasSpec && hasPlan                              → 'spec → plan'
 *   5. hasSpec                                         → 'spec'
 *
 * `complete` is checked before `implementing` defensively: in normal data
 * `allTasksDone` implies `!anyTaskInProgress`, but ordering the check this
 * way means a malformed parse (both true) still resolves to the terminal
 * state rather than getting stuck reporting "implementing".
 *
 * If `!hasSpec` the row would not exist in the tree (the explorer only
 * lists directories that contain a spec.md), so this branch is theoretical;
 * we fall through to `'spec'` as the bottom of the pipeline.
 */
export function computePipelineState(input: PipelineStateInput): PipelineState {
  const { hasSpec, hasPlan, hasTasks, anyTaskInProgress, allTasksDone } = input;

  if (hasSpec && hasPlan && hasTasks && allTasksDone) {
    return 'complete';
  }
  if (hasSpec && hasPlan && hasTasks && anyTaskInProgress) {
    return 'implementing';
  }
  if (hasSpec && hasPlan && hasTasks) {
    return 'spec → plan → tasks';
  }
  if (hasSpec && hasPlan) {
    return 'spec → plan';
  }
  return 'spec';
}
