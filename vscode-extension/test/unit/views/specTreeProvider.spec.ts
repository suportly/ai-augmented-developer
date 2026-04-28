import { expect } from 'chai';

import {
  SpecTreeProvider,
  type ClarificationGroupNode,
  type ClarificationNode,
  type EmptyStateNode,
  type IconFactories,
  type Node,
  type SpecNode,
  type TaskNode,
  type TreeItemCtors,
} from '../../../src/views/specTreeProvider';
import type {
  Clarification,
  PipelineState,
  SpecModel,
  Task,
  TaskStatus,
} from '../../../src/parser/types';
import {
  StubEventEmitter,
  StubRange,
  StubThemeIcon,
  StubTreeItem,
  StubTreeItemCollapsibleState,
  StubUri,
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
let lastStatusIconCalls: TaskStatus[] = [];

interface IconStub {
  readonly tag: 'icon-stub';
  readonly status: TaskStatus;
}

function makeProvider(
  specs: readonly SpecModel[],
  iconFactoriesOverride?: IconFactories,
  options?: { multiRoot?: boolean },
): SpecTreeProvider {
  lastEmitter = undefined;
  lastStatusIconCalls = [];
  const ctors: TreeItemCtors = {
    TreeItem: StubTreeItem as unknown as TreeItemCtors['TreeItem'],
    TreeItemCollapsibleState: StubTreeItemCollapsibleState,
    EventEmitter: class<T> extends StubEventEmitter<T> {
      constructor() {
        super();
        lastEmitter = this as unknown as StubEventEmitter<unknown>;
      }
    } as unknown as TreeItemCtors['EventEmitter'],
    Uri: StubUri as unknown as TreeItemCtors['Uri'],
    Range: StubRange as unknown as TreeItemCtors['Range'],
    ThemeIcon: StubThemeIcon as unknown as TreeItemCtors['ThemeIcon'],
  };
  const iconFactories: IconFactories = iconFactoriesOverride ?? {
    statusIcon: (status: TaskStatus): IconStub => {
      lastStatusIconCalls.push(status);
      return { tag: 'icon-stub', status };
    },
  };
  return new SpecTreeProvider(ctors, iconFactories, specs, options);
}

function buildTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 'T001',
    title: 'Bootstrap',
    status: 'pending',
    line: 1,
    ...overrides,
  };
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

  it('SpecStatus is surfaced in tooltip (description carries pipelineState badge after T022)', () => {
    // Pipeline-state badge replaces the SpecStatus in the description
    // (T022). The status remains visible via the tooltip's "Status:" line.
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
      expect(item.tooltip, `status=${status}`).to.contain(`Status: ${expected}`);
    }
  });

  it('getChildren(specNode) returns [] when the spec has zero tasks', () => {
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

describe('SpecTreeProvider — TaskNode rendering (T017)', () => {
  it('returns one TaskNode per task in source order', () => {
    const tasks: Task[] = [
      buildTask({ id: 'T001', title: 'Bootstrap', status: 'done', line: 10 }),
      buildTask({ id: 'T002', title: 'Parser', status: 'in_progress', line: 20 }),
      buildTask({ id: 'T003', title: 'View', status: 'pending', line: 30 }),
      buildTask({ id: 'T004', title: 'Wire-up', status: 'blocked', line: 40 }),
    ];
    const model = buildModel({ tasks });
    const provider = makeProvider([model]);

    const [specNode] = provider.getChildren() as SpecNode[];
    const children = provider.getChildren(specNode) as TaskNode[];

    expect(children).to.have.lengthOf(4);
    expect(children.map((n) => n.kind)).to.deep.equal([
      'task',
      'task',
      'task',
      'task',
    ]);
    expect(children.map((n) => n.task.id)).to.deep.equal([
      'T001',
      'T002',
      'T003',
      'T004',
    ]);
    for (const child of children) {
      expect(child.specModel).to.equal(model);
    }
  });

  it('renders a TaskNode TreeItem with label, tooltip, icon, contextValue, collapsible None', () => {
    const task = buildTask({ id: 'T042', title: 'Wire it up', status: 'in_progress' });
    const model = buildModel({ tasks: [task] });
    const provider = makeProvider([model]);

    const [specNode] = provider.getChildren() as SpecNode[];
    const [taskNode] = provider.getChildren(specNode) as TaskNode[];

    const item = provider.getTreeItem(taskNode);

    expect(item.label).to.equal('T042 — Wire it up');
    expect(item.description).to.be.undefined;
    expect(item.tooltip).to.equal('T042 · status: in_progress');
    expect(item.contextValue).to.equal('aiadev.task');
    expect((item as unknown as StubTreeItem).collapsibleState).to.equal(
      StubTreeItemCollapsibleState.None,
    );
    expect(item.iconPath).to.deep.equal({
      tag: 'icon-stub',
      status: 'in_progress',
    });
  });

  it("appends ' · D / N done' to SpecNode description when tasks exist (implementing state)", () => {
    const tasks: Task[] = [
      buildTask({ id: 'T001', status: 'done' }),
      buildTask({ id: 'T002', status: 'pending' }),
      buildTask({ id: 'T003', status: 'in_progress' }),
      buildTask({ id: 'T004', status: 'blocked' }),
    ];
    const model = buildModel({
      status: 'approved',
      pipelineState: 'implementing',
      tasks,
    });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.description).to.equal('implementing · 1 / 4 done');
  });

  it('omits the done-counter suffix when the spec has zero tasks (spec → plan state)', () => {
    const provider = makeProvider([
      buildModel({
        status: 'approved',
        pipelineState: 'spec → plan',
        tasks: [],
      }),
    ]);
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.description).to.equal('spec → plan');
  });

  it('invokes the injected statusIcon factory once per task with that task status', () => {
    const tasks: Task[] = [
      buildTask({ id: 'T001', status: 'done' }),
      buildTask({ id: 'T002', status: 'pending' }),
      buildTask({ id: 'T003', status: 'blocked' }),
    ];
    const model = buildModel({ tasks });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];
    const taskNodes = provider.getChildren(specNode) as TaskNode[];

    lastStatusIconCalls = [];
    for (const node of taskNodes) {
      provider.getTreeItem(node);
    }

    expect(lastStatusIconCalls).to.deep.equal(['done', 'pending', 'blocked']);
  });
});

describe('SpecTreeProvider — TaskNode reveal command (T018)', () => {
  it('sets a vscode.open command with title "Open task" on the TaskNode TreeItem', () => {
    const task = buildTask({ id: 'T042', title: 'Wire it up', line: 17 });
    const model = buildModel({ tasks: [task] });
    const provider = makeProvider([model]);

    const [specNode] = provider.getChildren() as SpecNode[];
    const [taskNode] = provider.getChildren(specNode) as TaskNode[];

    const item = provider.getTreeItem(taskNode);
    const command = (item as unknown as StubTreeItem).command as
      | { command: string; title: string; arguments: unknown[] }
      | undefined;

    expect(command).to.exist;
    expect(command!.command).to.equal('vscode.open');
    expect(command!.title).to.equal('Open task');
  });

  it('passes a Uri pointing at specModel.tasksPath as the first argument', () => {
    const task = buildTask({ id: 'T001', line: 5 });
    const model = buildModel({
      tasks: [task],
      tasksPath: '/work/root/specs/0012-vscode-spec-explorer/tasks.md',
    });
    const provider = makeProvider([model]);

    const [specNode] = provider.getChildren() as SpecNode[];
    const [taskNode] = provider.getChildren(specNode) as TaskNode[];

    const item = provider.getTreeItem(taskNode);
    const command = (item as unknown as StubTreeItem).command as {
      arguments: [StubUri, { selection: StubRange }];
    };

    expect(command.arguments[0]).to.be.instanceOf(StubUri);
    expect(command.arguments[0].fsPath).to.equal(
      '/work/root/specs/0012-vscode-spec-explorer/tasks.md',
    );
  });

  it('passes a Range covering the heading line (task.line - 1, 0) as the selection', () => {
    const task = buildTask({ id: 'T007', line: 42 });
    const model = buildModel({ tasks: [task] });
    const provider = makeProvider([model]);

    const [specNode] = provider.getChildren() as SpecNode[];
    const [taskNode] = provider.getChildren(specNode) as TaskNode[];

    const item = provider.getTreeItem(taskNode);
    const command = (item as unknown as StubTreeItem).command as {
      arguments: [StubUri, { selection: StubRange }];
    };

    const range = command.arguments[1].selection;
    expect(range).to.be.instanceOf(StubRange);
    expect(range.startLine).to.equal(41);
    expect(range.startCharacter).to.equal(0);
    expect(range.endLine).to.equal(41);
    expect(range.endCharacter).to.equal(0);
  });

  it('leaves command undefined when tasksPath is missing', () => {
    const task = buildTask({ id: 'T001', line: 1 });
    const model = buildModel({ tasks: [task], tasksPath: undefined });
    const provider = makeProvider([model]);

    const [specNode] = provider.getChildren() as SpecNode[];
    const [taskNode] = provider.getChildren(specNode) as TaskNode[];

    const item = provider.getTreeItem(taskNode);

    expect((item as unknown as StubTreeItem).command).to.be.undefined;
  });
});

describe('SpecTreeProvider — ClarificationGroupNode rendering (T020)', () => {
  function buildClarification(overrides: Partial<Clarification> = {}): Clarification {
    return {
      id: 'cl-1',
      question: 'What is the retention policy?',
      line: 5,
      ...overrides,
    };
  }

  it('does not include a clGroup under specNode when clarifications is empty', () => {
    const model = buildModel({
      tasks: [buildTask({ id: 'T001' })],
      clarifications: [],
    });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];

    const children = provider.getChildren(specNode) as Node[];

    expect(children.map((n) => n.kind)).to.deep.equal(['task']);
    expect(children.some((n) => n.kind === 'clGroup')).to.be.false;
  });

  it('appends a single clGroup after the task nodes when clarifications exist', () => {
    const tasks: Task[] = [
      buildTask({ id: 'T001', line: 1 }),
      buildTask({ id: 'T002', line: 2 }),
      buildTask({ id: 'T003', line: 3 }),
      buildTask({ id: 'T004', line: 4 }),
    ];
    const clarifications: Clarification[] = [
      buildClarification({ id: 'cl-1', question: 'Q1?', line: 10 }),
      buildClarification({ id: 'cl-2', question: 'Q2?', line: 20 }),
    ];
    const model = buildModel({ tasks, clarifications });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];

    const children = provider.getChildren(specNode) as Node[];

    expect(children).to.have.lengthOf(5);
    expect(children.slice(0, 4).map((n) => n.kind)).to.deep.equal([
      'task',
      'task',
      'task',
      'task',
    ]);
    expect(children[4].kind).to.equal('clGroup');
    expect((children[4] as ClarificationGroupNode).specModel).to.equal(model);
  });

  it('renders the clGroup TreeItem with label, tooltip (plural), iconPath, contextValue and Expanded state', () => {
    const clarifications: Clarification[] = [
      buildClarification({ id: 'cl-1' }),
      buildClarification({ id: 'cl-2' }),
    ];
    const model = buildModel({ tasks: [], clarifications });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];
    const [groupNode] = provider.getChildren(specNode) as ClarificationGroupNode[];

    const item = provider.getTreeItem(groupNode);

    expect(item.label).to.equal('Clarifications (2)');
    expect(item.description).to.be.undefined;
    expect(item.tooltip).to.equal('2 unresolved clarifications');
    expect(item.contextValue).to.equal('aiadev.clarificationGroup');
    expect((item as unknown as StubTreeItem).collapsibleState).to.equal(
      StubTreeItemCollapsibleState.Expanded,
    );
    expect(item.iconPath).to.be.instanceOf(StubThemeIcon);
    expect((item.iconPath as StubThemeIcon).id).to.equal('question');
  });

  it('uses the singular form when there is exactly one clarification', () => {
    const model = buildModel({
      tasks: [],
      clarifications: [buildClarification({ id: 'cl-1' })],
    });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];
    const [groupNode] = provider.getChildren(specNode) as ClarificationGroupNode[];

    const item = provider.getTreeItem(groupNode);

    expect(item.label).to.equal('Clarifications (1)');
    expect(item.tooltip).to.equal('1 unresolved clarification');
  });

  it('getChildren(clGroupNode) returns one ClarificationNode per clarification, in source order', () => {
    const clarifications: Clarification[] = [
      buildClarification({ id: 'cl-1', question: 'First?', line: 10 }),
      buildClarification({ id: 'cl-2', question: 'Second?', line: 20 }),
    ];
    const model = buildModel({ tasks: [], clarifications });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];
    const [groupNode] = provider.getChildren(specNode) as ClarificationGroupNode[];

    const children = provider.getChildren(groupNode) as ClarificationNode[];

    expect(children).to.have.lengthOf(2);
    expect(children.map((n) => n.kind)).to.deep.equal(['cl', 'cl']);
    expect(children.map((n) => n.clarification.id)).to.deep.equal(['cl-1', 'cl-2']);
    for (const child of children) {
      expect(child.specModel).to.equal(model);
    }
  });

  it('renders a clNode with id label, truncates a long question to 80 chars + …', () => {
    const longQuestion =
      'This is a very long clarification question that goes on and on and definitely exceeds eighty characters in length.';
    expect(longQuestion.length).to.be.greaterThan(80);
    const clarifications: Clarification[] = [
      buildClarification({ id: 'cl-7', question: longQuestion, line: 42 }),
    ];
    const model = buildModel({ tasks: [], clarifications });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];
    const [groupNode] = provider.getChildren(specNode) as ClarificationGroupNode[];
    const [clNode] = provider.getChildren(groupNode) as ClarificationNode[];

    const item = provider.getTreeItem(clNode);

    expect(item.label).to.equal('cl-7');
    expect(item.description).to.equal(longQuestion.slice(0, 80) + '…');
    expect((item.description as string).length).to.equal(81);
    expect(item.tooltip).to.equal(longQuestion);
    expect(item.contextValue).to.equal('aiadev.clarification');
    expect((item as unknown as StubTreeItem).collapsibleState).to.equal(
      StubTreeItemCollapsibleState.None,
    );
  });

  it('shows a short question untruncated with no trailing ellipsis', () => {
    const shortQuestion = 'Short question?';
    const clarifications: Clarification[] = [
      buildClarification({ id: 'cl-3', question: shortQuestion }),
    ];
    const model = buildModel({ tasks: [], clarifications });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];
    const [groupNode] = provider.getChildren(specNode) as ClarificationGroupNode[];
    const [clNode] = provider.getChildren(groupNode) as ClarificationNode[];

    const item = provider.getTreeItem(clNode);

    expect(item.description).to.equal(shortQuestion);
    expect(item.description).to.not.contain('…');
    expect(item.tooltip).to.equal(shortQuestion);
  });

  it('getChildren(clNode) returns []', () => {
    const clarifications: Clarification[] = [buildClarification()];
    const model = buildModel({ tasks: [], clarifications });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];
    const [groupNode] = provider.getChildren(specNode) as ClarificationGroupNode[];
    const [clNode] = provider.getChildren(groupNode) as ClarificationNode[];

    expect(provider.getChildren(clNode)).to.deep.equal([]);
  });
});

describe('SpecTreeProvider — ClarificationNode reveal command (T021)', () => {
  function buildClarification(overrides: Partial<Clarification> = {}): Clarification {
    return {
      id: 'cl-1',
      question: 'What is the retention policy?',
      line: 5,
      ...overrides,
    };
  }

  it('sets a vscode.open command with title "Open clarification" on the ClarificationNode TreeItem', () => {
    const clarifications: Clarification[] = [
      buildClarification({ id: 'cl-1', line: 7 }),
    ];
    const model = buildModel({ tasks: [], clarifications });
    const provider = makeProvider([model]);

    const [specNode] = provider.getChildren() as SpecNode[];
    const [groupNode] = provider.getChildren(specNode) as ClarificationGroupNode[];
    const [clNode] = provider.getChildren(groupNode) as ClarificationNode[];

    const item = provider.getTreeItem(clNode);
    const command = (item as unknown as StubTreeItem).command as
      | { command: string; title: string; arguments: unknown[] }
      | undefined;

    expect(command).to.exist;
    expect(command!.command).to.equal('vscode.open');
    expect(command!.title).to.equal('Open clarification');
  });

  it('passes a Uri pointing at specModel.specPath as the first argument', () => {
    const clarifications: Clarification[] = [
      buildClarification({ id: 'cl-1', line: 5 }),
    ];
    const model = buildModel({
      tasks: [],
      clarifications,
      specPath: '/work/root/specs/0012-vscode-spec-explorer/spec.md',
    });
    const provider = makeProvider([model]);

    const [specNode] = provider.getChildren() as SpecNode[];
    const [groupNode] = provider.getChildren(specNode) as ClarificationGroupNode[];
    const [clNode] = provider.getChildren(groupNode) as ClarificationNode[];

    const item = provider.getTreeItem(clNode);
    const command = (item as unknown as StubTreeItem).command as {
      arguments: [StubUri, { selection: StubRange }];
    };

    expect(command.arguments[0]).to.be.instanceOf(StubUri);
    expect(command.arguments[0].fsPath).to.equal(
      '/work/root/specs/0012-vscode-spec-explorer/spec.md',
    );
  });

  it('passes a Range covering the marker line (cl.line - 1, 0) as the selection', () => {
    const clarifications: Clarification[] = [
      buildClarification({ id: 'cl-9', line: 42 }),
    ];
    const model = buildModel({ tasks: [], clarifications });
    const provider = makeProvider([model]);

    const [specNode] = provider.getChildren() as SpecNode[];
    const [groupNode] = provider.getChildren(specNode) as ClarificationGroupNode[];
    const [clNode] = provider.getChildren(groupNode) as ClarificationNode[];

    const item = provider.getTreeItem(clNode);
    const command = (item as unknown as StubTreeItem).command as {
      arguments: [StubUri, { selection: StubRange }];
    };

    const range = command.arguments[1].selection;
    expect(range).to.be.instanceOf(StubRange);
    expect(range.startLine).to.equal(41);
    expect(range.startCharacter).to.equal(0);
    expect(range.endLine).to.equal(41);
    expect(range.endCharacter).to.equal(0);
  });
});

describe('SpecTreeProvider — Pipeline-state badge on SpecNode (T022)', () => {
  interface BadgeCase {
    pipelineState: PipelineState;
    tasks: Task[];
    expectedDescription: string;
    expectedIcon: string;
    expectedNextHint: string;
  }

  const doneTask = buildTask({ id: 'T001', status: 'done' });
  const pendingTask = buildTask({ id: 'T002', status: 'pending' });
  const inProgressTask = buildTask({ id: 'T003', status: 'in_progress' });

  const cases: BadgeCase[] = [
    {
      pipelineState: 'spec',
      tasks: [],
      expectedDescription: 'spec',
      expectedIcon: 'symbol-file',
      expectedNextHint: 'Next: run /aiadev:plan',
    },
    {
      pipelineState: 'spec → plan',
      tasks: [],
      expectedDescription: 'spec → plan',
      expectedIcon: 'symbol-file',
      expectedNextHint: 'Next: run /aiadev:tasks',
    },
    {
      pipelineState: 'spec → plan → tasks',
      tasks: [
        buildTask({ id: 'T001', status: 'pending' }),
        buildTask({ id: 'T002', status: 'pending' }),
        buildTask({ id: 'T003', status: 'pending' }),
      ],
      expectedDescription: 'spec → plan → tasks · 0 / 3 done',
      expectedIcon: 'symbol-file',
      expectedNextHint: 'Next: run /aiadev:implement',
    },
    {
      pipelineState: 'implementing',
      tasks: [doneTask, inProgressTask, pendingTask],
      expectedDescription: 'implementing · 1 / 3 done',
      expectedIcon: 'sync~spin',
      expectedNextHint: 'Next: continue running /aiadev:implement',
    },
    {
      pipelineState: 'complete',
      tasks: [
        buildTask({ id: 'T001', status: 'done' }),
        buildTask({ id: 'T002', status: 'done' }),
        buildTask({ id: 'T003', status: 'done' }),
      ],
      expectedDescription: 'complete',
      expectedIcon: 'check-all',
      expectedNextHint:
        'Next: run /aiadev:analyze then /aiadev:requesting-code-review',
    },
  ];

  for (const c of cases) {
    it(`renders correct badge + icon for pipelineState='${c.pipelineState}'`, () => {
      const model = buildModel({
        pipelineState: c.pipelineState,
        tasks: c.tasks,
      });
      const provider = makeProvider([model]);
      const [specNode] = provider.getChildren() as SpecNode[];

      const item = provider.getTreeItem(specNode);

      expect(item.description).to.equal(c.expectedDescription);
      expect(item.iconPath).to.be.instanceOf(StubThemeIcon);
      expect((item.iconPath as StubThemeIcon).id).to.equal(c.expectedIcon);
    });

    it(`tooltip contains the Next-action hint for pipelineState='${c.pipelineState}'`, () => {
      const model = buildModel({
        pipelineState: c.pipelineState,
        tasks: c.tasks,
        status: 'approved',
      });
      const provider = makeProvider([model]);
      const [specNode] = provider.getChildren() as SpecNode[];

      const item = provider.getTreeItem(specNode);

      expect(item.tooltip).to.contain(c.expectedNextHint);
      expect(item.tooltip).to.contain(model.specDirName);
      expect(item.tooltip).to.contain(c.pipelineState);
      expect(item.tooltip).to.contain('Status: Approved');
      expect(item.tooltip).to.contain(model.specPath);
    });
  }

  it('tooltip is parseError verbatim when set, ignoring multi-line construction', () => {
    const model = buildModel({
      status: 'unknown',
      pipelineState: 'spec',
      parseError: 'Status header missing',
    });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.tooltip).to.equal('Status header missing');
  });
});

describe('SpecTreeProvider — Multi-root folder prefix on SpecNode (T023)', () => {
  it('renders label without folder prefix when multiRoot is false (default)', () => {
    const model = buildModel({
      workspaceFolderName: 'frontend',
      specId: '0001',
      title: 'Title',
    });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.label).to.equal('0001 — Title');
  });

  it('renders label with [<workspaceFolderName>] prefix when multiRoot is true', () => {
    const model = buildModel({
      workspaceFolderName: 'frontend',
      specId: '0001',
      title: 'Title',
    });
    const provider = makeProvider([model], undefined, { multiRoot: true });
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.label).to.equal('[frontend] 0001 — Title');
  });

  it('also prefixes the specDirName fallback (when title is empty) under multiRoot', () => {
    const model = buildModel({
      workspaceFolderName: 'backend',
      specDirName: '0099-mystery',
      title: '',
    });
    const provider = makeProvider([model], undefined, { multiRoot: true });
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.label).to.equal('[backend] 0099-mystery');
  });

  it('setMultiRoot(true) flips the label and fires the change event', () => {
    const model = buildModel({
      workspaceFolderName: 'frontend',
      specId: '0001',
      title: 'Title',
    });
    const provider = makeProvider([model]);
    const captured = lastEmitter!;
    const [specNode] = provider.getChildren() as SpecNode[];

    const before = provider.getTreeItem(specNode);
    expect(before.label).to.equal('0001 — Title');
    expect(captured.fired).to.have.lengthOf(0);

    provider.setMultiRoot(true);

    const after = provider.getTreeItem(specNode);
    expect(after.label).to.equal('[frontend] 0001 — Title');
    expect(captured.fired).to.have.lengthOf(1);
    expect(captured.fired[0]).to.be.undefined;
  });

  it('setMultiRoot(value) does not fire when value is unchanged', () => {
    const provider = makeProvider([buildModel()]);
    const captured = lastEmitter!;

    provider.setMultiRoot(false);

    expect(captured.fired).to.have.lengthOf(0);
  });
});

describe('SpecTreeProvider — Branch highlight on SpecNode (T024)', () => {
  it('renders no "● current" suffix when no current branch is set for the folder', () => {
    const model = buildModel({
      workspaceFolderUri: '/work/root',
      branch: 'feature/vscode-spec-explorer',
      pipelineState: 'spec',
      tasks: [],
    });
    const provider = makeProvider([model]);
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.description).to.equal('spec');
    expect(item.description).to.not.contain('● current');
  });

  it('appends " · ● current" to description when current branch matches model.branch', () => {
    const model = buildModel({
      workspaceFolderUri: '/work/root',
      branch: 'feature/vscode-spec-explorer',
      pipelineState: 'spec',
      tasks: [],
    });
    const provider = makeProvider([model]);
    provider.setCurrentBranch('/work/root', 'feature/vscode-spec-explorer');
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.description).to.equal('spec · ● current');
  });

  it('appends " · ● current" after the done counter when in implementing state', () => {
    const tasks: Task[] = [
      buildTask({ id: 'T001', status: 'done' }),
      buildTask({ id: 'T002', status: 'pending' }),
      buildTask({ id: 'T003', status: 'pending' }),
    ];
    const model = buildModel({
      workspaceFolderUri: '/work/root',
      branch: 'feature/vscode-spec-explorer',
      pipelineState: 'implementing',
      tasks,
    });
    const provider = makeProvider([model]);
    provider.setCurrentBranch('/work/root', 'feature/vscode-spec-explorer');
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.description).to.equal('implementing · 1 / 3 done · ● current');
  });

  it('does not append "● current" when current branch does not match model.branch', () => {
    const model = buildModel({
      workspaceFolderUri: '/work/root',
      branch: 'feature/vscode-spec-explorer',
      pipelineState: 'spec',
      tasks: [],
    });
    const provider = makeProvider([model]);
    provider.setCurrentBranch('/work/root', 'main');
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.description).to.equal('spec');
    expect(item.description).to.not.contain('● current');
  });

  it('does not append "● current" when the current branch is set for a different folder uri', () => {
    const model = buildModel({
      workspaceFolderUri: '/work/root',
      branch: 'feature/vscode-spec-explorer',
      pipelineState: 'spec',
      tasks: [],
    });
    const provider = makeProvider([model]);
    provider.setCurrentBranch('/work/other', 'feature/vscode-spec-explorer');
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.description).to.equal('spec');
  });

  it('preserves the pipeline-state iconPath even when the spec is the current branch', () => {
    const model = buildModel({
      workspaceFolderUri: '/work/root',
      branch: 'feature/vscode-spec-explorer',
      pipelineState: 'implementing',
      tasks: [buildTask({ id: 'T001', status: 'done' })],
    });
    const provider = makeProvider([model]);
    provider.setCurrentBranch('/work/root', 'feature/vscode-spec-explorer');
    const [specNode] = provider.getChildren() as SpecNode[];

    const item = provider.getTreeItem(specNode);

    expect(item.iconPath).to.be.instanceOf(StubThemeIcon);
    expect((item.iconPath as StubThemeIcon).id).to.equal('sync~spin');
  });

  it('setCurrentBranch fires the change event when the value changes', () => {
    const provider = makeProvider([buildModel({ workspaceFolderUri: '/work/root' })]);
    const captured = lastEmitter!;

    expect(captured.fired).to.have.lengthOf(0);

    provider.setCurrentBranch('/work/root', 'main');

    expect(captured.fired).to.have.lengthOf(1);
    expect(captured.fired[0]).to.be.undefined;
  });

  it('setCurrentBranch does not fire when the value is unchanged', () => {
    const provider = makeProvider([buildModel({ workspaceFolderUri: '/work/root' })]);
    const captured = lastEmitter!;

    provider.setCurrentBranch('/work/root', 'main');
    expect(captured.fired).to.have.lengthOf(1);

    provider.setCurrentBranch('/work/root', 'main');
    expect(captured.fired).to.have.lengthOf(1);
  });

  it('setCurrentBranch(uri, undefined) clears a previously set value and removes the highlight', () => {
    const model = buildModel({
      workspaceFolderUri: '/work/root',
      branch: 'feature/vscode-spec-explorer',
      pipelineState: 'spec',
      tasks: [],
    });
    const provider = makeProvider([model]);
    provider.setCurrentBranch('/work/root', 'feature/vscode-spec-explorer');
    const [specNode] = provider.getChildren() as SpecNode[];

    const before = provider.getTreeItem(specNode);
    expect(before.description).to.equal('spec · ● current');

    const captured = lastEmitter!;
    const firesBefore = captured.fired.length;

    provider.setCurrentBranch('/work/root', undefined);

    const after = provider.getTreeItem(specNode);
    expect(after.description).to.equal('spec');
    expect(captured.fired.length).to.equal(firesBefore + 1);
  });

  it('setCurrentBranch(uri, undefined) is a no-op (no fire) when no value was set', () => {
    const provider = makeProvider([buildModel({ workspaceFolderUri: '/work/root' })]);
    const captured = lastEmitter!;

    provider.setCurrentBranch('/work/root', undefined);

    expect(captured.fired).to.have.lengthOf(0);
  });
});
