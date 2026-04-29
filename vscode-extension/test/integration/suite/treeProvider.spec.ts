import * as assert from 'assert';
import * as vscode from 'vscode';
import type { WiredExtension } from '../../../src/extension';

suite('Tree provider', () => {
  test('spec.md present → refresh produces at least one spec entry (Story 1.1)', async function() {
    this.timeout(20000);
    // Give the extension 2 s to do its initial refresh after activation.
    await new Promise(r => setTimeout(r, 2000));
    await vscode.commands.executeCommand('aiadev.specExplorer.refresh');
    await new Promise(r => setTimeout(r, 2000));

    const ext = vscode.extensions.getExtension('aiadev.aiadev-spec-explorer');
    assert.ok(ext, 'Extension not found — check publisher.name in package.json');
    const exports = ext.exports as { getWiredExtension(): WiredExtension | undefined };
    const w = exports.getWiredExtension();
    assert.ok(w, 'wireExtension should have been called on activation');

    const nodes = w.provider.getChildren();
    assert.ok(nodes.length > 0, `Expected at least one SpecNode, got ${nodes.length}`);

    // Assert the first node is a SpecNode for the fixture spec.
    const first = nodes[0] as { kind: string; model: { specId: string; title: string } };
    assert.strictEqual(first.kind, 'spec', 'first node should be a spec node');
    assert.strictEqual(first.model.specId, '0001', `Expected specId '0001', got '${first.model.specId}'`);
  });

  test('SpecNode children include TaskNodes from tasks.md (Story 2.1 smoke)', async function() {
    this.timeout(10000);
    // The fixture has 2 tasks (T001 pending, T002 done).
    const ext = vscode.extensions.getExtension('aiadev.aiadev-spec-explorer');
    assert.ok(ext);
    const w = (ext.exports as { getWiredExtension(): WiredExtension | undefined }).getWiredExtension();
    assert.ok(w, 'wireExtension should have been called');

    const specNodes = w.provider.getChildren();
    assert.ok(specNodes.length > 0);
    const taskNodes = w.provider.getChildren(specNodes[0] as Parameters<typeof w.provider.getChildren>[0]);
    // First N task-like children (before any clarification group).
    const tasks = taskNodes.filter((n: { kind: string }) => n.kind === 'task');
    assert.strictEqual(tasks.length, 2, `Expected 2 task nodes from fixture, got ${tasks.length}`);
  });

  test('refresh resolves idempotently on a populated workspace (no-crash)', async () => {
    // Verifies the provider handles a second refresh without error.
    // Note: a true empty-workspace test would require a separate Extension Host launch;
    // that is deferred to the multi-root / code-workspace follow-up.
    await assert.doesNotReject(
      () => Promise.resolve(vscode.commands.executeCommand('aiadev.specExplorer.refresh'))
    );
  });
});
