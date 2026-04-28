/**
 * Pure parser for the bold-key header block of a `spec.md` file.
 *
 * Header shape (see `templates/spec-template.md`):
 *
 *   # Feature specification: <title>
 *
 *   **Branch:** `feature/foo`
 *   **Created:** 2026-04-28
 *   **Status:** Draft
 *   **Spec ID:** 0012
 *   **Language:** en
 *
 *   ---
 *
 * Only the metadata block before the first horizontal rule (`---`) is
 * consumed; downstream sections are out of scope for this task.
 */

import type { SpecStatus } from './types';

export interface SpecHeaderFields {
  title: string | undefined;
  branch: string | undefined;
  language: string | undefined;
  specId: string | undefined;
  status: SpecStatus;
  parseError?: string;
}

const TITLE_PREFIX = '# Feature specification:';
const BOLD_KEY_RE = /^\*\*([^*]+):\*\*\s*(.+?)\s*$/;

const STATUS_MAP: Record<string, SpecStatus> = {
  draft: 'draft',
  'in review': 'in review',
  approved: 'approved',
  implemented: 'implemented',
  'pr open': 'pr open',
};

function stripBackticks(value: string): string {
  if (value.length >= 2 && value.startsWith('`') && value.endsWith('`')) {
    return value.slice(1, -1);
  }
  return value;
}

function normaliseStatus(raw: string): {
  status: SpecStatus;
  parseError?: string;
} {
  const key = raw.trim().toLowerCase();
  const mapped = STATUS_MAP[key];
  if (mapped !== undefined) {
    return { status: mapped };
  }
  return {
    status: 'unknown',
    parseError: `Unrecognised Status value: "${raw}"`,
  };
}

export function parseSpec(source: string): SpecHeaderFields {
  const lines = source.split('\n');

  let title: string | undefined;
  let branch: string | undefined;
  let language: string | undefined;
  let specId: string | undefined;
  let status: SpecStatus = 'unknown';
  let parseError: string | undefined;

  for (const rawLine of lines) {
    const line = rawLine;

    if (title === undefined && line.startsWith(TITLE_PREFIX)) {
      title = line.slice(TITLE_PREFIX.length).trim() || undefined;
      continue;
    }

    if (line.trim() === '---') {
      break;
    }

    const match = BOLD_KEY_RE.exec(line);
    if (!match) {
      continue;
    }

    const key = match[1].trim().toLowerCase();
    const value = stripBackticks(match[2].trim());

    switch (key) {
      case 'branch':
        branch = value;
        break;
      case 'language':
        language = value;
        break;
      case 'spec id':
        specId = value;
        break;
      case 'status': {
        const result = normaliseStatus(value);
        status = result.status;
        if (result.parseError !== undefined) {
          parseError = result.parseError;
        }
        break;
      }
      default:
        break;
    }
  }

  const result: SpecHeaderFields = {
    title,
    branch,
    language,
    specId,
    status,
  };
  if (parseError !== undefined) {
    result.parseError = parseError;
  }
  return result;
}
