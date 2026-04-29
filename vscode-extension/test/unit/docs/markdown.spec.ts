import { expect } from 'chai';
import * as fs from 'node:fs';
import * as path from 'node:path';

const extensionRoot = path.resolve(__dirname, '../../..');
const repoRoot = path.resolve(extensionRoot, '..');

function firstNonBlankLine(content: string): string {
  for (const raw of content.split(/\r?\n/)) {
    const line = raw.trim();
    if (line.length > 0) {
      return line;
    }
  }
  return '';
}

describe('docs/markdown', () => {
  it('extension README exists and starts with a Markdown heading', () => {
    const readmePath = path.join(extensionRoot, 'README.md');
    expect(fs.existsSync(readmePath), `missing ${readmePath}`).to.equal(true);
    const content = fs.readFileSync(readmePath, 'utf8');
    expect(firstNonBlankLine(content)).to.match(/^#\s+/);
  });

  it('extension CHANGELOG exists, starts with a heading, and seeds 0.0.1', () => {
    const changelogPath = path.join(extensionRoot, 'CHANGELOG.md');
    expect(fs.existsSync(changelogPath), `missing ${changelogPath}`).to.equal(true);
    const content = fs.readFileSync(changelogPath, 'utf8');
    expect(firstNonBlankLine(content)).to.match(/^#\s+/);
    expect(content).to.match(/##\s*\[0\.0\.1\]\s*-\s*2026-04-28/);
  });

  it('root README links to the VS Code extension docs', () => {
    const rootReadmePath = path.join(repoRoot, 'README.md');
    expect(fs.existsSync(rootReadmePath), `missing ${rootReadmePath}`).to.equal(true);
    const content = fs.readFileSync(rootReadmePath, 'utf8');
    const hasLink =
      content.includes('vscode-extension/README.md') ||
      content.includes('./vscode-extension/') ||
      content.includes('(vscode-extension/)');
    expect(hasLink, 'root README must link to vscode-extension/README.md or ./vscode-extension/').to.equal(true);
  });
});
