---
name: start-dev
description: Iniciar ambiente de desenvolvimento completo (backend + mobile). Usar quando quiser subir os servicos para desenvolvimento.
disable-model-invocation: true
allowed-tools: Bash, Read
argument-hint: "[backend|mobile|all]"
---

# Start Dev Environment

Iniciar servicos de desenvolvimento do StiveX.

## Uso

- `/start-dev` ou `/start-dev all` — Inicia backend + mobile
- `/start-dev backend` — Apenas backend (Daphne + auto-reload)
- `/start-dev mobile` — Apenas Expo dev server

## Comandos

### Backend (com auto-reload via watchfiles)
```bash
cd {{BACKEND_DIR}} && source venv/bin/activate

# Verificar se ja esta rodando
lsof -ti:8003 && echo "Backend ja rodando na porta 8003" || watchfiles 'daphne -b 0.0.0.0 -p 8003 {{BACKEND_ASGI_MODULE}}:application' .
```

### Mobile (Expo)
```bash
cd {{MOBILE_DIR}} && npm start
```

### Servicos extras (push notifications)
```bash
# Redis (necessario para Celery)
docker run -d --name redis -p 6379:6379 redis:alpine 2>/dev/null || docker start redis

# Celery Worker (push notifications)
cd {{BACKEND_DIR}} && source venv/bin/activate && celery -A {{CELERY_APP}} worker -l info

# Celery Beat (notificacoes agendadas - opcional)
cd {{BACKEND_DIR}} && source venv/bin/activate && celery -A {{CELERY_APP}} beat -l info
```

## Portas
- Backend: `http://0.0.0.0:8003`
- Mobile: `http://localhost:8082`
- Admin: `http://localhost:5174`
- Redis: `localhost:6379`

## Passos
1. Verificar qual servico iniciar baseado em `$ARGUMENTS`
2. Verificar se portas ja estao em uso
3. Iniciar servicos em background
4. Reportar URLs de acesso
