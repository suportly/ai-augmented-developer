---
description: REST/HTTP API conventions — URLs, payloads, error shapes, status codes.
alwaysApply: true
---

# API conventions

## URLs

- Nouns, plural, lowercase, hyphenated: `/api/v1/user-orders/`.
- Hierarchy reflects ownership: `/api/v1/users/42/orders/` beats
  `/api/v1/orders?userId=42` when orders always belong to a user.
- Version in the path (`/api/v1/...`), not in a header.
- No verbs in URLs. Actions are HTTP methods. When an action does not
  fit CRUD, model it as a sub-resource: `POST /api/v1/orders/42/cancellation`,
  not `POST /api/v1/orders/42/cancel`.

## HTTP methods

| Method | Use |
|--------|-----|
| GET    | Read. Never mutates. Safe to cache. |
| POST   | Create, or a non-idempotent action. |
| PUT    | Replace the entire resource. Idempotent. |
| PATCH  | Partial update. Idempotent when given the same payload. |
| DELETE | Remove. Idempotent: 204 if deleted, 204 if already gone. |

## Status codes

- 200 OK — success with body.
- 201 Created — after POST; `Location` header points at the new resource.
- 204 No Content — success without body (DELETE, idle PATCH).
- 400 Bad Request — validation error. Payload carries the field errors.
- 401 Unauthorized — no or bad credentials.
- 403 Forbidden — authenticated but not allowed.
- 404 Not Found — resource does not exist or the user cannot see it.
- 409 Conflict — version mismatch or duplicate-key violation.
- 422 Unprocessable Entity — only when the framework demands it over 400.
- 500 Internal Server Error — real bug, always logged.

Never return 200 with `"error": ...` in the body. The status code is
the first-class signal.

## Error shape

Every 4xx/5xx response has the same envelope:

```json
{
  "error": {
    "code": "validation_failed",
    "message": "Human-readable summary.",
    "details": [
      {"field": "email", "issue": "already_in_use"}
    ]
  }
}
```

- `code` is a stable string the client can switch on.
- `message` is for logs and debug surfaces, not for end-user UI.
- `details` is optional and only present for per-field problems.

## Pagination

- Cursor-based for any list that can grow unbounded. Offset/limit is
  acceptable only for fixed, small lists (dropdowns, enums).
- Response shape:

```json
{
  "results": [...],
  "next_cursor": "opaque-string-or-null",
  "total": 42
}
```

## Forbidden

- Mixing snake_case and camelCase in the same payload. Pick one
  convention per API and stick to it.
- Returning HTML from a JSON endpoint. Ever.
- Swallowing exceptions into a 200. If the server failed, say so.
