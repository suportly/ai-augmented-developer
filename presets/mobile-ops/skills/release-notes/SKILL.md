---
name: release-notes
description: Gerar release notes para App Store e Google Play baseado nos commits recentes. Usar ao submeter nova versao para review.
disable-model-invocation: true
allowed-tools: Bash, Read
argument-hint: "[versao]"
---

# Release Notes Generator

Gerar release notes bilingues (PT-BR + EN) para App Store Connect e Google Play Console.

## Passos

1. **Identificar versao**:
   - Se `$ARGUMENTS` informado, usar como versao
   - Senao, ler de `{{MOBILE_DIR}}/app.json` → `expo.version`

2. **Coletar mudancas** — Ler commits desde o ultimo tag/release:
   ```bash
   cd {{MOBILE_DIR}} && git log --oneline --no-merges HEAD~20..HEAD
   ```

3. **Gerar release notes** em dois idiomas:

   ### Formato App Store (max 4000 chars)
   ```
   **Portugues (pt-BR):**
   O que ha de novo na versao X.Y.Z:
   - [mudanca 1]
   - [mudanca 2]
   ...

   **English (en):**
   What's New in Version X.Y.Z:
   - [change 1]
   - [change 2]
   ...
   ```

4. **Regras**:
   - Linguagem voltada ao usuario (nao tecnica)
   - Foco em beneficios, nao implementacao
   - Maximo 5-7 bullet points
   - Commits internos (refactor, chore, ci) NAO aparecem
   - Bug fixes agrupados em "Correcoes de estabilidade"
   - Features novas primeiro, melhorias depois, fixes por ultimo
