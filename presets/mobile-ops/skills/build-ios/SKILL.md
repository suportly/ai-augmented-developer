---
name: build-ios
description: Build iOS na nuvem do EAS para TestFlight/App Store. Usar quando precisar gerar build iOS para producao.
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Grep
argument-hint: "[--skip-bump]"
---

# Build iOS (EAS Cloud)

Gerar build iOS na nuvem do EAS (nao precisa de Mac local).

## Passos

1. **Verificar versoes** — Ler `app.json`, garantir `version` e `buildNumber` corretos
2. **Bump version** se necessario (a menos que `$ARGUMENTS` contenha `--skip-bump`):
   - Incrementar `version` em `app.json` se for novo release
   - `buildNumber` eh auto-incrementado pelo EAS (`autoIncrement: true` no eas.json)
3. **Executar build na nuvem**:
   ```bash
   cd {{MOBILE_DIR}} && eas build --platform ios --profile production --non-interactive
   ```
   - Rodar em background (build leva ~15-20 min na nuvem)
4. **Verificar status**:
   ```bash
   eas build:list --platform ios --limit 1
   ```
5. **Reportar resultado** — Informar status do build e sugerir proximo passo

## Proximos passos apos build
- Submit para TestFlight: `eas submit --platform ios --latest --non-interactive`
- Verificar no App Store Connect: https://appstoreconnect.apple.com/apps/6757546111/testflight/ios

## Credenciais iOS (ja configuradas em eas.json)
- Apple Team ID: `RXT9Q43769`
- App Store Connect App ID: `6757546111`
- ASC API Key: `./docs/AuthKey_W4CVHV2LMF.p8`
