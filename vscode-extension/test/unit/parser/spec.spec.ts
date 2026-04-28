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

  it('strips a UTF-8 BOM at the start of the source before parsing', () => {
    const source =
      '﻿' +
      [
        '# Feature specification: BOM prefixed',
        '',
        '**Branch:** `feature/bom`',
        '**Status:** Draft',
        '**Spec ID:** 0001',
        '**Language:** en',
        '',
        '---',
      ].join('\n');

    const result = parseSpec(source);

    expect(result.title).to.equal('BOM prefixed');
    expect(result.title ?? '').to.not.match(/﻿/);
    expect(result.branch).to.equal('feature/bom');
    expect(result.status).to.equal('draft');
    expect(result.specId).to.equal('0001');
    expect(result.language).to.equal('en');
    expect(result.parseError).to.equal(undefined);
  });

  it('parses CRLF line endings identically to LF', () => {
    const lines = [
      '# Feature specification: CRLF source',
      '',
      '**Branch:** `feature/crlf`',
      '**Status:** Approved',
      '**Spec ID:** 0002',
      '**Language:** en',
      '',
      '---',
    ];
    const lf = parseSpec(lines.join('\n'));
    const crlf = parseSpec(lines.join('\r\n'));

    expect(crlf).to.deep.equal(lf);
    expect(crlf.title).to.equal('CRLF source');
    expect(crlf.status).to.equal('approved');
  });

  const caseVariants: Array<{ label: string; key: string }> = [
    { label: 'lowercase', key: '**status:**' },
    { label: 'titlecase', key: '**Status:**' },
    { label: 'uppercase', key: '**STATUS:**' },
    { label: 'mixedcase', key: '**StAtUs:**' },
  ];

  for (const variant of caseVariants) {
    it(`treats ${variant.label} bold key (${variant.key}) as Status`, () => {
      const source = [
        '# Feature specification: Case variant',
        '',
        `${variant.key} approved`,
        '**Spec ID:** 0003',
        '',
        '---',
      ].join('\n');

      const result = parseSpec(source);

      expect(result.status).to.equal('approved');
      expect(result.parseError).to.equal(undefined);
    });
  }

  it('parses the bom-crlf fixture end-to-end (BOM + CRLF on disk)', () => {
    const result = parseSpec(readFixture('bom-crlf'));

    expect(result.title).to.equal('BOM CRLF fixture');
    expect(result.title ?? '').to.not.match(/﻿/);
    expect(result.branch).to.equal('feature/bom-crlf');
    expect(result.language).to.equal('en');
    expect(result.specId).to.equal('0100');
    expect(result.status).to.equal('approved');
    expect(result.parseError).to.equal(undefined);
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
