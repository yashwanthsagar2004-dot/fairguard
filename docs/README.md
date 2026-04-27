# FairGuard

Open-source fairness auditing platform for AI decision systems.

## Structure
- `/frontend`: Next.js 14 Web Application
- `/backend`: FastAPI Service
- `/shared`: Shared schemas
- `/infra`: Deployment configurations
- `/docs`: Documentation

## Running Locally

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Regulatory Alignment
FairGuard aligns with:
- EU AI Act (Article 9 & 15)
- NYC Local Law 144
- Colorado SB21-169
