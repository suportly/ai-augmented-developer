---
name: bump-version
description: Incrementar versao do app mobile (versionCode, versionName, buildNumber). Usar antes de builds de producao.
disable-model-invocation: true
allowed-tools: Read, Edit, Grep
argument-hint: "[major|minor|patch]"
---

# Bump Version

Incrementar versao do app {{APP_NAME}} para novo release.

## Arquivos que DEVEM ser atualizados (AMBOS!)

1. **`{{MOBILE_DIR}}/app.json`**:
   - `expo.version` — versionName (ex: "1.0.50" -> "1.0.51")
   - `expo.android.versionCode` — numero incremental (ex: 162 -> 163)
   - `expo.ios.buildNumber` — auto-incrementado pelo EAS, mas pode ser manual

2. **`{{MOBILE_DIR}}/android/app/build.gradle`**:
   - `versionCode` — DEVE ser igual ao `app.json`
   - `versionName` — DEVE ser igual ao `app.json`

## Logica de bump

- **patch** (default): `1.0.50` -> `1.0.51`
- **minor**: `1.0.50` -> `1.1.0`
- **major**: `1.0.50` -> `2.0.0`

O `versionCode` SEMPRE incrementa em 1, independente do tipo de bump.

## Passos

1. Ler versoes atuais de `app.json` e `build.gradle`
2. Calcular nova versao baseado no argumento (`$ARGUMENTS` ou `patch` por default)
3. Atualizar ambos os arquivos
4. Mostrar resumo: versao anterior -> nova versao

## CRITICO
- Se `versionCode` divergir entre `app.json` e `build.gradle`, o `build.gradle` tem precedencia (pasta `android/` existe)
- Google Play rejeita `versionCode` ja usado — SEMPRE incrementar
