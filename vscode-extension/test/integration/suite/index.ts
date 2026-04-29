import * as path from 'path';
import * as fs from 'fs';
import Mocha from 'mocha';

function findSpecFiles(dir: string): string[] {
  const results: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...findSpecFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith('.spec.js')) {
      results.push(fullPath);
    }
  }
  return results;
}

export function run(): Promise<void> {
  const mocha = new Mocha({ ui: 'tdd', color: true, timeout: 30000 });
  const testsRoot = path.resolve(__dirname, '.');
  return new Promise((resolve, reject) => {
    try {
      const files = findSpecFiles(testsRoot);
      files.forEach(f => mocha.addFile(f));
      mocha.run((failures: number) => failures > 0 ? reject(new Error(`${failures} tests failed`)) : resolve());
    } catch (err) {
      reject(err);
    }
  });
}
