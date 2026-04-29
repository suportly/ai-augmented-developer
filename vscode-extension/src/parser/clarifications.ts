/**
 * Extract `[NEEDS CLARIFICATION:cl-N <question>]` markers from a Markdown
 * source string.
 *
 * Markers without a `cl-N` id (legacy free-form markers) are intentionally
 * ignored — assigning ids is the `clarify` skill's job, not this parser's.
 */

import type { Clarification } from './types';

const BOM = '﻿';

// `[NEEDS CLARIFICATION:` then optional whitespace, then `cl-<N>`, at least
// one whitespace char, then the question body (anything except `]`), closed
// by `]`. Markers do not nest, so a non-greedy `[^\]]*` body is enough.
const MARKER_PATTERN =
  /\[NEEDS CLARIFICATION:\s*(cl-\d+)\s+([^\]]*)\]/g;

export function extractClarifications(source: string): Clarification[] {
  if (!source) {
    return [];
  }

  const normalized = source.startsWith(BOM) ? source.slice(BOM.length) : source;
  const lines = normalized.split(/\r?\n/);

  // Map each line's start offset within `normalized`, accounting for either
  // `\n` or `\r\n` line endings.
  const lineStartOffsets: number[] = new Array(lines.length);
  let cursor = 0;
  for (let i = 0; i < lines.length; i += 1) {
    lineStartOffsets[i] = cursor;
    cursor += lines[i].length;
    if (cursor < normalized.length && normalized[cursor] === '\r') {
      cursor += 1;
    }
    if (cursor < normalized.length && normalized[cursor] === '\n') {
      cursor += 1;
    }
  }

  function lineForOffset(offset: number): number {
    let lo = 0;
    let hi = lineStartOffsets.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >>> 1;
      if (lineStartOffsets[mid] <= offset) {
        lo = mid;
      } else {
        hi = mid - 1;
      }
    }
    return lo + 1;
  }

  const results: Clarification[] = [];
  const re = new RegExp(MARKER_PATTERN.source, MARKER_PATTERN.flags);
  let match: RegExpExecArray | null;
  while ((match = re.exec(normalized)) !== null) {
    const [, id, rawQuestion] = match;
    results.push({
      id,
      question: rawQuestion.trim(),
      line: lineForOffset(match.index),
    });
  }

  return results;
}
