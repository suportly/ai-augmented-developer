---
name: deploy-admin
description: Deploy do admin dashboard React para Cloud Run (GCP). Usar quando precisar publicar mudancas do {{ADMIN_DIR}} em producao.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep
---

# Deploy Admin Dashboard (Cloud Run)

Deploy do {{ADMIN_DIR}} para o Cloud Run na GCP.

## Passos

1. **Verificar mudancas pendentes**:
   ```bash
   cd {{ADMIN_DIR}} && git status
   ```

2. **Build da imagem Docker**:
   ```bash
   cd {{ADMIN_DIR}}
   IMAGE="{{GCP_REGION}}-docker.pkg.dev/{{GCP_PROJECT}}/{{ARTIFACT_REPO}}/{{ADMIN_SERVICE}}:latest"
   docker build -t $IMAGE .
   ```

3. **Push para Artifact Registry**:
   ```bash
   docker push $IMAGE
   ```

4. **Deploy no Cloud Run**:
   ```bash
   gcloud run deploy {{ADMIN_SERVICE}} \
     --image $IMAGE \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated \
     --min-instances 1 \
     --max-instances 5 \
     --memory 256Mi \
     --cpu 1 \
     --timeout 300 \
     --concurrency 80 \
     --no-cpu-throttling
   ```

5. **Verificar deploy**:
   ```bash
   gcloud run services describe {{ADMIN_SERVICE}} --region us-central1 --format="value(status.url)"
   ```

## Info
- URL: `https://{{ADMIN_SERVICE}}-1085114214798.us-central1.run.app`
- Regiao: `us-central1` (Iowa)
