# FleetOps Deployment Guide

## What We Built

FleetOps is a complete open-source governance platform with:
- **22 frontend pages** (React + TypeScript + Tailwind)
- **24 API routes** (FastAPI)
- **18 backend services**
- **11 provider adapters**
- **6 test suites**
- Full documentation

## Project Structure

```
fleetops/
├── frontend/              # React SPA
│   ├── src/
│   │   ├── pages/         # 22 pages
│   │   ├── components/    # 9 components
│   │   ├── hooks/         # 9 hooks
│   │   └── lib/api.ts     # API client
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/               # FastAPI
│   ├── app/
│   │   ├── main.py        # Entry point
│   │   ├── api/routes/    # 24 routes
│   │   ├── services/      # 18 services
│   │   ├── adapters/      # 11 adapters
│   │   └── models/        # DB models
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic/           # Migrations
├── docs/                  # 3 documentation files
├── scripts/               # Utility scripts
├── docker-compose.yml     # Dev setup
└── docker-compose.prod.yml # Production
```

## Where Code Should Live

### 1. Backend (Python/FastAPI)
```
backend/app/
├── main.py              # DO NOT MODIFY - Entry point
├── core/                # Config, auth, database, security
│   ├── config.py        # Environment variables
│   ├── database.py      # DB connection
│   ├── auth.py          # JWT, password hashing
│   └── security.py      # CSP, XSS, CSRF headers
├── api/routes/          # ADD NEW ROUTES HERE
│   ├── auth.py          # Auth endpoints
│   ├── tasks.py         # Task CRUD
│   └── ...              # 24 total
├── services/            # ADD NEW SERVICES HERE
│   ├── task_service.py  # Task logic
│   └── ...              # 18 total
├── adapters/            # ADD NEW ADAPTERS HERE
│   ├── slack_bot_adapter.py
│   └── ...              # 11 total
└── models/models.py     # SQLAlchemy models
```

### 2. Frontend (React/TypeScript)
```
frontend/src/
├── pages/               # ADD NEW PAGES HERE
│   ├── Dashboard.tsx
│   ├── Tasks.tsx
│   └── ...              # 22 total
├── components/          # ADD REUSABLE COMPONENTS HERE
│   ├── Sidebar.tsx      # Navigation
│   ├── Layout.tsx       # Page wrapper
│   └── ...              # 9 total
├── hooks/               # ADD CUSTOM HOOKS HERE
│   ├── useAuth.tsx      # Auth state
│   └── ...              # 9 total
├── lib/api.ts           # ADD API ENDPOINTS HERE
└── App.tsx              # ADD ROUTES HERE
```

### 3. Documentation
```
docs/
├── API_REFERENCE.md     # API docs
├── GETTING_STARTED.md   # Setup guide
└── ARCHITECTURE.md      # System design
```

### 4. Scripts
```
scripts/
├── seed_demo.py         # Demo data
├── validate_env.py      # Environment check
├── backup.sh            # Automated backups
└── deploy.sh            # Production deploy
```

## Quick Start (Docker)

```bash
# 1. Clone
git clone https://github.com/LunarPerovskite/FleetOps.git
cd FleetOps

# 2. Environment
cp .env.example .env

# 3. Validate
python scripts/validate_env.py

# 4. Start
docker-compose up -d

# 5. Access
Frontend: http://localhost:3000
Backend:  http://localhost:8000
API Docs: http://localhost:8000/docs
```

## Manual Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_demo.py  # Optional demo data
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Adding Features

### Add a New Page
1. Create `frontend/src/pages/NewPage.tsx`
2. Add route in `frontend/src/App.tsx`
3. Add link in `frontend/src/components/Sidebar.tsx`
4. Add API calls in `frontend/src/lib/api.ts`

### Add a New API Endpoint
1. Create or edit `backend/app/api/routes/feature.py`
2. Register in `backend/app/main.py`
3. Add service in `backend/app/services/`
4. Add frontend calls in `frontend/src/lib/api.ts`

### Add a New Adapter
1. Create `backend/app/adapters/new_adapter.py`
2. Use in relevant service

## Current Status

### ✅ Working
- All 22 frontend pages
- All 24 API routes
- Docker setup
- Documentation
- Tests structure

### ⚠️ Needs Setup
- Database must be initialized
- Environment variables must be set
- Frontend dependencies must be installed

### 🔮 Future (When Ready)
- Cloud hosting (currently disabled)
- Marketplace purchases
- Mobile app

## Security

- JWT authentication
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection
- CSRF protection

## Support

- GitHub Issues: https://github.com/LunarPerovskite/FleetOps/issues
- Email: juanestebanmosquera@yahoo.com

---

**Current Version**: v0.1.0-beta
**License**: MIT
**Status**: Self-hosted only, 100% free
