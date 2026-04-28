import { FileSystem } from '../../src/io/filesystem';

/**
 * In-memory `FileSystem` implementation for unit tests.
 *
 * Glob support is intentionally minimal — only what `aggregate.ts` (T012) and
 * `watcher.ts` (T019) need:
 *
 *   - literal path segments
 *   - `*`  — matches one path segment, no `/`
 *   - `**` — matches zero or more path segments
 *   - `{a,b,c}` — alternation, expanded at parse time into multiple patterns
 *
 * Anything else (character classes, `?`, escapes) is unsupported.
 */
export class FakeFileSystem implements FileSystem {
  private readonly files: Map<string, string>;

  constructor(files: Record<string, string>) {
    this.files = new Map(Object.entries(files));
  }

  async findFiles(folderFsPath: string, pattern: string): Promise<string[]> {
    const base = folderFsPath.endsWith('/')
      ? folderFsPath.slice(0, -1)
      : folderFsPath;
    const expanded = expandBraces(pattern);
    const regexes = expanded.map((p) => globToRegExp(p));

    const matches: string[] = [];
    for (const path of this.files.keys()) {
      const prefix = base + '/';
      if (!path.startsWith(prefix)) {
        continue;
      }
      const relative = path.slice(prefix.length);
      if (regexes.some((re) => re.test(relative))) {
        matches.push(path);
      }
    }
    matches.sort();
    return matches;
  }

  async readFileText(absoluteFsPath: string): Promise<string> {
    const content = this.files.get(absoluteFsPath);
    if (content === undefined) {
      throw new Error('ENOENT: ' + absoluteFsPath);
    }
    return content;
  }

  async exists(absoluteFsPath: string): Promise<boolean> {
    return this.files.has(absoluteFsPath);
  }
}

/**
 * Expand `{a,b,c}` alternations into the cartesian product of literal patterns.
 * `foo/{a,b}.md` -> ['foo/a.md', 'foo/b.md']. Nested braces are not supported.
 */
function expandBraces(pattern: string): string[] {
  const match = /\{([^{}]+)\}/.exec(pattern);
  if (!match) {
    return [pattern];
  }
  const whole = match[0];
  const inner = match[1];
  const options = inner.split(',');
  const before = pattern.slice(0, match.index);
  const after = pattern.slice(match.index + whole.length);
  const out: string[] = [];
  for (const opt of options) {
    out.push(...expandBraces(before + opt + after));
  }
  return out;
}

/**
 * Convert a brace-free glob pattern into an anchored RegExp.
 * Supports `**`, `*`, and literal segments.
 */
function globToRegExp(pattern: string): RegExp {
  let re = '';
  let i = 0;
  while (i < pattern.length) {
    const c = pattern[i];
    if (c === '*' && pattern[i + 1] === '*') {
      // `**` matches zero or more path segments. Consume an optional trailing
      // slash so `**/foo` matches `foo` (zero segments) too.
      re += '.*';
      i += 2;
      if (pattern[i] === '/') {
        i += 1;
      }
    } else if (c === '*') {
      re += '[^/]*';
      i += 1;
    } else if (/[.+^${}()|[\]\\]/.test(c)) {
      re += '\\' + c;
      i += 1;
    } else {
      re += c;
      i += 1;
    }
  }
  return new RegExp('^' + re + '$');
}
