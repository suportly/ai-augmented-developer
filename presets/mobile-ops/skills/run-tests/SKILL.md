---
name: run-tests
description: Executar testes do projeto. Usar apos modificar codigo para verificar regressoes.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep
argument-hint: "[mobile|backend|admin] [--file path]"
---

# Run Tests

Executar testes do projeto StiveX.

## Uso

- `/run-tests` — Roda testes mobile (default)
- `/run-tests mobile` — Testes RNTL do {{MOBILE_DIR}}
- `/run-tests backend` — Testes Django do {{BACKEND_DIR}}
- `/run-tests admin` — Testes do {{ADMIN_DIR}}
- `/run-tests mobile --file path/to/test` — Teste especifico

## Comandos por plataforma

### Mobile (RNTL)
```bash
cd {{MOBILE_DIR}} && npx jest --no-coverage
# Teste especifico:
cd {{MOBILE_DIR}} && npx jest --no-coverage path/to/test
```

### Backend (Django)
```bash
cd {{BACKEND_DIR}} && source venv/bin/activate && python manage.py test
# App especifica:
cd {{BACKEND_DIR}} && source venv/bin/activate && python manage.py test accounts
```

### Admin (Vite)
```bash
cd {{ADMIN_DIR}} && npm run lint
```

## Passos

1. Identificar qual plataforma testar baseado em `$ARGUMENTS` (default: mobile)
2. Rodar os testes
3. Analisar output:
   - Se tudo passou: reportar sucesso com contagem
   - Se falhou: listar testes que falharam e analisar se sao pre-existentes ou novos
4. Para falhas novas: sugerir fix

## Testes pre-existentes com falha conhecida
- `GroupListScreen.test.tsx` — Falha intermitente conhecida
- `DashboardScreen.stale.test.tsx` — Timeout intermitente
