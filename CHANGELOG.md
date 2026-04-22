# Changelog

All notable changes to FleetOps will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Core platform: FastAPI backend, React frontend, PostgreSQL database
- Authentication: JWT-based auth with provider adapters (Clerk, Auth0, Okta)
- Task management: Create, approve, track tasks with risk levels
- Agent hierarchy: Customizable levels, unlimited sub-agents
- Approval workflows: Multi-stage with SLA tracking
- Evidence store: Immutable, cryptographically signed events
- Customer service: Multi-channel support (WhatsApp, Telegram, Web, Voice, Email, Discord)
- Provider adapters: Auth, DB, monitoring, secrets, CDN, email, storage
- Real-time updates: WebSocket hub with connection status
- Dashboard: Real-time stats, activity feed, pending approvals
- Onboarding: 7-step guided setup wizard
- Custom dashboard builder: 6 widget types
- Settings: Dark mode, language (EN/ES), notifications
- Mobile responsive: Split navigation for mobile/desktop
- Search: Full-text with filters across all pages
- Export: JSON export for events and audit logs
- Health checks: /health, /ready, /live endpoints
- Rate limiting: Redis-based with headers
- Security: CSP, XSS, CSRF, HSTS protection
- Testing: 6 test suites with pytest
- CI/CD: GitHub Actions with backend/frontend tests, security scan
- Documentation: README, CONTRIBUTING, MONETIZATION strategy
- Docker: Production compose with SSL, monitoring, backups

### Infrastructure
- Production Docker Compose with Nginx reverse proxy
- Automated backups with S3/R2 upload
- Prometheus + Grafana monitoring stack
- Alembic database migrations

## [0.1.0] - 2026-04-22

### Added
- Initial release with core governance platform
- All critical, high, and medium priority features implemented
- 137 files, 50+ commits
- Ready for beta testing
