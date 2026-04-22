# Getting Started with FleetOps

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Node.js 18+
- PostgreSQL 16+ (optional, can use Docker)
- Redis 7+ (optional, can use Docker)

### 1. Clone the Repository

```bash
git clone https://github.com/LunarPerovskite/FleetOps.git
cd FleetOps
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your settings
```

Required environment variables:
```env
DATABASE_URL=postgresql+asyncpg://fleetops:password@localhost:5432/fleetops
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key
```

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database
- Redis cache
- Backend API (http://localhost:8000)
- Frontend (http://localhost:3000)

### 4. Create First Admin User

```bash
cd backend
python -m app.scripts.create_admin \
  --email admin@fleetops.io \
  --password changeme \
  --name "Admin User"
```

### 5. Access FleetOps

- **Web App**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Development Setup

### Backend Only

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Only

```bash
cd frontend
npm install
npm run dev
```

## Connect Your First Agent

### 1. Get API Key

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "email=admin@fleetops.io" \
  -d "password=changeme"
```

### 2. Create Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Agent",
    "provider": "openai",
    "model": "gpt-4.1",
    "capabilities": ["coding", "analysis"],
    "level": "junior"
  }'
```

### 3. Create Task

```bash
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Analyze customer feedback",
    "description": "Process Q3 customer feedback data",
    "agent_id": "AGENT_ID_FROM_STEP_2",
    "risk_level": "medium"
  }'
```

### 4. Approve Task

```bash
curl -X POST http://localhost:8000/api/v1/tasks/TASK_ID/approve \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "approve",
    "comments": "Proceed with analysis"
  }'
```

## What's Next?

- [Connect Claude Code](docs/connectors/claude.md)
- [Set up WhatsApp](docs/connectors/whatsapp.md)
- [Configure Human Hierarchy](docs/hierarchy.md)
- [View Analytics](docs/analytics.md)

## Troubleshooting

### Database Connection Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000
# Kill process or change port in .env
```

### Redis Not Available
```bash
# Start Redis only
docker-compose up -d redis
```

## Support

- GitHub Issues: https://github.com/LunarPerovskite/FleetOps/issues
- Documentation: https://docs.fleetops.io
- Community: https://discord.gg/fleetops
