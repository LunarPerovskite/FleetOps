# FleetOps Test Plan

## Test Categories

### 1. Unit Tests (Priority 1)
- [ ] Auth service (login, register, token validation)
- [ ] Task service (create, approve, lifecycle)
- [ ] Agent service (hierarchy, sub-agents)
- [ ] Approval service (routing, SLA)
- [ ] Event service (signing, verification)
- [ ] Billing service (tiers, limits)
- [ ] Customer service (routing, queues)
- [ ] Analytics service (scoring, forecasting)
- [ ] Search service (filters, facets)
- [ ] All provider adapters (auth, db, monitoring, secrets, CDN)

### 2. Integration Tests (Priority 1)
- [ ] Full task lifecycle (create → approve → complete)
- [ ] Agent creation with sub-agents
- [ ] Human hierarchy assignments
- [ ] Approval ladder enforcement
- [ ] WebSocket communication
- [ ] Provider adapter integration
- [ ] Database transactions
- [ ] Rate limiting

### 3. API Tests (Priority 2)
- [ ] All endpoints return correct status codes
- [ ] Authentication required on protected routes
- [ ] Rate limiting works
- [ ] Input validation
- [ ] Error responses are structured

### 4. Frontend Tests (Priority 2)
- [ ] Component rendering
- [ ] User interactions
- [ ] API integration
- [ ] Error handling
- [ ] Responsive design

### 5. E2E Tests (Priority 3)
- [ ] User registration flow
- [ ] Create and approve task
- [ ] Agent management
- [ ] Dashboard navigation
- [ ] Provider configuration

## Test Tools
- **Backend**: pytest, pytest-asyncio, httpx
- **Frontend**: Vitest, React Testing Library
- **E2E**: Playwright
- **Coverage**: pytest-cov

## Coverage Goals
- Unit: 80%
- Integration: 70%
- API: 90%
- Overall: 80%
