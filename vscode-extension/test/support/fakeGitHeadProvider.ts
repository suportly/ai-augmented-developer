import { GitHeadProvider } from '../../src/io/git';

/**
 * Deterministic in-memory `GitHeadProvider` for unit tests.
 *
 * Maps repository fs-paths to branch names. A path that is absent from the map
 * (or whose value is `undefined`) yields `undefined`, mirroring the production
 * provider's behaviour for missing repos / detached HEAD / API failures.
 */
export class FakeGitHeadProvider implements GitHeadProvider {
  private readonly branches: Map<string, string | undefined>;

  constructor(branches: Record<string, string | undefined>) {
    this.branches = new Map(Object.entries(branches));
  }

  async getCurrentBranch(repoFsPath: string): Promise<string | undefined> {
    return this.branches.get(repoFsPath);
  }

  setBranch(repoFsPath: string, branch: string | undefined): void {
    this.branches.set(repoFsPath, branch);
  }
}
