import { expect } from 'chai';

import {
  SpecTreeProvider,
  type EmptyStateNode,
  type Node,
  type SpecNode,
  type TreeItemCtors,
} from '../../../src/views/specTreeProvider';
import type { SpecModel } from '../../../src/parser/types';
import {
  StubEventEmitter,
  StubTreeItem,
  StubTreeItemCollapsibleState,
} from '../../support/vscodeStub';

/**
 * Stub-based unit tests for the SpecTreeProvider parent rows.
 *
 * Plan deviation: plan.md Phase 4 originally called for `@vscode/test-electron`
 * integration tests; we pivot to stubs (same factory pattern as T014 / icons)
 * to keep view-layer tests in the fast Node-only `npm run test:unit` lane. A
 * follow-up task will add real Extension Host integration tests.
 *
 * T015 narrow scope: SpecNode rendering only. TaskNode children (T017),
 * EmptyStateNode (T016), ClarificationGroupNode (T020), pipeline-state badge
 * refinement (T022), folder prefix (T023), branch highlight (T024) are all
 * deferred.
 */

function buildModel(overrides: Partial<SpecModel> = {}): SpecModel {
  const base: SpecModel = {
    workspaceFolderName: 'root',
    workspaceFolderUri: '/work/root',
    specDirName: '0012-vscode-spec-explorer',
    specId: '0012',
    title: 'VS Code spec explorer extension',
    branch: 'feature/vscode-spec-explorer',
    language: 'en',
    status: 'approved',
    hasSpec: true,
    hasPlan: true,
    hasTasks: true,
    tasks: [],
    clarifications: [],
    pipelineState: 'implementing',
    specPath: '/work/root/specs/0012-vscode-spec-explorer/spec.md',
    tasksPath: '/work/root/specs/0012-vscode-spec-explorer/tasks.md',
  };
  return { ...base, ...overrides };
}

let lastEmitter: StubEventEmitter<unknown> | undefined;

function makeProvider(specs: readonly SpecModel[]): SpecTreeProvider {
  lastEmitter = undefined;
  const ctors: TreeItemCtors = {
    TreeItem: StubTreeItem as unknown as TreeItemCtors['TreeItem'],
    TreeItemCollapsibleState: StubTreeItemCollapsibleState,
    EventEmitter: class<T> extends StubEventEmitter<T> {
      constructor() {
        super();
        lastEmitter = this as unknown as StubEventEmitter<unknown>;
      }
    } as unknown as TreeItemCtors['EventEmitter'],
  };
  return new SpecTreeProvider(ctors, specs);
}

describe('SpecTreeProvider — SpecNode rendering (T015)', () => {
  it('returns one SpecNode per spec from getChildren() with no element', () => {
    const a = buildModel({ specId: '0001', title: 'Alpha' });
    const b = buildModel({ specId: '0002', title: 'Beta' });
    const provider = makeProvider([a, b]);

    const children = provider.getChildren() as SpecNode[];

    expect(children).to.have.lengthOf(2);
    expect(children[0].kind).to.equal('spec');
    expect(children[0].model).to.equal(a);
    expect(children[1].model).to.equal(b);
  });

  it('renders label as "<specId> — <title>"', () => {
    const model = buildModel({
      specId: '0012',
      title: 'VS Code spec explorer extension',
    });
    const provider = makeProvider([model]);
    const [node] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(node);

    expect(item.label).to.equal('0012 — VS Code spec explorer extension');
    expect((item as unknown as StubTreeItem).collapsibleState).to.equal(
      StubTreeItemCollapsibleState.Collapsed,
    );
    expect(item.contextValue).to.equal('aiadev.spec');
  });

  it('falls back to specDirName when title is empty', () => {
    const model = buildModel({ specDirName: '0099-mystery', title: '' });
    const provider = makeProvider([model]);
    const [node] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(node);

    expect(item.label).to.equal('0099-mystery');
  });

  it('uppercases first letter of status; maps "pr open" → "PR Open" and "unknown" → "Unknown"', () => {
    const cases: Array<[SpecModel['status'], string]> = [
      ['draft', 'Draft'],
      ['in review', 'In review'],
      ['approved', 'Approved'],
      ['implemented', 'Implemented'],
      ['pr open', 'PR Open'],
      ['unknown', 'Unknown'],
    ];

    for (const [status, expected] of cases) {
      const provider = makeProvider([buildModel({ status })]);
      const [node] = provider.getChildren() as SpecNode[];
      const item = provider.getTreeItem(node);
      expect(item.description, `status=${status}`).to.equal(expected);
    }
  });

  it('tooltip is parseError when set, otherwise "<specDirName> · <specPath>"', () => {
    const happy = buildModel();
    const sad = buildModel({
      status: 'unknown',
      parseError: 'Status header missing',
    });
    const happyProv = makeProvider([happy]);
    const sadProv = makeProvider([sad]);

    const happyItem = happyProv.getTreeItem(
      (happyProv.getChildren() as SpecNode[])[0],
    );
    const sadItem = sadProv.getTreeItem(
      (sadProv.getChildren() as SpecNode[])[0],
    );

    expect(happyItem.tooltip).to.equal(
      `${happy.specDirName} · ${happy.specPath}`,
    );
    expect(sadItem.tooltip).to.equal('Status header missing');
  });

  it('iconPath is undefined for now (T022 will set it)', () => {
    const provider = makeProvider([buildModel()]);
    const [node] = provider.getChildren() as SpecNode[];
    const item = provider.getTreeItem(node);
    expect(item.iconPath).to.be.undefined;
  });

  it('getChildren(specNode) returns [] (TaskNode population deferred to T017)', () => {
    const provider = makeProvider([buildModel()]);
    const [node] = provider.getChildren() as SpecNode[];
    expect(provider.getChildren(node)).to.deep.equal([]);
  });

  it('setSpecs(next) updates children and fires the change event', () => {
    const a = buildModel({ specId: '0001', title: 'Alpha' });
    const b = buildModel({ specId: '0002', title: 'Beta' });
    const provider = makeProvider([a]);
    const captured = lastEmitter!;

    expect(provider.getChildren()).to.have.lengthOf(1);
    expect(captured.fired).to.have.lengthOf(0);

    provider.setSpecs([a, b]);

    expect(provider.getChildren()).to.have.lengthOf(2);
    expect(captured.fired).to.have.lengthOf(1);
    expect(captured.fired[0]).to.be.undefined;
  });

  it('exposes onDidChangeTreeData wired to the constructor-created emitter', () => {
    const provider = makeProvider([buildModel()]);
    const captured = lastEmitter!;
    expect(provider.onDidChangeTreeData).to.equal(captured.event);
  });
});

describe('SpecTreeProvider — EmptyStateNode rendering (T016)', () => {
  it('returns one EmptyStateNode when specs array is empty', () => {
    const provider = makeProvider([]);

    const children = provider.getChildren() as Node[];

    expect(children).to.have.lengthOf(1);
    expect(children[0].kind).to.equal('empty');
  });

  it('renders the empty-state node with the verbatim label', () => {
    const provider = makeProvider([]);
    const [node] = provider.getChildren() as EmptyStateNode[];

    const item = provider.getTreeItem(node);

    expect(item.label).to.equal('No aiadev specs found in this workspace');
    expect(item.description).to.be.undefined;
    expect(item.iconPath).to.be.undefined;
    expect(item.contextValue).to.equal('aiadev.empty');
    expect((item as unknown as StubTreeItem).collapsibleState).to.equal(
      StubTreeItemCollapsibleState.None,
    );
  });

  it('tooltip matches the verbatim hint about /aiadev:specify', () => {
    const provider = makeProvider([]);
    const [node] = provider.getChildren() as EmptyStateNode[];

    const item = provider.getTreeItem(node);

    expect(item.tooltip).to.equal(
      'Create a spec with /aiadev:specify in the integrated terminal.',
    );
  });

  it('switches to a single empty-state node after setSpecs([]) from non-empty', () => {
    const provider = makeProvider([buildModel({ specId: '0001' })]);

    expect(provider.getChildren()).to.have.lengthOf(1);
    expect((provider.getChildren() as Node[])[0].kind).to.equal('spec');

    provider.setSpecs([]);

    const children = provider.getChildren() as Node[];
    expect(children).to.have.lengthOf(1);
    expect(children[0].kind).to.equal('empty');
  });

  it('getChildren(emptyNode) returns []', () => {
    const provider = makeProvider([]);
    const [node] = provider.getChildren() as EmptyStateNode[];

    expect(provider.getChildren(node)).to.deep.equal([]);
  });
});
