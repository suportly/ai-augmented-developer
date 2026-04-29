import { expect } from 'chai';
import { readFileSync } from 'fs';
import { join } from 'path';

import { extractClarifications } from '../../../src/parser/clarifications';

const FIXTURES = join(__dirname, '..', '..', 'fixtures', 'specs');

function readFixture(name: string): string {
  return readFileSync(join(FIXTURES, name, 'spec.md'), 'utf8');
}

describe('extractClarifications', () => {
  it('returns 4 entries from the with-clarifications fixture', () => {
    const result = extractClarifications(readFixture('with-clarifications'));
    expect(result).to.have.lengthOf(4);
  });

  it('returns entries in source order with the expected ids', () => {
    const result = extractClarifications(readFixture('with-clarifications'));
    expect(result.map((c) => c.id)).to.deep.equal([
      'cl-1',
      'cl-3',
      'cl-1',
      'cl-2',
    ]);
  });

  it('trims each question and contains the text between the id and closing bracket', () => {
    const result = extractClarifications(readFixture('with-clarifications'));
    expect(result[0].question).to.equal('which thing exactly?');
    expect(result[1].question).to.equal('should we also record IP address?');
    expect(result[2].question).to.equal('is the retry count configurable?');
    expect(result[3].question).to.equal('what about backoff?');
  });

  it('reports 1-based line numbers matching the fixture', () => {
    const source = readFixture('with-clarifications');
    const result = extractClarifications(source);
    const lines = source.split(/\r?\n/);

    // Sanity: the lines we expect.
    const cl1FirstLine = lines.findIndex((l) =>
      l.includes('[NEEDS CLARIFICATION:cl-1 which thing exactly?]'),
    ) + 1;
    const cl3Line = lines.findIndex((l) =>
      l.includes('cl-3 should we also record IP address?'),
    ) + 1;
    const sameLine = lines.findIndex((l) =>
      l.includes('Edge case row'),
    ) + 1;

    expect(result[0].line).to.equal(cl1FirstLine);
    expect(result[1].line).to.equal(cl3Line);
    expect(result[2].line).to.equal(sameLine);
    expect(result[3].line).to.equal(sameLine);
  });

  it('returns an empty array for empty source', () => {
    expect(extractClarifications('')).to.deep.equal([]);
  });

  it('returns an empty array for source with no markers', () => {
    const source = [
      '# Just a doc',
      '',
      'Some prose without any clarification markers.',
      '',
      'Another paragraph.',
    ].join('\n');
    expect(extractClarifications(source)).to.deep.equal([]);
  });

  it('ignores legacy markers without a cl-N id', () => {
    const source = 'Prose [NEEDS CLARIFICATION: bare question with no id] more.';
    expect(extractClarifications(source)).to.deep.equal([]);
  });

  it('strips a leading BOM and tolerates CRLF line endings', () => {
    const source =
      '﻿# Title\r\n\r\nLine with [NEEDS CLARIFICATION:cl-1 q?] here.\r\n';
    const result = extractClarifications(source);
    expect(result).to.have.lengthOf(1);
    expect(result[0].id).to.equal('cl-1');
    expect(result[0].question).to.equal('q?');
    expect(result[0].line).to.equal(3);
  });

  it('records the opening line when a marker spans multiple lines', () => {
    const source = [
      'first line',
      'second [NEEDS CLARIFICATION:cl-2 multi',
      'line question?] tail',
    ].join('\n');
    const result = extractClarifications(source);
    expect(result).to.have.lengthOf(1);
    expect(result[0].id).to.equal('cl-2');
    expect(result[0].line).to.equal(2);
  });
});
