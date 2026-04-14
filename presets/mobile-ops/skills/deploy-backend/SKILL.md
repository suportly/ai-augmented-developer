---
name: deploy-backend
description: Deploy do backend Django para Cloud Run (GCP). Usar quando precisar publicar mudancas da API em producao.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep
---

# Deploy Backend (Cloud Run)

Deploy do {{BACKEND_DIR}} para o Cloud Run na GCP.

## Pre-requisitos
- Docker rodando localmente
- `gcloud` autenticado (`gcloud auth login`)
- Credenciais de Docker configuradas (`gcloud auth configure-docker {{GCP_REGION}}-docker.pkg.dev`)

## Passos

1. **Verificar mudancas pendentes**:
   ```bash
   cd {{BACKEND_DIR}} && git status
   ```
   - Se houver mudancas nao commitadas, avisar o usuario

2. **Verificar se ha migrations pendentes**:
   ```bash
   cd {{BACKEND_DIR}} && source venv/bin/activate && python manage.py showmigrations | grep "\[ \]"
   ```
   - Se houver migrations nao aplicadas, avisar (precisam ser aplicadas no Cloud SQL tambem)

3. **Build da imagem Docker**:
   ```bash
   cd {{BACKEND_DIR}}
   IMAGE="{{GCP_REGION}}-docker.pkg.dev/{{GCP_PROJECT}}/{{ARTIFACT_REPO}}/{{BACKEND_SERVICE}}:latest"
   docker build -f Dockerfile.cloudrun -t $IMAGE .
   ```

4. **Push para Artifact Registry**:
   ```bash
   docker push $IMAGE
   ```

5. **Deploy no Cloud Run**:
   ```bash
   gcloud run deploy {{BACKEND_SERVICE}} \
     --image $IMAGE \
     --region {{GCP_REGION}} \
     --platform managed \
     --allow-unauthenticated \
     --min-instances 1 \
     --max-instances 10 \
     --memory 1Gi \
     --cpu 1 \
     --timeout 3600 \
     --concurrency 80 \
     --no-cpu-throttling
   ```

6. **Verificar deploy**:
   ```bash
   gcloud run services describe {{BACKEND_SERVICE}} --region {{GCP_REGION}} --format="value(status.url)"
   ```

## CRITICO
- **SEMPRE usar `--memory 1Gi`** — 512Mi causa OOM em producao
- URL de producao: `https://{{PROD_API_URL}}`
- Cloud SQL: `{{GCP_PROJECT}}:us-central1:{{CLOUD_SQL_INSTANCE}}`
