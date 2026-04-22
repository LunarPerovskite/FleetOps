# Getting Started with FleetOps

## Prerequisites

- Docker and Docker Compose (recommended)
- Or: Python 3.11+, Node.js 18+, PostgreSQL 16, Redis 7

## Quick Start (5 minutes)

### 1. Clone and Setup

```bash
git clone https://github.com/LunarPerovskite/FleetOps.git
cd FleetOps
cp .env.example .env
```

### 2. Configure Environment

Edit `.env`:

```env
# Required
DATABASE_URL=postgresql://fleetops:password@localhost:5432/fleetops
JWT_SECRET=your-super-secret-key-min-32-chars-long
REDIS_URL=redis://localhost:6379

# Optional
FRONTEND_URL=http://localhost:3000
API_URL=http://localhost:8000
```

### 3. Start with Docker

```bash
# Development
docker-compose up -d

# Or production
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Visit

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 5. Onboard

1. Visit `/onboarding`
2. Create your organization
3. Configure providers at `/providers`
4. Invite team members
5. Start creating tasks!

---

## Development Setup

### Backend

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

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database Setup

```bash
# Create database
createdb fleetops

# Run seed data (optional)
cd backend
python scripts/seed_demo.py
```

---

## Configuration Guide

### Authentication Providers

#### Clerk (Recommended - Easiest)

1. Sign up at https://clerk.dev
2. Create an application
3. Copy API keys to `.env`:
```env
CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
```

#### Auth0

1. Sign up at https://auth0.com
2. Create an API application
3. Configure callback URLs
4. Copy keys to `.env`

#### Self-Hosted (Advanced)

Use built-in JWT auth with PBKDF2 hashing. No external provider needed.

### Database Providers

#### Supabase (Recommended - Free Tier)

1. Create project at https://supabase.com
2. Copy connection string to `DATABASE_URL`

#### Neon (Serverless PostgreSQL)

1. Create project at https://neon.tech
2. Copy connection string

#### Local PostgreSQL

```bash
# Install PostgreSQL
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Start service
sudo service postgresql start  # Linux
brew services start postgresql  # macOS

# Create database
sudo -u postgres createdb fleetops
sudo -u postgres createuser -P fleetops
```

---

## Common Tasks

### Create First Agent

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Claude Code",
    "provider": "anthropic",
    "model": "claude-3-sonnet",
    "capabilities": ["coding", "review"],
    "level": "senior"
  }'
```

### Create First Task

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Review Pull Request #123",
    "description": "Check code quality and test coverage",
    "agent_id": "AGENT_ID",
    "risk_level": "medium"
  }'
```

### Connect Slack

1. Create app at https://api.slack.com/apps
2. Add Bot Token Scopes: `chat:write`, `chat:write.public`
3. Install to workspace
4. Copy Bot User OAuth Token to `.env`:
```env
SLACK_BOT_TOKEN=xoxb-...
```

### Connect Discord

1. Create app at https://discord.com/developers/applications
2. Add Bot, enable Message Content Intent
3. Copy token to `.env`:
```env
DISCORD_BOT_TOKEN=...
```

---

## Next Steps

- Read [API Reference](API_REFERENCE.md)
- Check [Architecture Overview](ARCHITECTURE.md)
- See [Contributing Guidelines](../CONTRIBUTING.md)
- Join [Discord](https://discord.gg/fleetops) (coming soon)

---

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo service postgresql status

# Test connection
psql -U fleetops -d fleetops -c "SELECT 1"

# Check logs
docker-compose logs postgres
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Check logs
docker-compose logs redis
```

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill process
kill -9 PID

# Or change port in .env
API_PORT=8001
```

### CORS Errors

Make sure `FRONTEND_URL` and `API_URL` in `.env` match your actual URLs.

---

## Support

- 📧 Email: juanestebanmosquera@yahoo.com
- 💬 GitHub Issues: https://github.com/LunarPerovskite/FleetOps/issues
- 📖 Documentation: https://docs.fleetops.io (coming soon)
