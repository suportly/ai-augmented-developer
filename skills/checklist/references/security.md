# Checklist items: Security

- Input validation at every boundary that takes user data.
- Parameterized queries; no string-concatenated SQL.
- Authentication required on every endpoint that returns user data.
- Authorization enforced per user; no cross-user leaks.
- Secrets not logged, not echoed, not in error messages.
- Dependency vulnerability scan is clean or exceptions are documented.
