import * as assert from 'assert';
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

suite('File watcher', () => {
  test('mutating tasks.md and running refresh does not crash (Story 2.2 smoke)', async function() {
    this.timeout(10000);
    const ws = vscode.workspace.workspaceFolders?.[0];
    assert.ok(ws);
    const tasksPath = path.join(ws.uri.fsPath, 'specs', '0001-alpha', 'tasks.md');
    const original = fs.readFileSync(tasksPath, 'utf-8');
    try {
      // Flip one task to 'done'.
      const mutated = original.replace('**Status:** pending', '**Status:** done');
      fs.writeFileSync(tasksPath, mutated, 'utf-8');
      // Give the watcher debounce window (100 ms) + a safety margin.
      await new Promise(r => setTimeout(r, 500));
      await assert.doesNotReject(
        () => Promise.resolve(vscode.commands.executeCommand('aiadev.specExplorer.refresh'))
      );
    } finally {
      fs.writeFileSync(tasksPath, original, 'utf-8');
    }
  });
});
