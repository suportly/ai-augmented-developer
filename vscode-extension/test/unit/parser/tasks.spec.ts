import { expect } from 'chai';
import { readFileSync } from 'fs';
import { join } from 'path';

import { parseTasks } from '../../../src/parser/tasks';

const FIXTURES = join(__dirname, '..', '..', 'fixtures', 'specs');

function readFixture(name: string): string {
  return readFileSync(join(FIXTURES, name, 'tasks.md'), 'utf8');
}

describe('parseTasks', () => {
  it('returns 4 tasks T001-T004 from the canonical fixture in source order with one of each status', () => {
    const result = parseTasks(readFixture('canonical'));

    expect(result).to.have.lengthOf(4);
    expect(result.map((t) => t.id)).to.deep.equal(['T001', 'T002', 'T003', 'T004']);
    expect(result.map((t) => t.status)).to.deep.equal([
      'done',
      'in_progress',
      'blocked',
      'pending',
    ]);
    expect(result[0].title).to.equal('Scaffold parser module');
    expect(result[1].title).to.equal('Add status bullet recognition');
    expect(result[2].title).to.equal('Wire parser into provider');
    expect(result[3].title).to.equal('Document parser API');
  });

  it('reports the correct 1-based heading line number for each task', () => {
    const source = [
      '# Tasks: line numbers', // 1
      '', // 2
      '**Branch:** `feature/x`', // 3
      '', // 4
      '## Task list', // 5
      '', // 6
      '### T001 — First', // 7
      '', // 8
      '- **Status:** pending', // 9
      '', // 10
      '### T002 — Second', // 11
      '', // 12
      '- **Status:** done', // 13
    ].join('\n');

    const result = parseTasks(source);

    expect(result).to.have.lengthOf(2);
    expect(result[0].line).to.equal(7);
    expect(result[1].line).to.equal(11);
  });

  it('returns an empty array for empty source', () => {
    expect(parseTasks('')).to.deep.equal([]);
  });

  it('marks a task with no Status bullet before the next heading as status: unknown', () => {
    const source = [
      '### T001 — Lonely heading',
      '',
      'Some prose but no status bullet here.',
      '',
      '### T002 — Next task',
      '',
      '- **Status:** pending',
    ].join('\n');

    const result = parseTasks(source);

    expect(result).to.have.lengthOf(2);
    expect(result[0].id).to.equal('T001');
    expect(result[0].status).to.equal('unknown');
    expect(result[1].id).to.equal('T002');
    expect(result[1].status).to.equal('pending');
  });

  it('tolerates an ASCII hyphen in the heading: parses identically to em-dash form', () => {
    const emDash = [
      '### T001 — Em dash title',
      '',
      '- **Status:** pending',
    ].join('\n');
    const hyphen = [
      '### T001 - Em dash title',
      '',
      '- **Status:** pending',
    ].join('\n');

    expect(parseTasks(hyphen)).to.deep.equal(parseTasks(emDash));
    const [task] = parseTasks(hyphen);
    expect(task.id).to.equal('T001');
    expect(task.title).to.equal('Em dash title');
    expect(task.status).to.equal('pending');
  });

  it('parses BOM + CRLF input identically to LF input', () => {
    const lines = [
      '# Tasks: bom crlf',
      '',
      '### T001 — Heading',
      '',
      '- **Status:** done',
      '',
      '### T002 — Second',
      '',
      '- **Status:** blocked',
    ];

    const lf = parseTasks(lines.join('\n'));
    const bomCrlf = parseTasks('﻿' + lines.join('\r\n'));

    expect(bomCrlf).to.deep.equal(lf);
    expect(bomCrlf[0].title).to.equal('Heading');
    expect(bomCrlf[0].status).to.equal('done');
    expect(bomCrlf[1].status).to.equal('blocked');
  });

  it('maps unrecognised status values to "unknown"', () => {
    const source = [
      '### T001 — Bogus status',
      '',
      '- **Status:** wat',
    ].join('\n');

    const [task] = parseTasks(source);
    expect(task.status).to.equal('unknown');
  });

  // T009 regression guard: a malformed `**Status:** Bogus` line in one
  // task must not throw and must not contaminate the statuses of the
  // surrounding well-formed tasks. T008 already mapped any unrecognised
  // value to `unknown`, so this fixture-backed test pins the contract
  // for future refactors of the parser.
  it('parses heading without separator: "### T001 Title" with status unknown', () => {
    const source = [
      '### T001 Criar branch BKO-126',
      '### T002 [P] Outra task',
    ].join('\n');

    const result = parseTasks(source);

    expect(result).to.have.lengthOf(2);
    expect(result[0]).to.deep.include({ id: 'T001', title: 'Criar branch BKO-126', status: 'unknown' });
    expect(result[1]).to.deep.include({ id: 'T002', title: 'Outra task', status: 'unknown' });
  });

  it('parses tasks declared as H4-H6 headings, including under an H3 phase group', () => {
    const source = [
      '## Task list',
      '',
      '### Phase 1 — Modelo',
      '',
      '#### T001 — Schema',
      '',
      '- **Status:** pending',
      '',
      '#### T002 — Indexes',
      '',
      '- **Status:** done',
      '',
      '### Phase 2 — API',
      '',
      '##### T003 — Endpoint',
      '',
      '- **Status:** in_progress',
    ].join('\n');

    const result = parseTasks(source);

    expect(result.map((t) => t.id)).to.deep.equal(['T001', 'T002', 'T003']);
    expect(result.map((t) => t.status)).to.deep.equal(['pending', 'done', 'in_progress']);
    expect(result[0].title).to.equal('Schema');
    expect(result[2].title).to.equal('Endpoint');
  });

  it('parses GitHub task-list checkbox: [x] -> done, [ ] -> pending', () => {
    const source = [
      '- [x] T001 Done task',
      '- [ ] T002 [P] Pending task',
      '- [x] **T003** Bold id',
      '- [x] ~~**T004**~~ Strikethrough id',
    ].join('\n');

    const result = parseTasks(source);

    expect(result).to.have.lengthOf(4);
    expect(result.map((t) => t.status)).to.deep.equal(['done', 'pending', 'done', 'done']);
    expect(result[1].title).to.equal('Pending task');
    expect(result[2].title).to.equal('Bold id');
  });

  it('updates a heading-declared task with a table-row status (emoji + word)', () => {
    const source = [
      '### T001 First',
      '### T002 Second',
      '',
      '| Task | Commit | Status |',
      '|---|---|---|',
      '| T001 | abc123 | ✅ |',
      '| T002 | def456 | done |',
    ].join('\n');

    const result = parseTasks(source);

    expect(result).to.have.lengthOf(2);
    expect(result[0].status).to.equal('done');
    expect(result[1].status).to.equal('done');
  });

  it('tolerates markdown wrapping (**done**, ~~done~~) inside a status table cell', () => {
    const source = [
      '### T001 First',
      '### T002 Second',
      '### T003 Third',
      '',
      '| Task | Commit | Status |',
      '|---|---|---|',
      '| T001 | abc | **done** |',
      '| T002 | def | ~~pending~~ |',
      '| T003 | ghi | `in_progress` |',
    ].join('\n');

    const result = parseTasks(source);

    expect(result.map((t) => t.status)).to.deep.equal(['done', 'pending', 'in_progress']);
  });

  it('does not duplicate a task already declared by a heading when its id appears in a checkbox later', () => {
    const source = [
      '### T001 From heading',
      '- [x] T001 From checkbox (should be ignored as duplicate)',
    ].join('\n');

    const result = parseTasks(source);

    expect(result).to.have.lengthOf(1);
    expect(result[0].title).to.equal('From heading');
  });

  it('isolates an unknown status to the offending task without throwing (malformed-task-status fixture)', () => {
    const source = readFixture('malformed-task-status');

    const result = (() => {
      try {
        return parseTasks(source);
      } catch (err) {
        expect.fail(`parseTasks threw on malformed Status: ${(err as Error).message}`);
      }
    })();

    expect(result).to.have.lengthOf(3);
    expect(result!.map((t) => t.id)).to.deep.equal(['T001', 'T002', 'T003']);
    expect(result![0].status).to.equal('done');
    expect(result![1].status).to.equal('unknown');
    expect(result![2].status).to.equal('pending');
  });
});
