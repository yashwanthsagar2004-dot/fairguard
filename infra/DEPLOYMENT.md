# Infra

## Dockerfile (Backend)
```dockerfile
FROM python:3.11-slim
RUN groupadd -r fairguard && useradd -r -g fairguard fairguard
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY shared/ ../shared/
USER fairguard
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Vercel (Frontend)
- **Framework**: Vite
- **Root Directory**: `frontend/`
- **Output Directory**: `dist/`
- **Rewrites**: Point to the Cloud Run backend URL via environment variables.

## Cloud Run (Backend)
(Existing configuration for Python backend)
```yaml
# ... (same as before)
```

## Terraform
(Summary of provided module)
- BigQuery Dataset
- Pub/Sub: `fairguard-decisions`
- Cloud SQL: `db-f1-micro` (PostgreSQL)
- Cloud Storage: `fairguard-artifacts`
- KMS: `certificate-signer` key
