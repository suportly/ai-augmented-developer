---
name: ota-update
description: Publicar OTA update via EAS Update para o canal de producao. Usar para mudancas JS-only que nao precisam de build nativo.
disable-model-invocation: true
allowed-tools: Bash, Read
argument-hint: "[--message 'descricao']"
---

# OTA Update (EAS Update)

Publicar atualizacao over-the-air para o canal de producao. Funciona apenas para mudancas em JavaScript/TypeScript — mudancas nativas (novas libs, AndroidManifest, Info.plist) exigem build completo.

## Passos

1. **Verificar se a mudanca eh JS-only**:
   - Se envolve `package.json`, `android/`, `ios/`, nova dependencia nativa → precisa de build completo, NAO OTA
   - Se eh apenas codigo TS/JS, assets, ou configuracao → OTA funciona

2. **Publicar update**:
   ```bash
   cd {{MOBILE_DIR}} && eas update --branch production --message "$ARGUMENTS"
   ```
   - Se nao houver `--message` nos argumentos, pedir ao usuario uma descricao curta

3. **Verificar publicacao**:
   ```bash
   eas update:list --branch production --limit 1
   ```

4. **Reportar resultado**

## Requisitos
- O build em producao deve ter `channel: "production"` configurado no `eas.json`
- O app no dispositivo deve estar conectado ao canal (builds a partir de v1.0.50 ja tem)
- OTA update eh aplicado na proxima abertura do app

## Quando NAO usar OTA
- Nova dependencia nativa instalada
- Mudancas em `app.json` que afetam config nativa
- Mudancas em `android/` ou `ios/`
- Atualizacao de SDK do Expo
