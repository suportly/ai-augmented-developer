# Checklist items: Performance

- N+1 query check on each new queryset.
- Pagination on every list endpoint; no unbounded result sets.
- Heavy work off the request cycle (async tasks, background jobs).
- Cold-start impact measured for new dependencies.
