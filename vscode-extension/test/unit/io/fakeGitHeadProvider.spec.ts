import { expect } from 'chai';

import { FakeGitHeadProvider } from '../../support/fakeGitHeadProvider';

describe('FakeGitHeadProvider', () => {
  it('returns the configured branch for a known repo path', async () => {
    const provider = new FakeGitHeadProvider({
      '/ws/repo-a': 'feature/foo',
    });

    const branch = await provider.getCurrentBranch('/ws/repo-a');

    expect(branch).to.equal('feature/foo');
  });

  it('returns undefined for an unknown path (not in map)', async () => {
    const provider = new FakeGitHeadProvider({
      '/ws/repo-a': 'feature/foo',
    });

    const branch = await provider.getCurrentBranch('/ws/missing');

    expect(branch).to.be.undefined;
  });

  it('returns undefined when the configured value is explicitly undefined', async () => {
    const provider = new FakeGitHeadProvider({
      '/ws/repo-detached': undefined,
    });

    const branch = await provider.getCurrentBranch('/ws/repo-detached');

    expect(branch).to.be.undefined;
  });

  it('setBranch updates the value for subsequent calls', async () => {
    const provider = new FakeGitHeadProvider({
      '/ws/repo-a': 'feature/foo',
    });

    expect(await provider.getCurrentBranch('/ws/repo-a')).to.equal(
      'feature/foo',
    );

    provider.setBranch('/ws/repo-a', 'feature/bar');
    expect(await provider.getCurrentBranch('/ws/repo-a')).to.equal(
      'feature/bar',
    );

    provider.setBranch('/ws/repo-new', 'main');
    expect(await provider.getCurrentBranch('/ws/repo-new')).to.equal('main');

    provider.setBranch('/ws/repo-a', undefined);
    expect(await provider.getCurrentBranch('/ws/repo-a')).to.be.undefined;
  });
});
