/**
 * Compile-time exhaustiveness tests for parser/types.
 *
 * The primary value of this file is the `switch` statements below: if anyone
 * adds a new tag to `TaskStatus`, `SpecStatus`, or `PipelineState` without
 * also extending the corresponding switch, `tsc` will reject the call to
 * `assertNever(s)` because `s` will no longer be of type `never`. The runtime
 * `it()` blocks are smoke checks per variant; they would still pass if a tag
 * were silently dropped, so the typechecker is the real safety net here.
 */

import { expect } from 'chai';
import {
  TaskStatus,
  SpecStatus,
  PipelineState,
  assertNever,
} from '../../src/parser/types';

function describeTaskStatus(s: TaskStatus): string {
  switch (s) {
    case 'pending':
      return 'p';
    case 'in_progress':
      return 'i';
    case 'blocked':
      return 'b';
    case 'done':
      return 'd';
    case 'unknown':
      return 'u';
    default:
      return assertNever(s);
  }
}

function describeSpecStatus(s: SpecStatus): string {
  switch (s) {
    case 'draft':
      return 'D';
    case 'in review':
      return 'R';
    case 'approved':
      return 'A';
    case 'implemented':
      return 'I';
    case 'pr open':
      return 'P';
    case 'unknown':
      return 'U';
    default:
      return assertNever(s);
  }
}

function describePipelineState(s: PipelineState): string {
  switch (s) {
    case 'spec':
      return '1';
    case 'spec → plan':
      return '2';
    case 'spec → plan → tasks':
      return '3';
    case 'implementing':
      return '4';
    case 'complete':
      return '5';
    default:
      return assertNever(s);
  }
}

describe('parser/types — TaskStatus exhaustiveness', () => {
  it('maps "pending"', () => {
    expect(describeTaskStatus('pending')).to.equal('p');
  });
  it('maps "in_progress"', () => {
    expect(describeTaskStatus('in_progress')).to.equal('i');
  });
  it('maps "blocked"', () => {
    expect(describeTaskStatus('blocked')).to.equal('b');
  });
  it('maps "done"', () => {
    expect(describeTaskStatus('done')).to.equal('d');
  });
  it('maps "unknown"', () => {
    expect(describeTaskStatus('unknown')).to.equal('u');
  });
});

describe('parser/types — SpecStatus exhaustiveness', () => {
  it('maps "draft"', () => {
    expect(describeSpecStatus('draft')).to.equal('D');
  });
  it('maps "in review"', () => {
    expect(describeSpecStatus('in review')).to.equal('R');
  });
  it('maps "approved"', () => {
    expect(describeSpecStatus('approved')).to.equal('A');
  });
  it('maps "implemented"', () => {
    expect(describeSpecStatus('implemented')).to.equal('I');
  });
  it('maps "pr open"', () => {
    expect(describeSpecStatus('pr open')).to.equal('P');
  });
  it('maps "unknown"', () => {
    expect(describeSpecStatus('unknown')).to.equal('U');
  });
});

describe('parser/types — PipelineState exhaustiveness', () => {
  it('maps "spec"', () => {
    expect(describePipelineState('spec')).to.equal('1');
  });
  it('maps "spec → plan"', () => {
    expect(describePipelineState('spec → plan')).to.equal('2');
  });
  it('maps "spec → plan → tasks"', () => {
    expect(describePipelineState('spec → plan → tasks')).to.equal('3');
  });
  it('maps "implementing"', () => {
    expect(describePipelineState('implementing')).to.equal('4');
  });
  it('maps "complete"', () => {
    expect(describePipelineState('complete')).to.equal('5');
  });
});

describe('parser/types — assertNever', () => {
  it('throws when called at runtime', () => {
    // Cast through unknown to bypass `never` at runtime, exercising the throw.
    expect(() => assertNever('surprise' as unknown as never)).to.throw(
      /Unexpected value/,
    );
  });
});
