# FleetOps vs Competition

## Executive Summary

FleetOps is the **only platform** that combines:
1. **Governance-first** approach (not just observability)
2. **Human hierarchy** as first-class citizens (6 levels)
3. **Agent hierarchy** with sub-agents (5 levels, up to 5 sub-agents each)
4. **Multi-channel customer service** (WhatsApp, Telegram, Web, Voice, Email, Discord)
5. **Cross-machine distributed** architecture (WebSocket hub)
6. **Evidence-first compliance** (cryptographically signed logs)
7. **Universal connector** (one base class for all agent types)

---

## Detailed Comparison

### AgentOps
| Feature | AgentOps | FleetOps | Winner |
|---------|----------|----------|--------|
| **Type** | Observability | Governance + Orchestration | FleetOps |
| **Human-in-the-loop** | ❌ Manual only | ✅ First-class, any stage | FleetOps |
| **Human hierarchy** | ❌ None | ✅ 6 levels | FleetOps |
| **Agent hierarchy** | ❌ None | ✅ 5 levels + sub-agents | FleetOps |
| **Sub-agents** | ❌ None | ✅ Up to 5 per agent | FleetOps |
| **Multi-tenant** | ❌ Single org | ✅ Orgs + Teams + Projects | FleetOps |
| **Customer service** | ❌ None | ✅ 6 channels | FleetOps |
| **Cross-machine** | ❌ Local only | ✅ Distributed WebSocket | FleetOps |
| **Evidence store** | ⚠️ Logs | ✅ Cryptographically signed | FleetOps |
| **LLM cost tracking** | ✅ Yes | ✅ Yes | Tie |
| **Self-hosted** | ✅ Enterprise | ✅ All tiers | FleetOps |
| **Pricing** | $40/mo Pro | $29/mo Pro | FleetOps |
| **Free tier** | 5,000 events | 3 agents, 1 team, 1GB logs | FleetOps |
| **Integrations** | 400+ LLMs | 15+ connectors (growing) | AgentOps |
| **Maturity** | 2+ years | Alpha | AgentOps |

**Verdict**: AgentOps is a mature observability tool. FleetOps is a governance platform that includes observability. Different use cases.

---

### LangSmith (LangChain)
| Feature | LangSmith | FleetOps | Winner |
|---------|-----------|----------|--------|
| **Type** | Tracing | Governance | FleetOps |
| **Human approval** | ❌ None | ✅ Full workflow | FleetOps |
| **Role-based access** | ❌ None | ✅ 6 human levels | FleetOps |
| **Customer channels** | ❌ None | ✅ Multi-channel | FleetOps |
| **Self-hosted** | ✅ Yes | ✅ Yes | Tie |
| **LangChain focus** | ✅ Deep | ⚠️ Via connector | LangSmith |
| **Maturity** | 1+ years | Alpha | LangSmith |

**Verdict**: LangSmith is for LangChain developers. FleetOps is for organizations managing heterogeneous agent fleets.

---

### Langfuse
| Feature | Langfuse | FleetOps | Winner |
|---------|----------|----------|--------|
| **Type** | Observability | Governance | FleetOps |
| **Human-in-the-loop** | ❌ None | ✅ Full | FleetOps |
| **Prompt management** | ✅ Excellent | ✅ Versioned | Tie |
| **Cost tracking** | ✅ Yes | ✅ Yes | Tie |
| **Customer service** | ❌ None | ✅ Multi-channel | FleetOps |
| **Self-hosted** | ✅ Yes | ✅ Yes | Tie |

**Verdict**: Langfuse is excellent for prompt engineering. FleetOps is for governance and compliance.

---

### Prefactor
| Feature | Prefactor | FleetOps | Winner |
|---------|-----------|----------|--------|
| **Type** | Single-agent governance | Fleet-wide governance | FleetOps |
| **Multi-agent** | ❌ No | ✅ Yes | FleetOps |
| **Sub-agents** | ❌ No | ✅ Yes | FleetOps |
| **Human hierarchy** | ⚠️ Basic | ✅ Full | FleetOps |
| **Customer service** | ❌ None | ✅ Multi-channel | FleetOps |
| **Self-hosted** | ⚠️ Limited | ✅ Full | FleetOps |

**Verdict**: Prefactor focuses on single-agent governance. FleetOps governs entire fleets.

---

### GitHub Copilot / Claude Code
| Feature | Copilot/Claude | FleetOps | Winner |
|---------|---------------|----------|--------|
| **Type** | Coding assistant | Control plane | Different |
| **Governance** | ❌ None | ✅ Full | FleetOps |
| **Cross-agent** | ❌ Single | ✅ Multi-agent | FleetOps |
| **Evidence** | ❌ None | ✅ Immutable | FleetOps |
| **Human hierarchy** | ❌ None | ✅ 6 levels | FleetOps |
| **Integration** | ✅ Deep | ✅ Via connector | Copilot |

**Verdict**: Copilot/Claude are tools. FleetOps governs them.

---

### CrewAI / AutoGen
| Feature | CrewAI/AutoGen | FleetOps | Winner |
|---------|---------------|----------|--------|
| **Type** | Multi-agent framework | Governance layer | Different |
| **Agent frameworks** | ✅ Excellent | ⚠️ Via connectors | CrewAI |
| **Governance** | ❌ None | ✅ Full | FleetOps |
| **Human oversight** | ❌ None | ✅ First-class | FleetOps |
| **Customer service** | ❌ None | ✅ Multi-channel | FleetOps |

**Verdict**: CrewAI/AutoGen build agent teams. FleetOps governs them.

---

## FleetOps Unique Advantages

### 1. Evidence-First Compliance
- Cryptographically signed event log
- Immutable (no deletes, no edits)
- Export: JSON, CSV, PDF compliance reports
- Hot storage (90 days) + cold storage (compressed)
- SOC-2, HIPAA, GDPR ready

### 2. Universal Connector Architecture
- One base class for ALL agent types:
  - Coding: Claude, Codex, Copilot, Kilo, OpenCode
  - Customer service: WhatsApp, Telegram, Web, Voice, Email, Discord
  - Sales: WhatsApp, Telegram, Web
  - General: Gemini, Grok, Ollama, AutoGen, CrewAI, LangChain
- Supports CLI and Cloud modes
- Sub-agent hierarchy: any agent can create up to 5 sub-agents
- Cross-machine: agents connect from anywhere via WebSocket

### 3. Human-First Governance
- 6-level human hierarchy: Executive → Director → Senior Operator → Operator → Reviewer → Viewer
- HiTL at ANY stage, not just approval gates
- Role-based SLA: critical tasks get 5-min response, low-risk auto-approved
- Full audit trail: who approved what, when, with comments
- Workload distribution: who is approving what, SLA countdowns

### 4. Multi-Tenant Organization Model
- Organizations with multiple teams
- Teams with multiple projects
- Cost attribution: org, team, user, agent, task, cost center
- Agent sharing: team-owned or personal
- Budget alerts and spending limits

### 5. Cross-Provider Cost Control
- Track costs across Anthropic, OpenAI, Ollama, Gemini, Grok
- Per-agent, per-task, per-team cost allocation
- Model comparison: cost per task, quality per dollar
- Budget alerts when thresholds reached

### 6. Customer Service Integration
- WhatsApp, Telegram, Web chat, Voice, Email, Discord
- Auto-response with escalation keywords
- Human handoff with SLA tracking
- Conversation threading across channels
- Sentiment analysis for voice calls

### 7. Competitive Pricing
- Free: $0 (3 agents, 1 team, 1GB logs)
- Pro: $29/mo (unlimited agents, 50GB logs)
- Business: $99/mo (SSO, analytics, compliance exports)
- Enterprise: Custom (self-hosted, SLA)

vs AgentOps:
- Free: $0 (5,000 events)
- Pro: $40/mo (unlimited events)
- Enterprise: Custom

---

## What FleetOps Needs to Catch Up

1. **Maturity**: 2+ years behind AgentOps, LangSmith
2. **Integrations**: 400+ LLMs vs 15 connectors
3. **Community**: New project, needs contributors
4. **Documentation**: Needs comprehensive docs
5. **Battle-tested**: Alpha stage, needs production users

---

## Recommendations

### For Organizations Choosing a Platform:

**Choose FleetOps if:**
- You need governance and compliance
- You have multiple agent types (coding + customer service)
- You need human hierarchy and approval workflows
- You need evidence for auditors/regulators
- You want self-hosted at any tier

**Choose AgentOps if:**
- You need observability for existing agents
- You want 400+ LLM integrations
- You need mature, battle-tested platform
- Budget is not a constraint

**Choose LangSmith if:**
- You're building with LangChain
- You need deep prompt management
- You want tracing for debugging

**Choose CrewAI if:**
- You're building multi-agent teams
- You need agent frameworks
- Governance is secondary

---

*Analysis Date: April 2026*
*FleetOps Version: 0.1.0 Alpha*
