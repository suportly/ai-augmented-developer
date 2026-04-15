---
description: Baseline security rules — inputs, secrets, auth, logging, dependencies.
alwaysApply: true
---

# Security

Minimum bar for every change. Stack-specific presets may tighten these
with framework-level rules (CSRF, CSP, ORM scoping, etc.).

## Inputs

- Never trust client input. Validate at every boundary (HTTP handler,
  message consumer, CLI arg).
- Use the framework's serializer/validator; do not roll your own regex
  for emails, URLs, UUIDs.
- Parameterised queries only. String-concatenated SQL is a bug even
  when it "looks safe".
- HTML-escape every user-supplied string that renders into a template.
  `{{ user.bio }}` must escape by default; `|safe` requires a code
  review.

## Authentication & authorization

- Auth happens at a single chokepoint (middleware, decorator). No
  per-view ad-hoc checks.
- Authorization is explicit: a missing `queryset.filter(user=self.user)`
  is an IDOR. Scope every list endpoint.
- Never compare secrets with `==`. Use `hmac.compare_digest` /
  `crypto.timingSafeEqual`.

## Secrets

- Never commit secrets. Not even "temporarily", not even in
  `.env.example`, not in comments.
- Read secrets from the environment, a secret manager, or an encrypted
  vault. Treat the values as tainted: do not log them, do not include
  them in error messages.
- Rotate any secret that lands in git history. Reverting the commit is
  not enough.

## Logging & errors

- Log what happened and why. Do not log who it happened to if that
  who is personally identifiable without redaction.
- Stack traces go to observability tooling, never to the user. A user
  sees "something went wrong" + a request id; the id is the bridge.
- Structured logs (JSON or key=value). `print` is for debugging your
  laptop, never production.

## Dependencies

- Prefer the project's chosen library. Do not add a new dependency for
  a ten-line utility.
- Pin versions. Floating deps mean reproducibility goes away.
- Review each added dep: license, maintenance status, transitive
  footprint. `npm install some-regex-helper` can pull in 200 packages.

## Forbidden

- Disabling TLS verification in production code paths.
- Runtime code evaluation of untrusted strings (Python `eval`/`exec`,
  JS dynamic function constructors, shell-out with unsanitised input).
- `--no-verify`, `--skip-hooks`, `git push --force` on shared branches.
- Copy-pasting credentials into chat, PRs, or logs.
