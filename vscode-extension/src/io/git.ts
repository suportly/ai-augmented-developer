import * as vscode from 'vscode';

/**
 * Thin abstraction over the read-only git information the spec-explorer needs.
 *
 * The production implementation (`VsCodeGitHeadProvider`) wraps the built-in
 * `vscode.git` extension's API so tests can swap in a deterministic fake.
 */
export interface GitHeadProvider {
  /**
   * Returns the current HEAD branch name (e.g. 'feature/foo'), or undefined if
   * not on a branch / no repo / API unavailable.
   */
  getCurrentBranch(repoFsPath: string): Promise<string | undefined>;
}

/**
 * Minimal subset of the `vscode.git` extension's API surface that we touch.
 * Re-declared here so we don't take a hard dependency on the extension's
 * `.d.ts` (which is bundled inside the extension itself, not on npm).
 */
interface GitRepositoryState {
  readonly HEAD?: { readonly name?: string };
}

interface GitRepository {
  readonly rootUri: vscode.Uri;
  readonly state: GitRepositoryState;
}

interface GitApi {
  readonly repositories: readonly GitRepository[];
}

interface GitExtensionExports {
  getAPI(version: 1): GitApi;
}

/** Production `GitHeadProvider` backed by the built-in `vscode.git` extension. */
export class VsCodeGitHeadProvider implements GitHeadProvider {
  private cachedApi: GitApi | undefined;

  async getCurrentBranch(repoFsPath: string): Promise<string | undefined> {
    try {
      const api = this.getApi();
      if (!api) {
        return undefined;
      }
      const repo = api.repositories.find(
        (r) => r.rootUri.fsPath === repoFsPath,
      );
      if (!repo) {
        return undefined;
      }
      return repo.state.HEAD?.name;
    } catch {
      // TODO(T025): wire an OutputChannel here so caught errors surface as a
      // single-line diagnostic instead of being swallowed silently.
      return undefined;
    }
  }

  private getApi(): GitApi | undefined {
    if (this.cachedApi) {
      return this.cachedApi;
    }
    const extension =
      vscode.extensions.getExtension<GitExtensionExports>('vscode.git');
    const exports = extension?.exports;
    if (!exports) {
      return undefined;
    }
    this.cachedApi = exports.getAPI(1);
    return this.cachedApi;
  }
}
