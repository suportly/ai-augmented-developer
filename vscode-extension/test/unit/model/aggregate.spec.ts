import { expect } from 'chai';

import { buildSpecModels } from '../../../src/model/aggregate';
import { FakeFileSystem } from '../../support/fakeFileSystem';

const VALID_SPEC = [
  '# Feature specification: Example feature',
  '',
  '**Branch:** `feature/example`',
  '**Status:** Draft',
  '**Spec ID:** 0001',
  '**Language:** en',
  '',
  '---',
  '',
  'Body.',
  '',
].join('\n');

function specWithHeader(opts: {
  title: string;
  branch?: string;
  specId?: string;
  status?: string;
  language?: string;
  body?: string;
}): string {
  const lines = [
    '# Feature specification: ' + opts.title,
    '',
  ];
  if (opts.branch !== undefined) lines.push('**Branch:** `' + opts.branch + '`');
  if (opts.status !== undefined) lines.push('**Status:** ' + opts.status);
  if (opts.specId !== undefined) lines.push('**Spec ID:** ' + opts.specId);
  if (opts.language !== undefined) lines.push('**Language:** ' + opts.language);
  lines.push('', '---', '', opts.body ?? 'Body.');
  return lines.join('\n');
}

describe('buildSpecModels', () => {
  it('aggregates specs from multiple workspace folders with workspaceFolderName set per row', async () => {
    const fs = new FakeFileSystem({
      '/repo/framework/specs/0001-alpha/spec.md': specWithHeader({
        title: 'Alpha',
        branch: 'feature/alpha',
        specId: '0001',
        status: 'Draft',
        language: 'en',
      }),
      '/repo/consumer/specs/0002-beta/spec.md': specWithHeader({
        title: 'Beta',
        branch: 'feature/beta',
        specId: '0002',
        status: 'Approved',
        language: 'en',
      }),
    });

    const models = await buildSpecModels(
      fs,
      [
        { name: 'framework', fsPath: '/repo/framework' },
        { name: 'consumer', fsPath: '/repo/consumer' },
      ],
      'specs',
    );

    expect(models).to.have.lengthOf(2);
    const byId = new Map(models.map((m) => [m.specId, m]));
    expect(byId.get('0001')!.workspaceFolderName).to.equal('framework');
    expect(byId.get('0001')!.workspaceFolderUri).to.equal('/repo/framework');
    expect(byId.get('0002')!.workspaceFolderName).to.equal('consumer');
    expect(byId.get('0002')!.workspaceFolderUri).to.equal('/repo/consumer');
  });

  it('sorts results by specId ascending', async () => {
    const fs = new FakeFileSystem({
      '/ws/specs/0050-fifty/spec.md': specWithHeader({ title: 'Fifty', specId: '0050', status: 'Draft' }),
      '/ws/specs/0002-two/spec.md': specWithHeader({ title: 'Two', specId: '0002', status: 'Draft' }),
      '/ws/specs/0010-ten/spec.md': specWithHeader({ title: 'Ten', specId: '0010', status: 'Draft' }),
    });

    const models = await buildSpecModels(
      fs,
      [{ name: 'ws', fsPath: '/ws' }],
      'specs',
    );

    expect(models.map((m) => m.specId)).to.deep.equal(['0002', '0010', '0050']);
  });

  it('honours a non-default specsRoot setting', async () => {
    const fs = new FakeFileSystem({
      '/ws/docs/specs/0001-alpha/spec.md': specWithHeader({ title: 'Alpha', specId: '0001', status: 'Draft' }),
      // a spec under the default 'specs' root must NOT be picked up
      '/ws/specs/0099-ignore/spec.md': specWithHeader({ title: 'Ignore', specId: '0099', status: 'Draft' }),
    });

    const models = await buildSpecModels(
      fs,
      [{ name: 'ws', fsPath: '/ws' }],
      'docs/specs',
    );

    expect(models).to.have.lengthOf(1);
    expect(models[0].specId).to.equal('0001');
    expect(models[0].specPath).to.equal('/ws/docs/specs/0001-alpha/spec.md');
  });

  it('reports pipelineState "spec" when only spec.md exists', async () => {
    const fs = new FakeFileSystem({
      '/ws/specs/0001-alpha/spec.md': specWithHeader({ title: 'Alpha', specId: '0001', status: 'Draft' }),
    });

    const models = await buildSpecModels(
      fs,
      [{ name: 'ws', fsPath: '/ws' }],
      'specs',
    );

    expect(models).to.have.lengthOf(1);
    const m = models[0];
    expect(m.pipelineState).to.equal('spec');
    expect(m.hasSpec).to.equal(true);
    expect(m.hasPlan).to.equal(false);
    expect(m.hasTasks).to.equal(false);
    expect(m.tasks).to.deep.equal([]);
    expect(m.tasksPath).to.equal(undefined);
  });

  it('reports pipelineState "complete" when spec/plan/tasks present and every task is done', async () => {
    const tasks = [
      '### T001 — First',
      '',
      '- **Status:** done',
      '',
      '### T002 — Second',
      '',
      '- **Status:** done',
      '',
    ].join('\n');

    const fs = new FakeFileSystem({
      '/ws/specs/0001-alpha/spec.md': specWithHeader({ title: 'Alpha', specId: '0001', status: 'Implemented' }),
      '/ws/specs/0001-alpha/plan.md': '# plan',
      '/ws/specs/0001-alpha/tasks.md': tasks,
    });

    const models = await buildSpecModels(
      fs,
      [{ name: 'ws', fsPath: '/ws' }],
      'specs',
    );

    expect(models).to.have.lengthOf(1);
    const m = models[0];
    expect(m.hasSpec).to.equal(true);
    expect(m.hasPlan).to.equal(true);
    expect(m.hasTasks).to.equal(true);
    expect(m.tasks.map((t) => t.id)).to.deep.equal(['T001', 'T002']);
    expect(m.pipelineState).to.equal('complete');
    expect(m.tasksPath).to.equal('/ws/specs/0001-alpha/tasks.md');
  });

  it('propagates parseError and surfaces status "unknown" when Status header is missing', async () => {
    const noStatus = [
      '# Feature specification: Broken',
      '',
      '**Branch:** `feature/broken`',
      '**Spec ID:** 0001',
      '',
      '---',
      '',
    ].join('\n');

    const fs = new FakeFileSystem({
      '/ws/specs/0001-broken/spec.md': noStatus,
    });

    const models = await buildSpecModels(
      fs,
      [{ name: 'ws', fsPath: '/ws' }],
      'specs',
    );

    expect(models).to.have.lengthOf(1);
    const m = models[0];
    expect(m.status).to.equal('unknown');
    expect(m.parseError).to.be.a('string').and.match(/Status/);
  });

  it('surfaces clarifications extracted from spec.md', async () => {
    const body = [
      'Some intro.',
      '',
      '[NEEDS CLARIFICATION:cl-1 What is the retention policy?]',
      '',
      'More text. [NEEDS CLARIFICATION:cl-2 How is auth scoped?]',
    ].join('\n');

    const fs = new FakeFileSystem({
      '/ws/specs/0001-alpha/spec.md': specWithHeader({
        title: 'Alpha',
        specId: '0001',
        status: 'Draft',
        body,
      }),
    });

    const models = await buildSpecModels(
      fs,
      [{ name: 'ws', fsPath: '/ws' }],
      'specs',
    );

    expect(models).to.have.lengthOf(1);
    const ids = models[0].clarifications.map((c) => c.id);
    expect(ids).to.deep.equal(['cl-1', 'cl-2']);
  });

  it('rejects an absolute specsRoot with a TypeError', async () => {
    const fs = new FakeFileSystem({});
    let posixErr: unknown;
    try {
      await buildSpecModels(fs, [{ name: 'ws', fsPath: '/ws' }], '/abs/specs');
    } catch (e) {
      posixErr = e;
    }
    expect(posixErr).to.be.instanceOf(TypeError);
    expect((posixErr as Error).message).to.match(/absolute/i);

    let winErr: unknown;
    try {
      await buildSpecModels(fs, [{ name: 'ws', fsPath: '/ws' }], 'C:/specs');
    } catch (e) {
      winErr = e;
    }
    expect(winErr).to.be.instanceOf(TypeError);
    expect((winErr as Error).message).to.match(/absolute/i);
  });

  it('rejects a specsRoot containing ".." segments with a TypeError', async () => {
    const fs = new FakeFileSystem({});
    let err: unknown;
    try {
      await buildSpecModels(fs, [{ name: 'ws', fsPath: '/ws' }], '../escape/specs');
    } catch (e) {
      err = e;
    }
    expect(err).to.be.instanceOf(TypeError);
    expect((err as Error).message).to.match(/\.\./);
  });

  it('breaks ties on equal numeric specId by workspaceFolderName ascending', async () => {
    const fs = new FakeFileSystem({
      '/repo/zeta/specs/0007-x/spec.md': specWithHeader({ title: 'Z', specId: '0007', status: 'Draft' }),
      '/repo/alpha/specs/0007-x/spec.md': specWithHeader({ title: 'A', specId: '0007', status: 'Draft' }),
      '/repo/mike/specs/0007-x/spec.md': specWithHeader({ title: 'M', specId: '0007', status: 'Draft' }),
    });

    const models = await buildSpecModels(
      fs,
      [
        { name: 'zeta', fsPath: '/repo/zeta' },
        { name: 'alpha', fsPath: '/repo/alpha' },
        { name: 'mike', fsPath: '/repo/mike' },
      ],
      'specs',
    );

    expect(models.map((m) => m.workspaceFolderName)).to.deep.equal(['alpha', 'mike', 'zeta']);
  });

  it('falls back to specDirName as specId when dir lacks numeric prefix and header lacks Spec ID', async () => {
    const noSpecId = [
      '# Feature specification: Nameless',
      '',
      '**Branch:** `feature/nameless`',
      '**Status:** Draft',
      '**Language:** en',
      '',
      '---',
      '',
      'Body.',
    ].join('\n');

    const fs = new FakeFileSystem({
      '/ws/specs/no-prefix-here/spec.md': noSpecId,
    });

    const models = await buildSpecModels(
      fs,
      [{ name: 'ws', fsPath: '/ws' }],
      'specs',
    );

    expect(models).to.have.lengthOf(1);
    expect(models[0].specId).to.equal('no-prefix-here');
    expect(models[0].specDirName).to.equal('no-prefix-here');
  });

  it('uses dir-name prefix as specId, with sane defaults when valid', async () => {
    const fs = new FakeFileSystem({
      '/ws/specs/0042-meaning/spec.md': VALID_SPEC,
    });

    const models = await buildSpecModels(
      fs,
      [{ name: 'ws', fsPath: '/ws' }],
      'specs',
    );

    expect(models[0].specId).to.equal('0042');
    expect(models[0].specDirName).to.equal('0042-meaning');
    expect(models[0].title).to.equal('Example feature');
    expect(models[0].branch).to.equal('feature/example');
    expect(models[0].language).to.equal('en');
  });
});
