# FleetOps Deploy Button

## Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/LunarPerovskite/FleetOps)

## Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/FleetOps)

## Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/LunarPerovskite/FleetOps)

## Heroku (Legacy)

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/LunarPerovskite/FleetOps)

---

## Environment Variables Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `JWT_SECRET` | Secret for JWT tokens | `your-super-secret-key` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `FRONTEND_URL` | Frontend URL | `https://fleetops.vercel.app` |
| `API_URL` | Backend API URL | `https://fleetops-api.vercel.app` |

## One-Click Deploy

All buttons above will:
1. Clone the repository
2. Create a new project
3. Prompt for environment variables
4. Deploy the application

## Post-Deploy

After deployment:
1. Visit `/onboarding` to set up your organization
2. Configure providers in `/providers`
3. Invite team members
4. Start creating tasks and agents

## Self-Hosted

Want to self-host? See [README.md](README.md) for Docker deployment.

**Self-hosted is always 100% FREE with all features.**
