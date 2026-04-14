---
name: submit-android
description: Enviar build Android AAB para Google Play Console. Usar apos build Android finalizado.
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Submit Android para Google Play

Enviar o build Android AAB mais recente para o Google Play Console.

## Passos

1. **Verificar ultimo AAB gerado**:
   ```bash
   ls -lt {{MOBILE_DIR}}/build-*.aab | head -1
   ```

2. **Submeter via EAS**:
   ```bash
   cd {{MOBILE_DIR}} && eas submit --platform android --latest
   ```
   - Se nao funcionar, upload manual no Google Play Console

3. **Reportar resultado** com detalhes do arquivo enviado

## Upload manual (alternativa)
Se `eas submit` falhar, fazer upload manual:
1. Abrir Google Play Console
2. Ir em "Producao" > "Criar nova versao"
3. Upload do arquivo `.aab`
4. Preencher release notes
5. Publicar
