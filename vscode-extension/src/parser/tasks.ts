/**
 * Pure parser for the task list inside a `tasks.md` file.
 *
 * Heading shape (see `templates/tasks-template.md`):
 *
 *   ### T001 — Short title
 *
 *   - **Status:** pending
 *
 * The em-dash (U+2014) between id and title is canonical; an ASCII hyphen
 * is also tolerated for forgiveness. The first `- **Status:** <value>`
 * bullet between a heading and the next `### ` heading wins.
 */

import type { Task, TaskStatus } from './types';

const HEADING_RE = /^###\s+(T\d+)\s+[—-]\s+(.+?)\s*$/;
const STATUS_BULLET_RE = /^- \*\*Status:\*\*\s*(\S+)\s*$/;
const UTF8_BOM = '﻿';

const STATUS_MAP: Record<string, TaskStatus> = {
  pending: 'pending',
  in_progress: 'in_progress',
  blocked: 'blocked',
  done: 'done',
};

function normaliseStatus(raw: string): TaskStatus {
  return STATUS_MAP[raw] ?? 'unknown';
}

export function parseTasks(source: string): Task[] {
  const normalised = source.startsWith(UTF8_BOM) ? source.slice(UTF8_BOM.length) : source;
  if (normalised.length === 0) {
    return [];
  }

  const lines = normalised.split(/\r?\n/);
  const tasks: Task[] = [];

  let current: Task | undefined;
  let statusFound = false;

  const finalise = (): void => {
    if (current !== undefined) {
      tasks.push(current);
    }
    current = undefined;
    statusFound = false;
  };

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const headingMatch = HEADING_RE.exec(line);
    if (headingMatch) {
      finalise();
      current = {
        id: headingMatch[1],
        title: headingMatch[2].trim(),
        status: 'unknown',
        line: i + 1,
      };
      statusFound = false;
      continue;
    }

    if (current !== undefined && !statusFound) {
      const statusMatch = STATUS_BULLET_RE.exec(line);
      if (statusMatch) {
        current.status = normaliseStatus(statusMatch[1]);
        statusFound = true;
      }
    }
  }

  finalise();

  return tasks;
}
