import { expect } from 'chai';

import { FakeFileSystem } from '../../support/fakeFileSystem';

describe('FakeFileSystem', () => {
  describe('findFiles', () => {
    it('returns matching files in sorted order for a `*` pattern', async () => {
      const fs = new FakeFileSystem({
        '/ws/specs/0001-foo/spec.md': '# foo',
        '/ws/specs/0001-foo/tasks.md': '- task',
        '/ws/specs/0002-bar/spec.md': '# bar',
      });

      const result = await fs.findFiles('/ws', 'specs/*/spec.md');

      expect(result).to.deep.equal([
        '/ws/specs/0001-foo/spec.md',
        '/ws/specs/0002-bar/spec.md',
      ]);
    });

    it('expands brace alternation `{a,b}`', async () => {
      const fs = new FakeFileSystem({
        '/ws/specs/0001-foo/spec.md': '# foo',
        '/ws/specs/0001-foo/tasks.md': '- task',
        '/ws/specs/0002-bar/spec.md': '# bar',
        '/ws/specs/0002-bar/plan.md': '# plan (excluded)',
      });

      const result = await fs.findFiles('/ws', 'specs/*/{spec,tasks}.md');

      expect(result).to.deep.equal([
        '/ws/specs/0001-foo/spec.md',
        '/ws/specs/0001-foo/tasks.md',
        '/ws/specs/0002-bar/spec.md',
      ]);
    });

    it('returns an empty array when nothing matches', async () => {
      const fs = new FakeFileSystem({
        '/ws/README.md': 'readme',
      });

      const result = await fs.findFiles('/ws', 'specs/*/spec.md');

      expect(result).to.deep.equal([]);
    });
  });

  describe('readFileText', () => {
    it('returns the stored content for a known path', async () => {
      const fs = new FakeFileSystem({
        '/ws/specs/0001-foo/spec.md': '# foo\nhello',
      });

      const content = await fs.readFileText('/ws/specs/0001-foo/spec.md');

      expect(content).to.equal('# foo\nhello');
    });

    it('rejects with an ENOENT error for an unknown path', async () => {
      const fs = new FakeFileSystem({});

      let caught: Error | undefined;
      try {
        await fs.readFileText('/ws/missing.md');
      } catch (err) {
        caught = err as Error;
      }

      expect(caught).to.be.instanceOf(Error);
      expect(caught!.message).to.include('ENOENT');
      expect(caught!.message).to.include('/ws/missing.md');
    });
  });

  describe('exists', () => {
    it('returns true for a known path', async () => {
      const fs = new FakeFileSystem({
        '/ws/specs/0001-foo/spec.md': '# foo',
      });

      expect(await fs.exists('/ws/specs/0001-foo/spec.md')).to.equal(true);
    });

    it('returns false for an unknown path', async () => {
      const fs = new FakeFileSystem({});

      expect(await fs.exists('/ws/missing.md')).to.equal(false);
    });
  });
});
