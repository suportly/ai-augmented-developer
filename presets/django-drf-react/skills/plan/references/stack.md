# Stack conventions to check/apply in the plan (django-drf-react)

For Django backend:
- [ ] Model → Serializer → Service → View → URL order followed
- [ ] `transaction.on_commit()` used for Celery task dispatch
- [ ] UserManager used for user-scoped models
- [ ] `EncryptedTextField` for sensitive data

For React frontend:
- [ ] TypeScript types defined before components
- [ ] TanStack Query hooks before components
- [ ] No `useState` for server data
