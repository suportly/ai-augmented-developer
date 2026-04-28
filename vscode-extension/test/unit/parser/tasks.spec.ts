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
});
