/**
 * Maps a {@link TaskStatus} value to a `vscode.ThemeIcon` for display in the
 * spec explorer tree.
 *
 * The module is split into two layers so it can be unit-tested without
 * loading the `vscode` runtime module (which is unavailable outside the
 * extension host):
 *
 *  - {@link makeStatusIcon} accepts the `ThemeIcon` / `ThemeColor`
 *    constructors as parameters. Tests pass in stubs.
 *  - {@link statusIcon} lazily binds the factory to the real `vscode`
 *    constructors at first call, so production code stays a one-liner.
 *
 * The mapping itself is fixed by plan.md Phase 4 / spec Story 2 scenario 1.
 */
import { assertNever, type TaskStatus } from '../parser/types';

export interface IconCtors {
  ThemeIcon: new (id: string, color?: unknown) => unknown;
  ThemeColor: new (id: string) => unknown;
}

export function makeStatusIcon(ctors: IconCtors): (status: TaskStatus) => unknown {
  return function statusIcon(status: TaskStatus): unknown {
    switch (status) {
      case 'pending':
        return new ctors.ThemeIcon('circle-outline');
      case 'in_progress':
        return new ctors.ThemeIcon('sync~spin', new ctors.ThemeColor('charts.blue'));
      case 'blocked':
        return new ctors.ThemeIcon('error', new ctors.ThemeColor('errorForeground'));
      case 'done':
        return new ctors.ThemeIcon('check', new ctors.ThemeColor('charts.green'));
      case 'unknown':
        return new ctors.ThemeIcon('question');
      default:
        return assertNever(status);
    }
  };
}

let cached: ((status: TaskStatus) => unknown) | undefined;

/**
 * Production entry point. Binds {@link makeStatusIcon} to the real
 * `vscode.ThemeIcon` / `vscode.ThemeColor` constructors on first call.
 *
 * Uses `require('vscode')` so unit tests that import `makeStatusIcon`
 * directly never trigger the host-only module load. esbuild externalises
 * `vscode`, so the bundled output keeps the dynamic require intact.
 */
export function statusIcon(status: TaskStatus): unknown {
  if (!cached) {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const vscode = require('vscode') as IconCtors;
    cached = makeStatusIcon({ ThemeIcon: vscode.ThemeIcon, ThemeColor: vscode.ThemeColor });
  }
  return cached(status);
}
