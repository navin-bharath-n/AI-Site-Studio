# AI Site Studio

> **AI-powered Website Template Marketplace** — Browse, preview with your own business info, customize via AI, purchase, and deploy professional website templates.

[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=nextdotjs)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org/)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Shadcn UI, Framer Motion |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic, Celery |
| Database | PostgreSQL (Supabase) |
| Cache | Redis |
| Auth | Clerk |
| Storage | Cloudflare R2 |
| AI | OpenAI GPT-4o, Embeddings, GPT Image |
| Vector DB | Qdrant |
| Payments | Razorpay + Stripe |
| Deploy | Vercel (frontend) + Railway/Docker (backend) |

---

## Project Structure

```
ai-site-studio/
├── frontend/          # Next.js 15 App Router
├── backend/           # FastAPI Python API
├── docker-compose.yml # Local dev (Postgres + Redis)
└── README.md
```

## Quick Start (Local Development)

### Prerequisites
- Node.js 20+
- Python 3.12+
- Docker & Docker Compose

### 1. Clone & Configure

```bash
git clone <repo-url>
cd ai-site-studio

# Backend env
cp backend/.env.example backend/.env
# Fill in your keys in backend/.env

# Frontend env
cp frontend/.env.example frontend/.env.local
# Fill in your keys in frontend/.env.local
```

### 2. Start Infrastructure

```bash
docker-compose up -d   # Starts Postgres 16 + Redis 7
```

### 3. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed database (100 templates)
python scripts/seed.py

# Start API
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT signing secret |
| `CLERK_SECRET_KEY` | Clerk backend secret |
| `CLERK_WEBHOOK_SECRET` | Clerk webhook signing secret |
| `OPENAI_API_KEY` | OpenAI API key |
| `QDRANT_URL` | Qdrant instance URL |
| `QDRANT_API_KEY` | Qdrant API key |
| `R2_ACCOUNT_ID` | Cloudflare R2 account ID |
| `R2_ACCESS_KEY_ID` | R2 access key |
| `R2_SECRET_ACCESS_KEY` | R2 secret key |
| `R2_BUCKET_NAME` | R2 bucket name |
| `RAZORPAY_KEY_ID` | Razorpay key ID |
| `RAZORPAY_KEY_SECRET` | Razorpay secret |
| `STRIPE_SECRET_KEY` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key |
| `CLERK_SECRET_KEY` | Clerk secret key |
| `NEXT_PUBLIC_API_URL` | Backend API URL |
| `NEXT_PUBLIC_SITE_URL` | Frontend site URL |

---

## API Documentation

Start the backend and visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## License

MIT © AI Site Studio
