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

## Cloud Run (asia-south1)
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: fairguard-backend
  labels:
    cloud.googleapis.com/location: asia-south1
spec:
  template:
    spec:
      containers:
      - image: gcr.io/fairguard/backend
        resources:
          limits:
            cpu: 2000m
            memory: 4Gi
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-api-key
              key: latest
```

## Terraform
(Summary of provided module)
- BigQuery Dataset
- Pub/Sub: `fairguard-decisions`
- Cloud SQL: `db-f1-micro` (PostgreSQL)
- Cloud Storage: `fairguard-artifacts`
- KMS: `certificate-signer` key
