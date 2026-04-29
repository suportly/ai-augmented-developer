import { runTests } from '@vscode/test-electron';
import * as path from 'path';

// NOTE: multi-root integration testing is deferred. Passing two folder paths on
// the CLI is not reliably treated as a multi-root workspace by the VS Code
// Extension Host; the correct approach is a .code-workspace file, which
// requires a separate extensionTestsPath and fixture. The multi-root rendering
// path (SpecNode label prefixed with [folderName]) is exhaustively covered by
// the stub-based unit tests in test/unit/views/specTreeProvider.spec.ts (T023).
// Track in: https://github.com/suportly/ai-augmented-developer/issues — "T029 follow-up: multi-root integration test via .code-workspace"

async function main(): Promise<void> {
  // __dirname at runtime: <ext-root>/out/test/integration/
  // extensionDevelopmentPath: <ext-root>/
  // extensionTestsPath:       <ext-root>/out/test/integration/suite/index
  // workspacePath:            <ext-root>/test/fixtures/workspaces/single-root
  const extensionDevelopmentPath = path.resolve(__dirname, '../../../');
  const extensionTestsPath = path.resolve(__dirname, './suite/index');
  const workspacePath = path.resolve(extensionDevelopmentPath, 'test/fixtures/workspaces/single-root');
  await runTests({
    extensionDevelopmentPath,
    extensionTestsPath,
    launchArgs: [
      workspacePath,
      '--disable-gpu',
      '--no-sandbox',
    ],
  });
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
