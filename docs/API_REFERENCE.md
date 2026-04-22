# FleetOps API Reference

## Base URL

```
Development: http://localhost:8000
Production: https://api.fleetops.io
```

## Authentication

All endpoints (except `/health`, `/login`, `/register`) require a Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.fleetops.io/tasks
```

## Rate Limiting

- **Limit**: 100 requests per minute per client
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## Authentication

### POST /auth/register
Register a new user and organization.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe",
  "org_name": "My Company"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "operator",
    "org_id": "org_456"
  }
}
```

### POST /auth/login
Authenticate and get token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:** Same as register.

### GET /auth/me
Get current user info.

**Response:**
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "operator",
  "org_id": "org_456",
  "team_id": "team_789"
}
```

---

## Tasks

### GET /tasks
List tasks with optional filters.

**Query Parameters:**
- `status` — Filter by status (created, planning, executing, completed)
- `agent_id` — Filter by agent
- `page` — Page number (default: 1)
- `page_size` — Items per page (default: 20)

**Response:**
```json
{
  "tasks": [
    {
      "id": "task_123",
      "title": "Review Q3 Report",
      "status": "executing",
      "risk_level": "high",
      "agent_id": "agent_456",
      "org_id": "org_789"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20
}
```

### POST /tasks
Create a new task.

**Request:**
```json
{
  "title": "Deploy API v2",
  "description": "Update production API",
  "agent_id": "agent_456",
  "risk_level": "high",
  "priority": 80
}
```

### GET /tasks/{task_id}
Get task details.

### PUT /tasks/{task_id}
Update task.

### POST /tasks/{task_id}/approve
Approve/reject a task stage.

**Request:**
```json
{
  "decision": "approve",
  "comments": "Looks good to me",
  "human_id": "user_123"
}
```

### GET /tasks/{task_id}/events
Get task event history.

---

## Agents

### GET /agents
List agents.

### POST /agents
Create agent.

**Request:**
```json
{
  "name": "Claude Code",
  "provider": "anthropic",
  "model": "claude-3-sonnet",
  "capabilities": ["coding", "review"],
  "level": "senior",
  "org_id": "org_789"
}
```

### GET /agents/{agent_id}
Get agent details.

### PUT /agents/{agent_id}
Update agent.

### DELETE /agents/{agent_id}
Delete agent.

### GET /agents/{agent_id}/sub-agents
List sub-agents.

---

## Approvals

### GET /approvals
List approvals.

**Query Parameters:**
- `status` — pending, approved, rejected, escalated
- `task_id` — Filter by task

### GET /approvals/{approval_id}
Get approval details.

### POST /approvals/{approval_id}/decide
Make a decision.

**Request:**
```json
{
  "decision": "approve",
  "comments": "Approved with minor notes"
}
```

---

## Events

### GET /events
List events.

**Query Parameters:**
- `task_id` — Filter by task
- `event_type` — Filter by type
- `limit` — Max results (default: 100)

### GET /events/{event_id}
Get event details.

---

## Dashboard

### GET /dashboard/stats
Get dashboard statistics.

**Response:**
```json
{
  "total_tasks": 156,
  "active_agents": 12,
  "pending_approvals": 3,
  "cost_today": 45.67,
  "success_rate": 0.94
}
```

### GET /dashboard/activity
Get recent activity feed.

---

## Analytics

### GET /analytics
Get analytics overview.

### GET /analytics/agents
Get agent performance metrics.

### GET /analytics/costs
Get cost analytics.

---

## Search

### POST /search
Full-text search across tasks, agents, and events.

**Request:**
```json
{
  "search_text": "deploy",
  "filters": {
    "status": ["executing", "completed"],
    "date_from": "2026-01-01",
    "date_to": "2026-12-31"
  }
}
```

---

## Customer Service

### GET /customer-service/sessions
List customer service sessions.

### GET /customer-service/sessions/{session_id}
Get session with messages.

### POST /customer-service/sessions/{session_id}/messages
Send a message.

**Request:**
```json
{
  "content": "How can I help you today?",
  "agent_id": "agent_123"
}
```

### POST /customer-service/sessions/{session_id}/handoff
Request human handoff.

**Request:**
```json
{
  "reason": "Complex technical issue",
  "notes": "Customer needs database migration help"
}
```

---

## Hierarchy

### GET /hierarchy
Get hierarchy configuration.

### PUT /hierarchy
Update hierarchy.

### POST /hierarchy/validate
Validate hierarchy configuration.

---

## Providers

### GET /providers/config
Get provider configuration.

### PUT /providers/config
Update provider configuration.

### GET /providers/health
Check provider health status.

---

## Onboarding

### GET /onboarding/progress
Get onboarding progress.

### POST /onboarding/steps/{step_id}/complete
Complete a step.

### GET /onboarding/status
Quick status check.

---

## Health

### GET /health
Basic health check.

### GET /ready
Readiness check (includes database).

### GET /live
Liveness check.

### GET /health/detailed
Detailed health with all services.

---

## WebSocket

### /ws
Real-time updates.

**Connection:**
```
ws://api.fleetops.io/ws?token=YOUR_TOKEN
```

**Events:**
- `task_created` — New task created
- `task_completed` — Task finished
- `approval_required` — New approval needed
- `agent_created` — New agent registered

---

## Error Responses

All errors follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable description",
  "details": {},
  "correlation_id": "uuid-for-tracing"
}
```

Common status codes:
- `400` — Bad Request
- `401` — Unauthorized
- `403` — Forbidden
- `404` — Not Found
- `422` — Validation Error
- `429` — Rate Limited
- `500` — Internal Error
