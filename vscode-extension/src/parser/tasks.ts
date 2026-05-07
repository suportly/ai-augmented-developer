/**
 * Pure parser for the task list inside a `tasks.md` file.
 *
 * Recognises three task declarations:
 *
 *   1. Canonical heading with status bullet (templates/tasks-template.md).
 *      Any heading level from H3 to H6 is accepted, so authors may group
 *      tasks under a `### Phase N` header and demote tasks to `####`:
 *
 *        ### T001 — Title
 *        #### T001 — Title           (under a `### Phase` group)
 *        - **Status:** pending
 *
 *   2. Loose heading (no separator); status defaults to `unknown` and may
 *      be updated by a status bullet or a table row (#4):
 *
 *        ### T001 Title
 *        ##### T001 Title
 *
 *   3. GitHub task-list checkbox:
 *
 *        - [x] T001 Title              -> done
 *        - [ ] T002 [P] Title          -> pending
 *        - [x] **T003** Title          -> done
 *        - [x] ~~**T004**~~ Title      -> done (strikethrough tolerated)
 *
 *   4. Status table row (overrides current status of an existing task):
 *
 *        | T001 | commit | done    |   -> via word
 *        | T002 |        | pending |
 *        | T003 |        | (✅/🚧/⛔/⏳ emoji also accepted)
 */

import type { Task, TaskStatus } from './types';

const HEADING_RE = /^#{3,6}\s+(T\d+)(?:\s*[—-])?\s+(.+?)\s*$/;
// Tolerant of bold around the label and/or value, and of trailing prose
// after the status word (e.g. `- Status: **done** (commit abc1234)`).
// Accepts `- **Status:** done`, `- Status: done`, `- **Status**: done`,
// `- Status: **done** (commit X)`, etc.
const STATUS_BULLET_RE = /^-\s+\*{0,2}Status:?\*{0,2}:?\s*\*{0,2}([A-Za-z_-]+)\*{0,2}/i;
const CHECKBOX_RE =
  /^-\s+\[([ xX])\]\s+(?:~~)?(?:\*\*)?(T\d+)(?:\*\*)?(?:~~)?\s*(.*?)\s*$/;
const TABLE_STATUS_RE =
  /^\|\s*(?:\*\*)?(T\d+)(?:\*\*)?\s*\|.*?\|\s*([^|]*?)\s*\|?\s*$/;
// Strips `[P]`, `[US1]` and other leading bracket tags from task titles.
// See `templates/tasks-template.md` for the canonical tag conventions.
const LEADING_TAG_RE = /^(?:\[[^\]]+\]\s*)+/;
const SURROUND_BOLD_RE = /^\*\*(.+)\*\*$/;
const UTF8_BOM = '﻿';

const STATUS_MAP: Record<string, TaskStatus> = {
  pending: 'pending',
  todo: 'pending',
  in_progress: 'in_progress',
  'in-progress': 'in_progress',
  wip: 'in_progress',
  blocked: 'blocked',
  done: 'done',
  completed: 'done',
  complete: 'done',
  finished: 'done',
};

const EMOJI_STATUS_MAP: Record<string, TaskStatus> = {
  '✅': 'done',
  '✔': 'done',
  '☑': 'done',
  '🚧': 'in_progress',
  '🔄': 'in_progress',
  '⛔': 'blocked',
  '🚫': 'blocked',
  '⏳': 'pending',
  '⬜': 'pending',
};

function normaliseStatus(raw: string): TaskStatus {
  return STATUS_MAP[raw.toLowerCase()] ?? 'unknown';
}

function statusFromCell(cell: string): TaskStatus | undefined {
  const stripped = cell.replace(/[*~`]/g, '').trim().toLowerCase();
  if (STATUS_MAP[stripped]) {
    return STATUS_MAP[stripped];
  }
  for (const ch of cell) {
    if (EMOJI_STATUS_MAP[ch]) {
      return EMOJI_STATUS_MAP[ch];
    }
  }
  return undefined;
}

function cleanTitle(raw: string): string {
  let title = raw.trim();
  title = title.replace(LEADING_TAG_RE, '').trim();
  const bold = SURROUND_BOLD_RE.exec(title);
  if (bold) {
    title = bold[1].trim();
  }
  return title;
}

export function parseTasks(source: string): Task[] {
  const normalised = source.startsWith(UTF8_BOM) ? source.slice(UTF8_BOM.length) : source;
  if (normalised.length === 0) {
    return [];
  }

  const lines = normalised.split(/\r?\n/);
  const tasks: Task[] = [];
  const byId = new Map<string, Task>();
  const deferredTableStatus = new Map<string, TaskStatus>();

  let current: Task | undefined;
  let statusFound = false;

  const finalise = (): void => {
    if (current !== undefined && !byId.has(current.id)) {
      tasks.push(current);
      byId.set(current.id, current);
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
        title: cleanTitle(headingMatch[2]),
        status: 'unknown',
        line: i + 1,
      };
      statusFound = false;
      continue;
    }

    const checkboxMatch = CHECKBOX_RE.exec(line);
    if (checkboxMatch) {
      finalise();
      const id = checkboxMatch[2];
      if (!byId.has(id)) {
        const checked = checkboxMatch[1].toLowerCase() === 'x';
        const task: Task = {
          id,
          title: cleanTitle(checkboxMatch[3] || ''),
          status: checked ? 'done' : 'pending',
          line: i + 1,
        };
        tasks.push(task);
        byId.set(id, task);
      }
      continue;
    }

    if (current !== undefined && !statusFound) {
      const statusMatch = STATUS_BULLET_RE.exec(line);
      if (statusMatch) {
        current.status = normaliseStatus(statusMatch[1]);
        statusFound = true;
        continue;
      }
    }

    const tableMatch = TABLE_STATUS_RE.exec(line);
    if (tableMatch) {
      const id = tableMatch[1];
      const cellStatus = statusFromCell(tableMatch[2]);
      if (cellStatus) {
        const target = byId.get(id) ?? (current?.id === id ? current : undefined);
        if (target) {
          target.status = cellStatus;
        } else {
          deferredTableStatus.set(id, cellStatus);
        }
      }
    }
  }

  finalise();

  for (const [id, status] of deferredTableStatus) {
    const target = byId.get(id);
    if (target && target.status === 'unknown') {
      target.status = status;
    }
  }

  return tasks;
}
