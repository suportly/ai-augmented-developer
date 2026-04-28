import { expect } from 'chai';
import { readFileSync } from 'fs';
import { join } from 'path';

import { parseSpec } from '../../../src/parser/spec';

const FIXTURES = join(__dirname, '..', '..', 'fixtures', 'specs');

function readFixture(name: string): string {
  return readFileSync(join(FIXTURES, name, 'spec.md'), 'utf8');
}

describe('parseSpec', () => {
  it('extracts title, branch, language, specId, and status from the canonical fixture', () => {
    const result = parseSpec(readFixture('canonical'));

    expect(result.title).to.equal('Canonical fixture');
    expect(result.branch).to.equal('feature/canonical');
    expect(result.language).to.equal('en');
    expect(result.specId).to.equal('0099');
    expect(result.status).to.equal('approved');
    expect(result.parseError).to.equal(undefined);
  });

  it('strips surrounding backticks from bold-key values', () => {
    const source = [
      '# Feature specification: Backtick test',
      '',
      '**Branch:** `feature/backticked`',
      '**Status:** Draft',
      '**Language:** `en`',
      '**Spec ID:** `0042`',
      '',
      '---',
    ].join('\n');

    const result = parseSpec(source);

    expect(result.branch).to.equal('feature/backticked');
    expect(result.language).to.equal('en');
    expect(result.specId).to.equal('0042');
    expect(result.status).to.equal('draft');
  });

  it('returns status: unknown plus a parseError when the Status value is not in the canonical set', () => {
    const source = [
      '# Feature specification: Bogus status',
      '',
      '**Status:** Bogus',
      '**Spec ID:** 0001',
      '',
      '---',
    ].join('\n');

    const result = parseSpec(source);

    expect(result.status).to.equal('unknown');
    expect(result.parseError).to.be.a('string');
    expect(result.parseError).to.match(/Bogus/);
  });

  it('returns status: unknown with a Missing **Status:** header parseError when no Status line is present', () => {
    const result = parseSpec(readFixture('missing-status'));

    expect(result.status).to.equal('unknown');
    expect(result.parseError).to.equal('Missing **Status:** header');
  });

  it('distinguishes a missing Status header from an unrecognised Status value', () => {
    const missing = parseSpec(readFixture('missing-status'));
    const bogus = parseSpec(
      [
        '# Feature specification: Bogus status',
        '',
        '**Status:** Bogus',
        '',
        '---',
      ].join('\n'),
    );

    expect(missing.parseError).to.not.equal(bogus.parseError);
    expect(missing.parseError).to.match(/Missing/);
    expect(bogus.parseError).to.match(/Unrecognised/);
  });

  it('normalises multi-word status values to lowercase canonical form', () => {
    const inReview = parseSpec(
      [
        '# Feature specification: Multi-word in review',
        '',
        '**Status:** In review',
        '',
        '---',
      ].join('\n'),
    );
    expect(inReview.status).to.equal('in review');
    expect(inReview.parseError).to.equal(undefined);

    const prOpen = parseSpec(
      [
        '# Feature specification: Multi-word PR open',
        '',
        '**Status:** PR Open',
        '',
        '---',
      ].join('\n'),
    );
    expect(prOpen.status).to.equal('pr open');
    expect(prOpen.parseError).to.equal(undefined);
  });
});
