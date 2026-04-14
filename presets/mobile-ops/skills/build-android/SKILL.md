---
name: build-android
description: Build local Android AAB para Google Play. Usar quando precisar gerar build Android para producao.
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Grep
argument-hint: "[--skip-bump]"
---

# Build Android AAB Local

Gerar build AAB para upload no Google Play Console.

## Passos

1. **Verificar versoes** — Ler `app.json` e `android/app/build.gradle`, garantir que `versionCode` e `versionName` estejam sincronizados
2. **Bump version** se necessario (a menos que `$ARGUMENTS` contenha `--skip-bump`):
   - Incrementar `versionCode` em AMBOS `app.json` e `android/app/build.gradle`
   - Manter `versionName`/`version` sincronizados
3. **Executar build**:
   ```bash
   cd {{MOBILE_DIR}} && eas build --platform android --profile production --local
   ```
   - Timeout: 10 minutos (build pesado)
   - Rodar em background e notificar quando terminar
4. **Reportar resultado** — Informar caminho do arquivo `.aab` gerado e tamanho
5. **Proximo passo** — Sugerir `eas submit --platform android --latest` para upload

## Notas
- O `eas build` pode auto-incrementar versionCode — verificar no output
- Se build falhar com OOM/timeout do Gradle Worker, eh problema de carga da maquina — retry
- Arquivo gerado em `{{MOBILE_DIR}}/build-*.aab`
