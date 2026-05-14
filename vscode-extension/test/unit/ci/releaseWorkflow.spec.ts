import { expect } from 'chai';
import * as fs from 'fs';
import * as path from 'path';

const WORKFLOW_PATH = path.resolve(
  __dirname,
  '../../../../.github/workflows/vscode-extension.yml',
);

describe('ci/release-workflow', () => {
  let content: string;

  before(() => {
    content = fs.readFileSync(WORKFLOW_PATH, 'utf8');
  });

  it('triggers on tags matching vscode-extension-v*', () => {
    expect(content).to.match(/tags:\s*\n\s*-\s*['"]?vscode-extension-v\*['"]?/);
  });

  it('declares a release job', () => {
    expect(content).to.match(/^\s{2}release:/m);
  });

  it('release job declares needs: build to chain after the build job', () => {
    // Guards against decoupling the jobs — release must consume the VSIX
    // produced by build, so the structural dependency is required.
    const releaseSection = content.split(/^\s{2}release:/m)[1] ?? '';
    const firstTenLines = releaseSection.split('\n').slice(0, 10).join('\n');
    expect(firstTenLines).to.match(/needs:\s*build/);
  });

  it('gates the release job on a tag ref', () => {
    expect(content).to.include("startsWith(github.ref, 'refs/tags/vscode-extension-v')");
  });

  it('also gates the release job on a main push (auto-release path)', () => {
    expect(content).to.include("github.ref == 'refs/heads/main'");
  });

  it('resolves release context from package.json on the main-push path', () => {
    expect(content).to.match(/jq\s+-r\s+\.version\s+vscode-extension\/package\.json/);
  });

  it('creates and pushes the tag inline when releasing from main', () => {
    expect(content).to.match(/git tag -a "\$TAG"/);
    expect(content).to.match(/git push origin "\$TAG"/);
  });

  it('skips the tag-creation step on the tag-push path (create_tag == false)', () => {
    expect(content).to.match(/steps\.ctx\.outputs\.create_tag\s*==\s*'true'/);
  });

  it('grants contents: write to the release job', () => {
    const releaseSection = content.split(/^\s{2}release:/m)[1] ?? '';
    expect(releaseSection).to.match(/permissions:\s*\n\s*contents:\s*write/);
  });

  it('publishes to the Marketplace via vsce publish', () => {
    expect(content).to.match(/vsce\s+publish/);
  });

  it('attaches the VSIX to the GitHub release', () => {
    expect(content).to.include('softprops/action-gh-release');
  });

  it('skips Marketplace publish when VSCE_PAT is not set', () => {
    // Tolerant of additional conjuncts on the same `if:` line (e.g. the
    // should_release gate added when release-on-main was introduced).
    // The contract is: the publish step's `if:` expression includes a
    // `env.VSCE_PAT != ''` clause.
    expect(content).to.match(/if:[^\n]*env\.VSCE_PAT\s*!=\s*''/);
  });
});
