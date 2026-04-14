---
name: submit-ios
description: Enviar build iOS mais recente para TestFlight/App Store Connect. Usar apos build iOS finalizado.
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Submit iOS para TestFlight

Enviar o build iOS mais recente do EAS para o App Store Connect (TestFlight).

## Passos

1. **Verificar ultimo build**:
   ```bash
   cd {{MOBILE_DIR}} && eas build:list --platform ios --limit 1
   ```
   - Confirmar que status eh `FINISHED`

2. **Submeter para TestFlight**:
   ```bash
   cd {{MOBILE_DIR}} && eas submit --platform ios --latest --non-interactive
   ```

3. **Verificar status do submit**:
   ```bash
   eas submit:list --platform ios --limit 1
   ```

4. **Reportar resultado** e informar link do TestFlight:
   - https://appstoreconnect.apple.com/apps/6757546111/testflight/ios

## Credenciais (ja em eas.json)
- Apple Team ID: `RXT9Q43769`
- ASC API Key: `./docs/AuthKey_W4CVHV2LMF.p8`
- App Store Connect App ID: `6757546111`
