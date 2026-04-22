# FleetOps Agent Architecture — Local, Remote, and Cross-Agent Interaction

## Overview

FleetOps is designed as a **central hub** that can manage agents running:
- ✅ **On the same machine** (localhost)
- ✅ **On remote machines** (different servers)
- ✅ **In the cloud** (managed services)
- ✅ **Mixed setup** (some local, some remote)

Agents **do NOT directly interact** with each other. Instead, **FleetOps orchestrates** the interaction:

```
┌─────────────────────────────────────────────────────────────┐
│                    FleetOps (Central Hub)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Agent 1    │  │  Agent 2    │  │  Agent 3    │         │
│  │  (Local)    │  │  (Remote)   │  │  (Cloud)    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │               │
│         └────────────────┼────────────────┘               │
│                          │                                  │
│                    ┌─────┴─────┐                           │
│                    │ Human     │                           │
│                    │ Approval  │                           │
│                    └───────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏠 Local Machine Setup

### Agents Running on Same Machine

All agents can run on the same machine as FleetOps:

```bash
# FleetOps running on localhost:8000
# Agents running on different ports

OPENCLAW_URL=http://localhost:8080      # OpenClaw
HERMES_URL=http://localhost:9090        # Hermes  
CREWAI_URL=http://localhost:8001        # CrewAI
AUTOGEN_URL=http://localhost:8002        # AutoGen
OLLAMA_URL=http://localhost:11434       # Ollama
CLAUDE_CODE_CLI=claude                   # Claude Code (CLI)
AIDER_CLI=aider                         # Aider (CLI)
```

**Pros:**
- ✅ Low latency
- ✅ No network dependencies
- ✅ Easy to set up
- ✅ Secure (no external exposure)

**Cons:**
- ❌ Resource intensive (many agents)
- ❌ Single point of failure
- ❌ Limited scalability

---

## 🌐 Remote Machine Setup

### Agents Running on Different Machines

Agents can run on separate servers:

```bash
# FleetOps running on VPS: https://fleetops.yourdomain.com
# Agents running on different machines

OPENCLAW_URL=https://openclaw.internal:8080     # Dedicated OpenClaw server
CREWAI_URL=https://crewai.internal:8001         # Dedicated CrewAI server
AUTOGEN_URL=https://autogen.internal:8002         # Dedicated AutoGen server
OLLAMA_URL=https://gpu-server.internal:11434     # GPU server for Ollama
```

**Pros:**
- ✅ Distribute resource load
- ✅ GPU agents on GPU servers
- ✅ Better isolation
- ✅ Scalable

**Cons:**
- ❌ Network latency
- ❌ Requires connectivity
- ❌ Security configuration needed

---

## ☁️ Cloud/Managed Setup

### Managed Agent Services

```bash
# Using cloud services
DEVIN_API_URL=https://api.cognition.ai        # Devin (managed)
COPILOT_API_URL=https://api.github.com        # Copilot (managed)
SUPERAGI_URL=https://your-superagi.cloud      # SuperAGI Cloud
```

---

## 🔀 Mixed Setup (Recommended for Production)

### Hybrid Architecture

```yaml
# Example production setup
agents:
  # Critical agents - local for low latency
  openclaw:
    url: http://localhost:8080
    type: personal
    
  # Heavy compute - remote GPU server
  ollama:
    url: https://gpu-server.internal:11434
    type: local-llm
    
  # Team collaboration - remote server
  crewai:
    url: https://agents.internal:8001
    type: multi-agent
    
  # IDE agents - developer workstations
  claude_code:
    cli: claude
    type: ide
    # Runs on developer's machine, reports to FleetOps
    
  # Managed services - cloud
  devin:
    url: https://api.cognition.ai
    type: ide
    
  # Backup/secondary - different region
  autogen_backup:
    url: https://backup.internal:8002
    type: multi-agent
```

---

## 🔄 Cross-Agent Interaction (The Key Feature)

### How Agents Interact Through FleetOps

**Agents do NOT talk to each other directly.** FleetOps is the orchestrator:

```
┌──────────────────────────────────────────────────────────────┐
│                        FleetOps Hub                           │
│                                                               │
│  Step 1: CrewAI executes task                               │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                   │
│  │Researcher│──→│Writer   │──→│Editor   │                   │
│  └────┬────┘    └────┬────┘    └────┬────┘                   │
│       └──────────────┴──────────────┘                        │
│                      │                                         │
│                      ▼                                         │
│              Crew produces report                              │
│                      │                                         │
│  Step 2: FleetOps creates approval request                     │
│                      │                                         │
│                      ▼                                         │
│              ┌───────────────┐                                 │
│              │ Human Reviews │                                 │
│              │  ✓ Approve    │                                 │
│              └───────┬───────┘                                 │
│                      │                                         │
│  Step 3: FleetOps sends to next agent                         │
│                      │                                         │
│                      ▼                                         │
│  ┌─────────────────────────────┐                              │
│  │  Devin takes report         │                              │
│  │  Creates web application    │                              │
│  │  Based on report content    │                              │
│  └─────────────────────────────┘                              │
│                      │                                         │
│  Step 4: FleetOps creates new approval                        │
│                      │                                         │
│                      ▼                                         │
│              ┌───────────────┐                                 │
│              │ Human Reviews │                                 │
│              │  ✓ Approve    │                                 │
│              └───────────────┘                                 │
│                      │                                         │
│  Step 5: FleetOps deploys                                     │
│                      │                                         │
│                      ▼                                         │
│              Application deployed!                              │
└──────────────────────────────────────────────────────────────┘
```

### Interaction Patterns

#### Pattern 1: Sequential Pipeline
```python
# FleetOps orchestrates sequential execution
async def execute_pipeline(task_id, pipeline):
    results = {}
    
    for step in pipeline:
        # Execute with current agent
        agent = PersonalAgentAdapter(step["agent"])
        result = await agent.execute_task(
            task_id=f"{task_id}_{step['name']}",
            instructions=step["prompt"],
            context=results  # Pass previous results
        )
        
        # Wait for human approval
        approval = await wait_for_human_approval(result)
        
        if approval.decision == "approve":
            results[step["name"]] = result
        else:
            raise Exception(f"Step {step['name']} rejected")
    
    return results

# Example pipeline:
pipeline = [
    {"agent": "crewai", "name": "research", "prompt": "Research market trends"},
    {"agent": "openclaw", "name": "analysis", "prompt": "Analyze research data"},
    {"agent": "devin", "name": "implementation", "prompt": "Build app based on analysis"},
]
```

#### Pattern 2: Multi-Agent Debate
```python
# Multiple agents debate a topic
async def agent_debate(topic, agents=["autogen", "crewai", "openclaw"]):
    opinions = {}
    
    # Get opinions from all agents
    for agent_name in agents:
        agent = PersonalAgentAdapter(agent_name)
        opinion = await agent.execute_task(
            task_id=f"debate_{agent_name}",
            instructions=f"Analyze this topic and provide your perspective: {topic}"
        )
        opinions[agent_name] = opinion
    
    # Present all opinions to human
    comparison = create_comparison_view(opinions)
    
    # Human selects best approach
    selected = await wait_for_human_selection(comparison)
    
    return opinions[selected]
```

#### Pattern 3: Agent Consensus
```python
# Agents must agree before proceeding
async def agent_consensus(task, required_agents=["openclaw", "crewai"], threshold=0.8):
    approvals = {}
    
    for agent_name in required_agents:
        agent = PersonalAgentAdapter(agent_name)
        result = await agent.execute_task(
            task_id=f"consensus_{agent_name}",
            instructions=f"Review and approve: {task}"
        )
        approvals[agent_name] = result["approved"]
    
    # Calculate consensus
    approval_rate = sum(approvals.values()) / len(approvals)
    
    if approval_rate >= threshold:
        return {"status": "approved", "consensus": approval_rate}
    else:
        return {"status": "rejected", "approvals": approvals}
```

#### Pattern 4: Load Balancing
```python
# Distribute tasks across multiple agents
async def load_balanced_execute(tasks, agents=["openclaw", "crewai", "autogen"]):
    results = []
    
    # Assign tasks to least busy agents
    for i, task in enumerate(tasks):
        agent_name = agents[i % len(agents)]  # Round-robin
        
        agent = PersonalAgentAdapter(agent_name)
        result = await agent.execute_task(
            task_id=task["id"],
            instructions=task["instructions"]
        )
        
        results.append({
            "task": task["id"],
            "agent": agent_name,
            "result": result
        })
    
    return results
```

---

## 🏗️ Architecture Diagrams

### Full Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Internet / Cloud                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Devin      │  │   Copilot    │  │   SuperAGI   │          │
│  │   (Cognition)│  │   (GitHub)   │  │   (Cloud)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                     VPN / Internal Network                       │
│                            │                                     │
│  ┌─────────────────────────┼─────────────────────────────────┐  │
│  │                    FleetOps Hub                            │  │
│  │                     (VPS/Server)                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │ Task Queue  │  │ Approval    │  │ Event Log   │       │  │
│  │  │             │  │ System      │  │             │       │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │  │
│  │         │                │                │               │  │
│  │         └────────────────┼────────────────┘               │  │
│  │                          │                                │  │
│  │                    ┌─────┴─────┐                          │  │
│  │                    │ Router    │                          │  │
│  │                    │ (Distributes│                         │  │
│  │                    │ to agents) │                          │  │
│  │                    └─────┬─────┘                          │  │
│  │                          │                                │  │
│  │  ┌─────────┬─────────┬──┴──┬─────────┬─────────┐       │  │
│  │  │         │         │     │         │         │         │  │
│  │  ▼         ▼         ▼     ▼         ▼         ▼         │  │
│  │ ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐        │  │
│  │ │Ope│   │Her│   │Cre│   │Aut│   │Oll│   │Cus│        │  │
│  │ │nCl│   │mes│   │wAI│   │oGe│   │ama│   │tom│        │  │
│  │ │aw │   │   │   │   │   │n  │   │   │   │   │        │  │
│  │ └───┘   └───┘   └───┘   └───┘   └───┘   └───┘        │  │
│  │  :8080  :9090   :8001   :8002   :11434  :9999        │  │
│  │   ▲       ▲       ▲       ▲       ▲       ▲          │  │
│  └───┼───────┼───────┼───────┼───────┼───────┼──────────┘  │
│      │       │       │       │       │       │               │
│  ┌───┴───────┴───────┴───────┴───────┴───────┴───────────┐   │
│  │              Local Network / Docker Network            │   │
│  │                                                        │   │
│  │  All agents can be:                                    │   │
│  │  - Local (same machine)                               │   │
│  │  - Remote (different VMs)                             │   │
│  │  - Cloud (external services)                         │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Setup Examples

### Example 1: All Local (Development)

```bash
# .env
FLEETOPS_URL=http://localhost:8000

# All agents on same machine
OPENCLAW_URL=http://localhost:8080
HERMES_URL=http://localhost:9090
CREWAI_URL=http://localhost:8001
AUTOGEN_URL=http://localhost:8002
OLLAMA_URL=http://localhost:11434
CLAUDE_CODE_CLI=claude
AIDER_CLI=aider

# Docker Compose can run all services
```

### Example 2: Distributed (Production)

```bash
# FleetOps on main VPS
FLEETOPS_URL=https://fleetops.company.com

# Personal agents - local to FleetOps
OPENCLAW_URL=http://localhost:8080
HERMES_URL=http://localhost:9090

# Multi-agent frameworks - dedicated VM
CREWAI_URL=https://agents-vm1.internal:8001
AUTOGEN_URL=https://agents-vm1.internal:8002
META_GPT_URL=https://agents-vm2.internal:8003

# GPU agents - GPU server
OLLAMA_URL=https://gpu-server.internal:11434
LLAMAINDEX_URL=https://gpu-server.internal:8004

# IDE agents - developer machines (via VPN)
CLAUDE_CODE_CLI=claude  # Runs on dev machine, connects via CLI
DEVIN_API_URL=https://api.cognition.ai  # Cloud

# Cloud services
COPILOT_API_URL=https://api.github.com
```

### Example 3: Hybrid with Kubernetes

```yaml
# k8s/fleetops-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fleetops
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: fleetops
        image: fleetops:latest
        env:
        - name: OPENCLAW_URL
          value: "http://openclaw-service:8080"
        - name: CREWAI_URL
          value: "http://crewai-service:8001"
        - name: OLLAMA_URL
          value: "http://ollama-service:11434"
---
# k8s/openclaw-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openclaw
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: openclaw
        image: openclaw:latest
---
# k8s/ollama-deployment.yaml (on GPU nodes)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
spec:
  replicas: 1
  template:
    spec:
      nodeSelector:
        gpu: "true"
      containers:
      - name: ollama
        image: ollama/ollama:latest
        resources:
          limits:
            nvidia.com/gpu: 1
```

---

## 🔒 Security Considerations

### Network Security

```
┌────────────────────────────────────────────────────┐
│                    Firewall                         │
│  - Block external access to agent ports            │
│  - Only FleetOps can reach agents                  │
│                                                    │
│  External: 443 (FleetOps HTTPS only)               │
│  Internal: All ports between services              │
└────────────────────────────────────────────────────┘
```

### Authentication

```python
# Each agent connection uses:
- API keys (for cloud services)
- mTLS (for internal services)
- VPN (for remote access)
- Localhost only (for same-machine)
```

---

## 📊 Resource Management

### Resource Requirements by Agent Type

| Agent | CPU | RAM | GPU | Network | Best Location |
|-------|-----|-----|-----|---------|---------------|
| OpenClaw | Low | 512MB | No | Low | Same machine |
| Hermes | Low | 512MB | No | Low | Same machine |
| CrewAI | Medium | 2GB | Optional | Medium | Dedicated VM |
| AutoGen | Medium | 2GB | Optional | Medium | Dedicated VM |
| Ollama | High | 8GB+ | Required | Low | GPU Server |
| Claude Code | Low | 1GB | No | Medium | Dev machine |
| Devin | High | 4GB | No | High | Cloud/Remote |
| MetaGPT | Medium | 2GB | Optional | Medium | Dedicated VM |

---

## ✅ Summary

**Can they all be on the same machine?**
✅ **YES** — All agents can run locally with FleetOps

**Can they be remote?**
✅ **YES** — FleetOps connects via URLs/CLI paths

**Can they interact?**
✅ **YES** — FleetOps orchestrates interaction:
- Sequential pipelines
- Agent debates
- Consensus building
- Load balancing
- Human approval between steps

**Recommended setup:**
- **Development**: All local (Docker Compose)
- **Production**: Hybrid (some local, some remote, some cloud)
- **Scale**: Kubernetes with dedicated agent nodes

---

*FleetOps: The universal hub for AI agent governance*
