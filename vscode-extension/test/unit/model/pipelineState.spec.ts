import { expect } from 'chai';

import {
  computePipelineState,
  PipelineStateInput,
} from '../../../src/model/pipelineState';
import type { PipelineState } from '../../../src/parser/types';

const baseInput: PipelineStateInput = {
  hasSpec: false,
  hasPlan: false,
  hasTasks: false,
  anyTaskInProgress: false,
  allTasksDone: false,
};

interface Case {
  name: string;
  input: Partial<PipelineStateInput>;
  expected: PipelineState;
}

const cases: Case[] = [
  {
    name: 'spec only → "spec"',
    input: { hasSpec: true },
    expected: 'spec',
  },
  {
    name: 'spec + plan only → "spec → plan"',
    input: { hasSpec: true, hasPlan: true },
    expected: 'spec → plan',
  },
  {
    name: 'spec + plan + tasks, none in_progress, not all done → "spec → plan → tasks"',
    input: { hasSpec: true, hasPlan: true, hasTasks: true },
    expected: 'spec → plan → tasks',
  },
  {
    name: 'spec + plan + tasks, anyTaskInProgress → "implementing"',
    input: {
      hasSpec: true,
      hasPlan: true,
      hasTasks: true,
      anyTaskInProgress: true,
    },
    expected: 'implementing',
  },
  {
    name: 'spec + plan + tasks, allTasksDone → "complete"',
    input: {
      hasSpec: true,
      hasPlan: true,
      hasTasks: true,
      allTasksDone: true,
    },
    expected: 'complete',
  },
  {
    name: 'allTasksDone takes precedence over anyTaskInProgress (defensive)',
    input: {
      hasSpec: true,
      hasPlan: true,
      hasTasks: true,
      anyTaskInProgress: true,
      allTasksDone: true,
    },
    expected: 'complete',
  },
  {
    name: '!hasSpec → "spec" (theoretical fallback)',
    input: {},
    expected: 'spec',
  },
];

describe('computePipelineState', () => {
  for (const c of cases) {
    it(c.name, () => {
      const result = computePipelineState({ ...baseInput, ...c.input });
      expect(result).to.equal(c.expected);
    });
  }
});
