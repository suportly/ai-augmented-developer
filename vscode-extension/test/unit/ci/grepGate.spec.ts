import { expect } from 'chai';
import * as fs from 'fs';
import * as path from 'path';

interface Offence {
  file: string;
  line: number;
  pattern: string;
  text: string;
}

const SRC_ROOT = path.resolve(__dirname, '../../../src');

const FORBIDDEN: Array<{ name: string; regex: RegExp }> = [
  { name: 'console.log', regex: /\bconsole\.log\b/ },
  { name: 'console.error', regex: /\bconsole\.error\b/ },
  { name: 'fetch(', regex: /\bfetch\s*\(/ },
  { name: 'http.request / https.request', regex: /\bhttps?\.request\b/ },
  { name: 'http.get / https.get', regex: /\bhttps?\.get\b/ },
  { name: 'child_process', regex: /\bchild_process\b/ },
];

function walk(dir: string): string[] {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walk(full));
    } else if (entry.isFile() && full.endsWith('.ts')) {
      files.push(full);
    }
  }
  return files;
}

describe('ci/grep-gate', () => {
  it('production source files contain no forbidden runtime patterns', () => {
    const files = walk(SRC_ROOT);
    expect(files.length, 'expected to find at least one source file').to.be.greaterThan(0);

    const offences: Offence[] = [];
    for (const file of files) {
      const lines = fs.readFileSync(file, 'utf8').split(/\r?\n/);
      lines.forEach((text, idx) => {
        for (const { name, regex } of FORBIDDEN) {
          if (regex.test(text)) {
            offences.push({
              file: path.relative(SRC_ROOT, file),
              line: idx + 1,
              pattern: name,
              text: text.trim(),
            });
          }
        }
      });
    }

    const message = offences
      .map((o) => `  ${o.file}:${o.line} [${o.pattern}] ${o.text}`)
      .join('\n');
    expect(offences, `forbidden patterns found in src/:\n${message}`).to.deep.equal([]);
  });
});
