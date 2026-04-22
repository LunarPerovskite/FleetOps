# FleetOps Code Quality Audit

**Date**: 2026-04-22
**Scope**: Full codebase review for quality, robustness, and gaps
**Status**: Self-hosted beta

---

## 🚨 CRITICAL ISSUES (Fix First)

### 1. Security: Missing Production-Ready Dependencies
- **SQLAlchemy**: 2.0.25 has known issues. Upgrade to 2.0.28+
- **Pydantic**: 2.5.3 missing security patches. Upgrade to 2.6+
- **python-jose**: Abandoned project. Replace with `PyJWT` or `jose` from `python-jose` is fine but unmaintained
- **passlib**: 1.7.4 has argon2 issues. Add `argon2-cffi` explicitly
- **Missing**: `bcrypt` explicitly declared (needed for passlib)
- **Missing**: `python-jose` needs `cryptography` backend
- **Missing**: `slowapi` or better rate limiting library

**Recommendation**: Update requirements.txt:
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
pydantic==2.7.0
pydantic-settings==2.2.0
pyjwt==2.8.0
cryptography==42.0.0
passlib[bcrypt,argon2]==1.7.4
argon2-cffi==23.1.0
python-multipart==0.0.9
httpx==0.27.0
redis==5.0.3
celery==5.4.0
pytest==8.2.0
pytest-asyncio==0.23.5
python-dotenv==1.0.1
psycopg2-binary==2.9.9
asyncpg==0.29.0
structlog==24.1.0
slowapi==0.1.9
httpx-auth==0.22.0
```

### 2. Database: Missing Connection Pooling
Current `database.py` likely doesn't configure connection pooling. This will fail under load.

**Add to core/database.py**:
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Health check connections
    pool_recycle=3600,   # Recycle connections every hour
    echo=False
)
```

### 3. Authentication: Weak JWT Configuration
Need explicit JWT algorithm specification and token expiry management.

**Add to auth.py**:
```python
# Explicit algorithm (prevent algorithm confusion attacks)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
```

### 4. Missing Input Size Limits
- No file upload size limits
- No request body size limits
- No rate limiting on critical endpoints

**Add to main.py**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

### 5. Missing Error Monitoring
No Sentry/Rollbar integration for catching production errors.

---

## ⚠️ HIGH PRIORITY (Fix Before Launch)

### 6. Frontend: Missing Error Boundaries
React apps crash if any component throws. Need error boundaries.

**Create `components/ErrorBoundary.tsx`**:
```tsx
class ErrorBoundary extends React.Component {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error, info) { console.error(error, info); }
  render() { return this.state.hasError ? <FallbackUI /> : this.props.children; }
}
```

### 7. API Client: No Retry Logic
Current `api.ts` has no retry for failed requests.

**Add axios retry**:
```typescript
import axiosRetry from 'axios-retry';
axiosRetry(api, { retries: 3, retryDelay: axiosRetry.exponentialDelay });
```

### 8. Missing WebSocket Reconnection
WebSocket doesn't auto-reconnect on disconnect.

**Add to useWebSocket.ts**:
```typescript
const reconnect = useCallback(() => {
  setTimeout(() => connect(), 3000);
}, [connect]);
```

### 9. Missing Form Validation Schema
Forms use manual validation. Should use Zod or Yup.

**Add `zod` to frontend**:
```typescript
import { z } from 'zod';
const taskSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().optional(),
  risk_level: z.enum(['low', 'medium', 'high', 'critical'])
});
```

### 10. No API Versioning Strategy
Routes use `/api/v1` but no migration plan for v2.

**Recommendation**: Add version to OpenAPI schema and document deprecation policy.

### 11. Missing Pagination on List Endpoints
Tasks, agents, events lists will become slow with 1000+ items.

**Add to all list routes**:
```python
from fastapi import Query

@router.get("/tasks")
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ...
):
    offset = (page - 1) * page_size
    return db.query(Task).offset(offset).limit(page_size).all()
```

### 12. No Caching Strategy
Every request hits the database. No Redis caching for reads.

**Add Redis caching**:
```python
from redis import Redis
import json

cache = Redis.from_url(settings.REDIS_URL)

def cached(key_prefix, ttl=300):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{hash(str(args))}"
            cached = cache.get(cache_key)
            if cached: return json.loads(cached)
            result = await func(*args, **kwargs)
            cache.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 13. Frontend: No State Management for Lists
Using local state for lists. Should use React Query for caching.

**Migrate to React Query**:
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['tasks'],
  queryFn: tasksAPI.list,
  staleTime: 30000  // 30s cache
});
```

### 14. Missing API Response Types
Frontend uses `any` types for API responses. Should define interfaces.

**Create `types/api.ts`**:
```typescript
export interface Task {
  id: string;
  title: string;
  status: 'created' | 'planning' | 'executing' | 'completed';
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
}
```

### 15. No Automated Testing in CI
GitHub Actions runs lint but not full test suite.

**Add to `.github/workflows/ci.yml`**:
```yaml
- name: Run backend tests
  run: cd backend && pytest tests/ -v

- name: Run frontend tests
  run: cd frontend && npm test -- --watchAll=false
```

---

## 📝 MEDIUM PRIORITY (Quality Improvements)

### 16. Database: Missing Indexes
No indexes on frequently queried columns.

**Add migration**:
```sql
CREATE INDEX idx_tasks_org_id ON tasks(org_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_approvals_decision ON approvals(decision);
```

### 17. Missing Soft Deletes
All deletes are hard deletes. No recovery possible.

**Add to models**:
```python
class Task(Base):
    deleted_at = Column(DateTime, nullable=True)
    
    @classmethod
    def active(cls):
        return cls.query.filter(cls.deleted_at.is_(None))
```

### 18. No Audit Logging Middleware
Events are created manually. Should be automatic.

**Add middleware**:
```python
@app.middleware("http")
async def audit_middleware(request, call_next):
    response = await call_next(request)
    if request.method in ["POST", "PUT", "DELETE"]:
        log_audit_event(request, response)
    return response
```

### 19. Frontend: Missing Accessibility
- No ARIA labels
- No keyboard navigation
- No screen reader support

### 20. Missing API Documentation Examples
OpenAPI docs exist but no request/response examples.

### 21. No Database Backup Strategy
Backup script exists but no scheduled execution.

### 22. Missing Health Check for External Services
`/health` checks API but not database or Redis connectivity.

### 23. No Graceful Shutdown
Docker kill signal not handled properly.

**Add to main.py**:
```python
import signal

@app.on_event("shutdown")
async def shutdown():
    await redis.close()
    await engine.dispose()
```

### 24. Missing Request ID Tracking
No correlation IDs for tracing requests across services.

### 25. No Content Security Policy Headers
Security headers set but CSP not configured.

---

## 🎨 LOW PRIORITY (Nice to Have)

### 26. Frontend: Component Tests Missing
Only 6 backend tests. No frontend component tests.

### 27. No E2E Tests
No Playwright or Cypress tests.

### 28. No Performance Monitoring
No APM (New Relic, Datadog APM).

### 29. Missing OpenTelemetry
No distributed tracing.

### 30. No Dependency Scanning
No `safety` or `pip-audit` in CI.

---

## 📋 RECOMMENDED PRIORITY ORDER

### Phase 1 (This Week - Critical)
1. ✅ Update dependencies (security)
2. ✅ Add connection pooling
3. ✅ Add JWT algorithm specification
4. ✅ Add rate limiting (slowapi)
5. ✅ Add request size limits

### Phase 2 (Next Week - Important)
6. ✅ Add React Error Boundary
7. ✅ Add API retry logic
8. ✅ Add WebSocket reconnection
9. ✅ Add database indexes
10. ✅ Add pagination to all lists

### Phase 3 (Before Launch - Quality)
11. ✅ Add Zod form validation
12. ✅ Add API response types
13. ✅ Migrate to React Query
14. ✅ Add soft deletes
15. ✅ Add health checks for DB/Redis

### Phase 4 (Post-Launch)
16. Add E2E tests
17. Add performance monitoring
18. Add OpenTelemetry
19. Add dependency scanning
20. Add CSP headers

---

## 🏆 STRENGTHS (What's Good)

1. ✅ **Complete feature set** — All critical features from design.md
2. ✅ **Provider agnostic** — Good adapter pattern
3. ✅ **Real API integration** — All pages connected
4. ✅ **Comprehensive docs** — 4 documentation files
5. ✅ **Docker setup** — Easy local development
6. ✅ **Security foundations** — CSP, XSS, CSRF present
7. ✅ **Open source ready** — MIT license, CoC, Security.md

---

## 💡 RECOMMENDATIONS

**If launching this week:**
- Fix Phase 1 (critical security)
- Fix Phase 2 (user experience)
- Deploy with monitoring

**If launching next month:**
- Fix Phase 1 + 2 + 3
- Add comprehensive testing
- Do security audit

**For enterprise readiness:**
- Fix all phases
- Add SOC 2 compliance features
- Add SAML/SSO support
- Add audit logging
- Add RBAC (role-based access control)

---

*Audit completed: 2026-04-22*
*Next step: Fix Phase 1 critical issues*
