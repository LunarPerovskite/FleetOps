# FleetOps Agent Deployment Guide

## Overview

FleetOps can connect to agents deployed **any way you want**:

| Deployment Method | Supported | Examples |
|---|---|---|
| **Docker** | ✅ Yes | All agents in containers |
| **Docker Compose** | ✅ Yes | Full stack locally |
| **npm/Node.js** | ✅ Yes | Claude Code, Copilot CLI |
| **Python pip** | ✅ Yes | CrewAI, AutoGen, LangChain |
| **CLI binary** | ✅ Yes | Aider, Ollama, Claude Code |
| **VPS/VM** | ✅ Yes | Remote agents on servers |
| **Kubernetes** | ✅ Yes | Production scaling |
| **Systemd service** | ✅ Yes | Background services |
| **Process manager** | ✅ Yes | PM2, Supervisor |
| **Cloud functions** | ✅ Yes | AWS Lambda, Vercel |
| **Serverless** | ✅ Yes | Any HTTP endpoint |
| **Desktop app** | ✅ Yes | Cursor, VS Code extensions |
| **Mobile** | ✅ Partial | Via API |

---

## 🐳 Docker Deployment

### All Agents in Docker

```yaml
# docker-compose.agents.yml
version: '3.8'

services:
  # FleetOps Core
  fleetops:
    image: fleetops:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://fleetops:password@postgres:5432/fleetops
      - REDIS_URL=redis://redis:6379
      # Agent URLs (all internal Docker network)
      - OPENCLAW_URL=http://openclaw:8080
      - CREWAI_URL=http://crewai:8001
      - AUTOGEN_URL=http://autogen:8002
      - HERMES_URL=http://hermes:9090
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - postgres
      - redis
      - openclaw
      - crewai
      - ollama
    networks:
      - fleetops-network

  # Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: fleetops
      POSTGRES_PASSWORD: password
      POSTGRES_DB: fleetops
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - fleetops-network

  # Cache
  redis:
    image: redis:7-alpine
    networks:
      - fleetops-network

  # === AGENTS ===

  # OpenClaw Agent
  openclaw:
    image: openclaw:latest
    ports:
      - "8080:8080"  # Exposed for external access too
    environment:
      - OPENCLAW_MODE=governed
      - OPENCLAW_MAX_STEPS=50
    volumes:
      - openclaw_workspace:/workspace
    networks:
      - fleetops-network

  # CrewAI Multi-Agent
  crewai:
    build:
      context: ./agents/crewai
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - CREWAI_API_KEY=${CREWAI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - crewai_workspace:/workspace
    networks:
      - fleetops-network

  # AutoGen Multi-Agent
  autogen:
    build:
      context: ./agents/autogen
      dockerfile: Dockerfile
    ports:
      - "8002:8002"
    environment:
      - AUTOGEN_API_KEY=${AUTOGEN_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    networks:
      - fleetops-network

  # Hermes Agent
  hermes:
    image: hermes:latest
    ports:
      - "9090:9090"
    environment:
      - HERMES_PERSONA=professional
    networks:
      - fleetops-network

  # Ollama (GPU-enabled)
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    # GPU support
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - fleetops-network

  # LangChain Service
  langchain:
    build:
      context: ./agents/langchain
      dockerfile: Dockerfile
    ports:
      - "8003:8003"
    environment:
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    networks:
      - fleetops-network

  # LlamaIndex Service
  llamaindex:
    build:
      context: ./agents/llamaindex
      dockerfile: Dockerfile
    ports:
      - "8004:8004"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    networks:
      - fleetops-network

  # MetaGPT
  metagpt:
    build:
      context: ./agents/metagpt
      dockerfile: Dockerfile
    ports:
      - "8006:8006"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - metagpt_workspace:/workspace
    networks:
      - fleetops-network

  # SuperAGI
  superagi:
    image: superagi/superagi:latest
    ports:
      - "8010:8010"
    environment:
      - SUPERAGI_API_KEY=${SUPERAGI_API_KEY}
    networks:
      - fleetops-network

  # BabyAGI
  babyagi:
    build:
      context: ./agents/babyagi
      dockerfile: Dockerfile
    ports:
      - "8005:8005"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    networks:
      - fleetops-network

  # TaskWeaver (Microsoft)
  taskweaver:
    build:
      context: ./agents/taskweaver
      dockerfile: Dockerfile
    ports:
      - "8012:8012"
    networks:
      - fleetops-network

  # PraisonAI
  praisonai:
    build:
      context: ./agents/praisonai
      dockerfile: Dockerfile
    ports:
      - "8011:8011"
    networks:
      - fleetops-network

  # ChatDev
  chatdev:
    build:
      context: ./agents/chatdev
      dockerfile: Dockerfile
    ports:
      - "8007:8007"
    networks:
      - fleetops-network

  # AgentVerse
  agentverse:
    build:
      context: ./agents/agentverse
      dockerfile: Dockerfile
    ports:
      - "8009:8009"
    networks:
      - fleetops-network

  # GPTeam
  gpteam:
    build:
      context: ./agents/gpteam
      dockerfile: Dockerfile
    ports:
      - "8008:8008"
    networks:
      - fleetops-network

  # Local LLM (vLLM)
  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8013:8013"
    environment:
      - MODEL=mistral-7b
    command: --model mistral-7b --port 8013
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - fleetops-network

volumes:
  postgres_data:
  openclaw_workspace:
  crewai_workspace:
  ollama_models:
  metagpt_workspace:

networks:
  fleetops-network:
    driver: bridge
```

### Run Everything

```bash
# Start all services
docker-compose -f docker-compose.agents.yml up -d

# Scale specific agents
docker-compose -f docker-compose.agents.yml up -d --scale crewai=3

# View logs
docker-compose -f docker-compose.agents.yml logs -f fleetops

# Restart one agent
docker-compose -f docker-compose.agents.yml restart crewai
```

---

## 📦 npm/Node.js Deployment

### Agents Installed via npm

```bash
# Install Claude Code globally
npm install -g @anthropic-ai/claude-code

# FleetOps connects via CLI path
CLAUDE_CODE_CLI=claude
```

```bash
# Install Copilot CLI (if available)
npm install -g @github/copilot-cli

# FleetOps connects via CLI or API
COPILOT_CLI_PATH=/usr/local/bin/copilot
```

```bash
# Install other Node.js agents
npm install -g some-ai-agent
```

### Running Node.js Agents as Services

```json
// package.json for agent
{
  "name": "custom-agent",
  "version": "1.0.0",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.0",
    "axios": "^1.6.0"
  }
}
```

```javascript
// server.js - Custom agent HTTP API
const express = require('express');
const app = express();

app.use(express.json());

app.post('/execute', async (req, res) => {
  const { instructions, context } = req.body;
  
  // Agent logic here
  const result = await executeTask(instructions, context);
  
  res.json({
    status: 'success',
    output: result,
    requires_approval: true
  });
});

app.listen(9999, () => {
  console.log('Custom agent running on port 9999');
});
```

---

## 🐍 Python pip Deployment

### Agents Installed via pip

```bash
# Install Python agents
pip install crewai
pip install autogen
pip install langchain
pip install llama-index
pip install metagpt
pip install babyagi
pip install superagi
pip install praisonai
pip install taskweaver
pip install aider-chat
pip install openclaw  # hypothetical
```

### Running Python Agents

```bash
# Start CrewAI service
crewai server --port 8001

# Start AutoGen service
autogen server --port 8002

# Start LangChain service
langchain serve --port 8003
```

### Python Agent Wrapper Example

```python
# agents/crewai/server.py
from fastapi import FastAPI
from crewai import Agent, Task, Crew

app = FastAPI()

@app.post("/execute")
async def execute(request: dict):
    instructions = request["instructions"]
    
    # Create crew
    researcher = Agent(
        role='Researcher',
        goal='Research topics thoroughly',
        backstory='Expert researcher'
    )
    
    writer = Agent(
        role='Writer',
        goal='Write comprehensive content',
        backstory='Expert writer'
    )
    
    task = Task(
        description=instructions,
        agent=researcher
    )
    
    crew = Crew(
        agents=[researcher, writer],
        tasks=[task]
    )
    
    result = crew.kickoff()
    
    return {
        "status": "success",
        "output": result,
        "requires_approval": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

## 💻 CLI Binary Deployment

### Agents Installed as CLI Tools

```bash
# Claude Code (npm)
npm install -g @anthropic-ai/claude-code

# Aider (pip)
pip install aider-chat

# Ollama (binary)
curl -fsSL https://ollama.com/install.sh | sh

# Custom binary
wget https://example.com/agent-binary -O /usr/local/bin/my-agent
chmod +x /usr/local/bin/my-agent
```

### Running CLI Agents

```bash
# Start Ollama service
ollama serve

# Run Claude Code (interactive)
claude

# Run Aider
aider --model gpt-4 file.py
```

### FleetOps Connection to CLI Agents

```python
# backend/app/adapters/ide_agent_adapter.py
# Already handles CLI execution via subprocess

import subprocess

class ClaudeCodeAdapter:
    async def execute_task(self, task_id, instructions, repo_path):
        # Execute CLI command
        result = subprocess.run(
            ['claude', '--message', instructions, '--working-dir', repo_path],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        # Capture git diff
        diff = subprocess.run(
            ['git', 'diff'],
            capture_output=True,
            text=True,
            cwd=repo_path
        )
        
        return {
            "status": "success",
            "output": result.stdout,
            "diff": diff.stdout,
            "requires_approval": True
        }
```

---

## 🖥️ VPS/VM Deployment

### Deploy Agents on Separate VPS

```bash
# VPS 1: FleetOps + Light Agents
# Install FleetOps
git clone https://github.com/LunarPerovskite/FleetOps.git
cd FleetOps
docker-compose up -d

# VPS 2: GPU Server (Ollama + vLLM)
# Ubuntu with NVIDIA drivers
sudo apt update
sudo apt install nvidia-driver-535

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &

# Install vLLM
pip install vllm
python -m vllm.entrypoints.openai.api_server \
    --model mistral-7b \
    --port 8013

# VPS 3: Multi-Agent Frameworks (CrewAI + AutoGen)
pip install crewai autogen

# Start services
crewai server --port 8001 --host 0.0.0.0 &
autogen server --port 8002 --host 0.0.0.0 &
```

### FleetOps Configuration for Multi-VPS

```bash
# .env on FleetOps VPS
FLEETOPS_URL=https://fleetops.yourdomain.com

# Internal agents (same VPS)
OPENCLAW_URL=http://localhost:8080
HERMES_URL=http://localhost:9090

# Remote GPU server
OLLAMA_URL=https://gpu-server.yourdomain.com:11434
VLLM_URL=https://gpu-server.yourdomain.com:8013

# Remote agent VPS
CREWAI_URL=https://agents-vps.yourdomain.com:8001
AUTOGEN_URL=https://agents-vps.yourdomain.com:8002
META_GPT_URL=https://agents-vps.yourdomain.com:8003

# Cloud services
DEVIN_API_URL=https://api.cognition.ai
COPILOT_API_URL=https://api.github.com
```

---

## ☸️ Kubernetes Deployment

### K8s Manifests

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: fleetops
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fleetops-config
  namespace: fleetops
data:
  OPENCLAW_URL: "http://openclaw:8080"
  CREWAI_URL: "http://crewai:8001"
  AUTOGEN_URL: "http://autogen:8002"
  OLLAMA_URL: "http://ollama:11434"
---
# k8s/fleetops-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fleetops
  namespace: fleetops
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fleetops
  template:
    metadata:
      labels:
        app: fleetops
    spec:
      containers:
      - name: fleetops
        image: fleetops:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: fleetops-config
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: fleetops-secrets
              key: database-url
---
# k8s/crewai-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crewai
  namespace: fleetops
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crewai
  template:
    metadata:
      labels:
        app: crewai
    spec:
      containers:
      - name: crewai
        image: fleetops/crewai:latest
        ports:
        - containerPort: 8001
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: fleetops-secrets
              key: openai-key
---
# k8s/ollama-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: fleetops
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      nodeSelector:
        gpu: "true"  # Only run on GPU nodes
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        resources:
          limits:
            nvidia.com/gpu: 1
        volumeMounts:
        - name: ollama-models
          mountPath: /root/.ollama
      volumes:
      - name: ollama-models
        persistentVolumeClaim:
          claimName: ollama-models-pvc
```

---

## 🔧 Systemd Service Deployment

### Run Agents as System Services

```ini
# /etc/systemd/system/fleetops.service
[Unit]
Description=FleetOps
After=network.target

[Service]
Type=simple
User=fleetops
WorkingDirectory=/opt/fleetops
ExecStart=/usr/local/bin/docker-compose up
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/ollama.service
[Unit]
Description=Ollama LLM Server
After=network.target

[Service]
Type=simple
User=ollama
ExecStart=/usr/local/bin/ollama serve
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_PORT=11434"
Restart=always

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/crewai.service
[Unit]
Description=CrewAI Multi-Agent Framework
After=network.target

[Service]
Type=simple
User=crewai
WorkingDirectory=/opt/crewai
ExecStart=/usr/local/bin/crewai server --port 8001
Environment="OPENAI_API_KEY_FILE=/etc/crewai/openai.key"
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable all services
sudo systemctl enable fleetops ollama crewai
sudo systemctl start fleetops ollama crewai

# Check status
sudo systemctl status fleetops
sudo systemctl status ollama
sudo systemctl status crewai
```

---

## 🚀 Cloud Function Deployment

### Serverless Agents

```javascript
// AWS Lambda: CrewAI Agent
const { Crew, Agent, Task } = require('crewai');

exports.handler = async (event) => {
    const { instructions, context } = JSON.parse(event.body);
    
    const agent = new Agent({
        role: 'Worker',
        goal: 'Execute tasks',
        backstory: 'Expert agent'
    });
    
    const task = new Task({
        description: instructions,
        agent: agent
    });
    
    const crew = new Crew({
        agents: [agent],
        tasks: [task]
    });
    
    const result = await crew.kickoff();
    
    return {
        statusCode: 200,
        body: JSON.stringify({
            status: 'success',
            output: result,
            requires_approval: true
        })
    };
};
```

```yaml
# serverless.yml
service: fleetops-agents

provider:
  name: aws
  runtime: nodejs18.x

functions:
  crewai:
    handler: handler.crewai
    events:
      - http:
          path: execute
          method: post
    environment:
      OPENAI_API_KEY: ${env:OPENAI_API_KEY}

  autogen:
    handler: handler.autogen
    events:
      - http:
          path: execute
          method: post
```

---

## 🔄 Mixed Deployment Example

### Real-World Setup

```yaml
# Real-world mixed deployment

# FleetOps: VPS (Hostinger)
fleetops:
  host: vps.yourdomain.com
  type: docker
  
# Personal Agents: Same VPS (lightweight)
openclaw:
  host: localhost:8080 (same VPS)
  type: docker
  
hermes:
  host: localhost:9090 (same VPS)
  type: docker

# Multi-Agent: Separate VPS (medium compute)
crewai:
  host: agents.internal:8001
  type: systemd service
  deploy: pip install crewai
  
autogen:
  host: agents.internal:8002
  type: systemd service
  deploy: pip install autogen

# GPU: Dedicated GPU server
ollama:
  host: gpu.internal:11434
  type: systemd service
  hardware: NVIDIA RTX 4090
  
vllm:
  host: gpu.internal:8013
  type: docker
  deploy: vllm/vllm-openai:latest

# IDE Agents: Developer machines
claude_code:
  host: dev-laptop-1
  type: CLI
  deploy: npm install -g @anthropic-ai/claude-code
  
aider:
  host: dev-laptop-2
  type: CLI
  deploy: pip install aider-chat

# Cloud: External APIs
devin:
  host: api.cognition.ai
  type: cloud API
  
copilot:
  host: api.github.com
  type: cloud API

# Serverless: AWS Lambda
langchain:
  host: lambda.amazonaws.com
  type: serverless
  deploy: serverless deploy
```

---

## 📊 Deployment Comparison

| Method | Ease | Scale | Cost | Best For |
|---|---|---|---|---|
| **Docker Compose** | ⭐⭐⭐ Easy | ⭐⭐ Local only | 💰 Low | Development |
| **Docker Swarm** | ⭐⭐ Medium | ⭐⭐⭐ Multi-node | 💰 Medium | Small production |
| **Kubernetes** | ⭐ Complex | ⭐⭐⭐⭐⭐ Enterprise | 💰💰💰 High | Large scale |
| **Systemd** | ⭐⭐⭐ Easy | ⭐⭐ Single server | 💰 Low | Simple production |
| **VPS (manual)** | ⭐⭐ Medium | ⭐⭐ Single server | 💰 Low | Budget production |
| **Cloud VMs** | ⭐⭐ Medium | ⭐⭐⭐ Auto-scale | 💰💰 Medium | Flexible scaling |
| **Serverless** | ⭐⭐⭐ Easy | ⭐⭐⭐⭐ Auto-scale | 💰 Pay/use | Sporadic tasks |
| **Hybrid** | ⭐⭐ Medium | ⭐⭐⭐⭐⭐ Unlimited | 💰💰💰 Variable | Real-world |

---

## ✅ Summary

**Can all agents be remote?**
✅ **YES** — FleetOps connects via URLs regardless of location

**Can they be Docker, npm, Python, CLI?**
✅ **YES** — All deployment methods supported

**Can they be mixed?**
✅ **YES** — Docker + npm + Python + CLI + Cloud all together

**FleetOps doesn't care HOW agents are deployed.**
It only cares that they expose an HTTP API (or CLI path).

---

*Deploy agents your way. FleetOps connects them all.*
