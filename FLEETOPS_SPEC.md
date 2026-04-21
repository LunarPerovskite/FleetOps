# AgentHQ — Platform Specification
## The Operating System for Governed Human-Agent Work

> "Every AI action, accountable. Every agent, visible. Every human, in control."

---

## 1. WHAT IS AGENTHQ?

AgentHQ is a **centralized control plane** that connects existing AI coding agents (Claude Code, Codex, Copilot, Kilo, OpenCode, etc.) and adds:
- Human-in-the-loop at any workflow stage
- Full hierarchy for humans and agents
- Complete observability (LLM calls, prompts, costs)
- Immutable evidence store (logs, approvals, decisions)
- Fleet-wide visibility and control

**Not a new agent.** It's the governance layer that makes any agent team-ready, auditable, and controllable.

---

## 2. WHO IS IT FOR?

| User type | What they get |
|---|---|
| Solo developers | Personal agent fleet with full oversight |
| Engineering teams | Multi-agent collaboration with human approvals |
| Organizations | Fleet-wide governance, cost control, compliance |
| Regulated industries | Audit-ready evidence for every AI decision |
| Enterprises | Self-hosted deployment, SSO, compliance bundles |

---

## 3. HUMAN HIERARCHY

| Level | Role | Permissions |
|---|---|---|
| 1 | **Executive** | Full fleet view, highest-risk approvals, policy setting |
| 2 | **Director / Lead** | Team management, medium-high risk approvals |
| 3 | **Senior Operator** | Day-to-day oversight, medium-risk approvals, escalation |
| 4 | **Operator** | Works with agents, low-risk approvals, escalates |
| 5 | **Reviewer / Auditor** | Read-only access to all logs and evidence |
| 6 | **Viewer** | Dashboard-only, no action permissions |

Every human can be assigned to one or more teams.

---

## 4. AGENT HIERARCHY

| Level | Role | Description |
|---|---|---|
| 1 | **Lead Agent** | Coordinates sub-agents, proposes plans |
| 2 | **Senior Agent** | Complex tasks, flags risk, requests human input |
| 3 | **Junior Agent** | Simple tasks, reports, escalates uncertainty |
| 4 | **Specialist Agent** | Single domain (code, review, deploy, test) |
| 5 | **Monitor Agent** | Fleet watcher, flags anomalies, does NOT execute |

---

## 5. HUMAN-IN-THE-LOOP (HiTL) AT ANY POINT

Humans can be injected into **any stage** of the workflow — not just approvals:

```
Stage 1: INITIATION
    ↓ Human can intervene: confirm task scope, set priority
Stage 2: PLANNING
    ↓ Human can intervene: review agent's proposed plan
Stage 3: RESEARCH / DATA COLLECTION
    ↓ Human can intervene: validate sources, approve data access
Stage 4: EXECUTION (coding, writing, analysis)
    ↓ Human can intervene: mid-task check, approve direction change
Stage 5: REVIEW (by another agent or human)
    ↓ Human can intervene: approve final output
Stage 6: EXTERNAL ACTION (deploy, send, write)
    ↓ Human must intervene: explicit approval always
Stage 7: DELIVERY
    ↓ Human can intervene: confirm delivery method, timing
Stage 8: LOGGING + EVIDENCE STORE
    (automatic — no human needed)
```

Every HiTL insertion has:
- **Who** is required (role level)
- **Time limit** (SLA — if no response, escalate or pause)
- **Options**: approve / reject / request changes / escalate

---

## 6. TASK LIFECYCLE

```
Human (any level) initiates task
    ↓
Agent receives task
    ↓
Planning phase → HiTL: human reviews plan
    ↓
Execution begins
    ↓
Mid-task check → HiTL: human can intervene
    ↓
Review phase → HiTL: human approves output
    ↓
External action → HiTL: human must approve
    ↓
Evidence logged → immutable record
    ↓
Post-completion review → HiTL: auditor can review
```

---

## 7. APPROVAL RISK MATRIX

| Task Risk | Who can approve |
|---|---|
| LOW | Junior Agent (auto-approve) |
| MEDIUM | Senior Operator must approve |
| HIGH | Director must approve |
| CRITICAL | Executive + Director must both approve |
| BLOCKED | Task paused, escalates to next human level |

---

## 8. AGENT + HUMAN COLLABORATION MATRIX

| Agent Level | Can request help from | Can escalate to | Can approve |
|---|---|---|---|
| Junior Agent | Senior Agent | Senior Operator | nothing |
| Senior Agent | Lead Agent | Operator | low-risk tasks |
| Lead Agent | Monitor Agent | Senior Operator | medium-risk tasks |
| Monitor Agent | — | Director | flags only (no approval) |

---

## 9. FULL OBSERVABILITY — LLM USAGE TRACKING

Every model call is logged with:
- **Provider** (OpenAI, Anthropic, Ollama, Gemini, etc.)
- **Model** (e.g., claude-sonnet-4-6, gpt-5-nano)
- **Token count** (input + output + cache)
- **Cost** (computed from provider pricing)
- **Latency** (ms)
- **Task ID** (tied to the parent task)
- **Agent ID** (who made the call)
- **Temperature / parameters used**
- **Timestamp**

Daily / weekly / monthly cost breakdown per:
- Agent
- Team
- Project
- Customer (if multi-tenant)

---

## 10. PROMPT LINEAGE (Full Version Control)

Every prompt is versioned and stored:

| Field | What's tracked |
|---|---|
| **Prompt ID** | Unique version hash |
| **Version** | Semantic (v1, v2, v2.1) |
| **Agent** | Which agent used it |
| **Task** | Which task it was for |
| **System prompt** | Full system prompt snapshot |
| **User prompt** | Full user input snapshot |
| **Rendered prompt** | Final prompt with variables filled |
| **Model** | Which model received it |
| **Output** | Model's response (full) |
| **Response time** | ms |
| **Tokens** | in/out/cached |
| **Cost** | USD |
| **Context window used** | % |
| **Review status** | pending / approved / flagged |

**Prompt diffing**: compare v1 vs v2 of the same agent's system prompt.

**Searchable**: filter by agent, date range, task, prompt content, output content.

---

## 11. IMMUTABLE EVENT LOG (Everything Logged)

```
Timestamp | Event Type | Who/What | Details
--------------------------------------------------------------
T1 | task.created | human:john | task_id=x, description=y
T2 | task.assigned | agent:claude-code | assigned_to=senior-coder
T3 | prompt.v1.created | agent:claude-code | prompt_hash=abc123
T4 | llm.call.start | model:claude-sonnet-4-6 | tokens=1200
T5 | llm.call.end | model:claude-sonnet-4-6 | tokens_out=450, cost=$0.002
T6 | hitl.insertion.requested | agent:claude-code | stage=planning
T7 | human.approved | director:maria | hitl_id=h123, comments="ok"
T8 | task.completed | agent:claude-code | outcome=success
T9 | evidence.archived | system | task_id=x, size=2.3MB
```

Every event is **append-only** — no deletes, no edits.

---

## 12. SEARCHABLE EVIDENCE VAULT

**Search filters:**
- By task ID
- By agent
- By human
- By date range
- By prompt content (full-text search)
- By output content
- By LLM provider
- By cost range
- By token range
- By risk level
- By approval status

**Exports:**
- JSON (raw)
- CSV (spreadsheet)
- PDF (compliance report per task)

---

## 13. CONNECTED AGENTS (Supported)

| Agent | Connection Type | Status |
|---|---|---|
| Claude Code (Anthropic) | API key | ✅ Ready |
| Codex / ChatGPT (OpenAI) | API key | ✅ Ready |
| GitHub Copilot | OAuth (limited) | ⚠️ Partial |
| Kilo Code | API (if available) | ⚠️ Check |
| OpenCode | Webhook / SDK | ⚠️ Check |
| Gemini (Google) | API key | ✅ Ready |
| Grok (xAI) | API key | ✅ Ready |
| Ollama (local) | API key | ✅ Ready |
| Custom agents | SDK / webhook | ✅ Via SDK |

---

## 14. CONNECTOR SCHEMA (Webhooks)

Every agent sends events via webhook:

```json
{
  "event": "task_start | plan_ready | execution_progress | action_proposed | review_needed | approval_needed | executed | completed | failed",
  "task_id": "uuid",
  "agent_id": "agent-alias",
  "agent_level": "junior|senior|lead|monitor",
  "initiator_human": "human-id",
  "stage": "planning|execution|review|external_action|delivery",
  "hitl_required": true/false,
  "hitl_role_needed": "operator|senior|director|executive",
  "sla_minutes": 30,
  "data": { ... },
  "timestamp": "ISO8601"
}
```

---

## 15. AGENT CONNECTOR MANIFEST

Every agent declares itself on connection:

```json
{
  "agent_id": "uuid",
  "name": "Claude Code - Engineering",
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "capabilities": ["code", "review", "deploy"],
  "connector_type": "api_key",
  "api_endpoint": "https://api.anthropic.com",
  "callback_url": "https://agenthq.io/webhook/agent",
  "allowed_actions": ["read", "write", "execute"],
  "requires_hitl_at": ["external_action", "deploy"],
  "cost_center": "engineering",
  "org_id": "org-uuid",
  "owned_by": "user-uuid"
}
```

---

## 16. TENANT MODEL (Organizations + Teams + Users)

```
Platform (global)
└── Organization (company/account)
    ├── Admin (org-level settings, billing)
    ├── Teams (e.g., Engineering, Marketing, Ops)
    │   ├── Team Lead (human)
    │   └── Team Members (humans + agents)
    └── Shared Agents (owned by org)
        └── Per team: team-specific agents

Individual User (solo)
├── Personal agents
└── Can join organizations as member
```

**Two modes:**
- **Organization mode**: teams share agents, costs billed to org
- **Personal mode**: solo users, self-pay, private agents

---

## 17. COST ATTRIBUTION (Flexible)

| Mode | Who pays |
|---|---|
| **Organization pays** | Org budget covers all agents + humans |
| **Team pays** | Each team has a budget, charged separately |
| **User pays** | Individual users pay for their personal agents |
| **Per-agent pays** | Specific agents billed to specific cost centers |
| **混合 (Mixed)** | Combinations above |

**Cost tracking per:**
- Organization
- Team
- User
- Agent
- Task
- Cost center (custom dimension)

**Billing features:**
- Monthly invoices (PDF)
- Usage dashboards per org/team/user
- Alerts when budget threshold reached
- Credits / prepaid plans

---

## 18. LOGGING — FOREVER, ALWAYS

Storage architecture:
- **Hot storage** (last 90 days): fast query, full detail
- **Cold storage** (90+ days): compressed, searchable on demand
- **Immutable event log**: never deleted, cryptographically signed

Every event:
```json
{
  "event_id": "sha256-hash",
  "timestamp": "ISO8601",
  "org_id": "org-uuid",
  "team_id": "team-uuid",
  "user_id": "user-uuid",
  "agent_id": "agent-uuid",
  "task_id": "task-uuid",
  "event_type": "llm.call | prompt.created | hitl.requested | human.approved | etc.",
  "data": { ... },
  "signature": "sha256-of-event-for-immutability"
}
```

**Compliance exports:**
- GDPR-compliant data export (per user request)
- SOC2 audit reports
- Industry-specific (finance, healthcare) compliance bundles

---

## 19. SELF-HOSTED OPTION

For organizations that want to run it on their own infrastructure:

**Deployment options:**
- **Docker compose** (single VM, 1 click)
- **Kubernetes** (scale to hundreds of agents)
- **Bare metal** (for maximum control)

**Self-hosted includes:**
- Full platform features
- Connect their own API keys (no data leaves their network)
- Custom SSO / LDAP integration
- On-premise compliance (data never leaves their network)

---

## 20. REVENUE MODEL

| Tier | Price | Includes |
|---|---|---|
| **Free** | $0 | 1 org, 3 agents, 1 team, 1GB logs/month |
| **Pro** | $29/mo | Unlimited agents, teams, 50GB logs, priority support |
| **Business** | $99/mo | SSO, advanced analytics, compliance exports, API access |
| **Enterprise** | Custom | Self-hosted, unlimited, SLA, dedicated support |

---

## 21. DASHBOARD SECTIONS

### Fleet Overview
- Active agents + status
- Tasks in progress
- Human approvals pending
- Cost today / week / month

### Human Workload
- Who is approving what
- SLA countdown per pending item
- Escalations
- Workload distribution

### LLM Cost Analytics
- Cost per agent
- Cost per task
- Cost per team
- Token usage trends
- Model comparison
- Anomaly alerts

### Prompt Performance
- Avg tokens per task
- Avg latency per model
- Prompt version comparison
- Output quality scores
- Flagged prompts (errors, drift)

### Task Timeline
- All tasks with HiTL markers
- Who approved each stage
- Duration per stage
- Bottleneck detection

### Evidence Vault
- Full-text search across all logs
- Export compliance reports
- Incident replay
- Audit trail

### Policy Engine
- Rules per agent type
- Risk thresholds
- HiTL insertion rules
- Default approvers per risk level
- Policy change history

### Agent Registry
- All connected agents
- Role / tier / skills
- Permissions
- Uptime
- Cost to date

---

## 22. AGENTHQ SDK

```bash
pip install agenthq-sdk
```

```python
from agenthq import AgentHQ

client = AgentHQ(api_key="your-key", org_id="org-id")
client.connect_agent(
    name="My Agent",
    capabilities=["code", "review"],
    hitl_stages=["planning", "external_action"]
)
client.on_task_event(lambda event: client.report(event))
```

---

## 23. MVP BUILD PLAN

### Phase 1 — Core (weeks 1–4)
1. Auth system (signup, login, org/team management)
2. Agent connector SDK (at least Claude Code + Codex)
3. Task model (create → assign → execute → complete)
4. HiTL approval engine (approve/reject at any stage)
5. Evidence store (append-only log, forever)
6. LLM cost tracking (per call, per agent, per org)
7. Basic dashboard (fleet view, task queue, approvals)

### Phase 2 — Scale (weeks 5–12)
8. Prompt version control (full lineage)
9. Searchable evidence vault (Elasticsearch)
10. Multi-agent support (add more connectors)
11. Cost allocation (org/team/user pays)
12. Billing system (invoices, usage reports)
13. Self-hosted deployment (Docker compose)

---

## 24. COMPARISON VS EXISTING TOOLS

| Tool | What it does | AgentHQ difference |
|---|---|---|
| LangSmith | Tracing + debugging | Not a governance/approval system |
| Langfuse | Observability | No human hierarchy or HiTL |
| Prefactor | Governance + risk | Single-provider, not fleet-wide |
| Copilot | Code suggestions | No full agent control |
| Claude Code | Coding agent | No multi-agent coordination |
| pydantic-ai | Agent framework | No governance layer |

**AgentHQ's edge**: Fleet-wide visibility + human hierarchy + HiTL at any stage + full evidence store + cross-provider normalization.

---

## 25. WHERE WE DIFFERENTIATE (Honest Assessment)

**Real edge:**
- System of record + evidence bundle (not just tracing)
- Authority chain as first-class
- Cross-provider normalization (heterogeneous fleets)
- Supervisor advisory-only

**Not novel:**
- Governance + approval alone is a crowded category
- Agent registries exist in enterprise tools
- Tracing + observability is well-covered

**Defensible angle**: Evidence-first for regulated industries.

> "We are the proof you show to auditors, regulators, and compliance teams that every AI action had a human accountable for it."

---

## 26. TARGET VERTICALS

1. **Financial services** — fintech, banking, microfinance (Colombia + global)
2. **Healthcare admin** — clinics, labs, insurance
3. **Legal operations** — law firms, in-house legal
4. **E-commerce ops** — order handling, returns, support
5. **Government / public sector** — procurement, citizen attention

---

## 27. NEXT STEPS

1. Write full PRD document
2. Write database schema
3. Write API spec
4. Create AgentHQ SDK specification
5. Build MVP with Claude Code + Codex connectors
6. Launch beta

---

*Document version: 1.0 — April 2026*
*Author: AgentHQ Platform Design Team*