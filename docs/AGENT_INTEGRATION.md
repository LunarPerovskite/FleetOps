# Integrating AI Agents into FleetOps

## Overview

FleetOps is designed to work with ANY AI agent that exposes an API or command-line interface. Whether it's OpenClaw, Hermes, Claude Code, GitHub Copilot, or a custom agent, the integration pattern is the same.

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  FleetOps    │────▶│  Agent       │────▶│  Human       │
│  Backend     │     │  Adapter     │     │  Approval    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                      │                    │
       └──────────────────────┴────────────────────┘
                          
              1. Task Created (with agent assigned)
              2. FleetOps calls agent via adapter
              3. Agent executes work
              4. FleetOps presents results to human
              5. Human approves/rejects/escalates
              6. FleetOps records evidence
```

## Integration Pattern

### Step 1: Create an Agent Adapter

Create a file in `backend/app/adapters/`:

```python
# backend/app/adapters/openclaw_adapter.py
"""OpenClaw integration for FleetOps

Connects FleetOps tasks to OpenClaw agent sessions
"""

import os
from typing import Optional, Dict, Any
import httpx

class OpenClawAdapter:
    """Adapter for OpenClaw agent"""
    
    def __init__(self):
        self.base_url = os.getenv("OPENCLAW_URL", "http://localhost:8080")
        self.api_key = os.getenv("OPENCLAW_API_KEY")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=300  # 5 minutes for long tasks
        )
    
    async def execute_task(self, task_id: str, instructions: str, 
                          context: Optional[Dict[str, Any]] = None) -> Dict:
        """Execute a task using OpenClaw
        
        Args:
            task_id: FleetOps task ID
            instructions: Natural language instructions
            context: Additional context (files, URLs, etc.)
        
        Returns:
            Dict with results, status, and evidence
        """
        try:
            response = await self.client.post(
                "/api/v1/execute",
                json={
                    "task_id": task_id,
                    "instructions": instructions,
                    "context": context or {},
                    "mode": "governed"  # Tells OpenClaw to wait for approval
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "output": result.get("output"),
                    "files_changed": result.get("files_changed", []),
                    "execution_log": result.get("log"),
                    "requires_approval": True  # Always require human approval
                }
            else:
                return {
                    "status": "error",
                    "error": f"OpenClaw error: {response.status_code}",
                    "details": response.text
                }
                
        except httpx.TimeoutException:
            return {
                "status": "timeout",
                "error": "Task exceeded 5-minute timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_status(self, execution_id: str) -> Dict:
        """Check execution status"""
        try:
            response = await self.client.get(f"/api/v1/execute/{execution_id}")
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel running execution"""
        try:
            response = await self.client.post(f"/api/v1/execute/{execution_id}/cancel")
            return response.status_code == 200
        except:
            return False
    
    async def approve_result(self, execution_id: str, approved: bool,
                          comments: Optional[str] = None) -> Dict:
        """Send approval decision back to OpenClaw
        
        This is the key integration - FleetOps human approval
        is communicated back to the agent
        """
        try:
            response = await self.client.post(
                f"/api/v1/execute/{execution_id}/approval",
                json={
                    "approved": approved,
                    "comments": comments,
                    "source": "fleetops"
                }
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Initialize adapter
openclaw_adapter = OpenClawAdapter()
```

### Step 2: Create a Service that Uses the Adapter

```python
# backend/app/services/openclaw_task_service.py
"""Task service for OpenClaw integration"""

from app.adapters.openclaw_adapter import openclaw_adapter
from app.services.task_service import task_service
from app.services.notification_service import notification_service
from typing import Dict

class OpenClawTaskService:
    """Execute FleetOps tasks through OpenClaw"""
    
    async def execute_task(self, task_id: str) -> Dict:
        """Execute a task using OpenClaw
        
        Flow:
        1. Get task details from FleetOps
        2. Send to OpenClaw for execution
        3. Wait for results (async)
        4. Create approval request in FleetOps
        5. Human reviews and approves
        6. Send approval back to OpenClaw
        """
        # 1. Get task
        task = await task_service.get_task(task_id)
        
        # 2. Build instructions from task
        instructions = f"""
        Task: {task.title}
        Description: {task.description}
        Risk Level: {task.risk_level}
        Priority: {task.priority}
        
        Please complete this task according to the governance framework.
        All changes will be reviewed by a human before being applied.
        """
        
        # 3. Execute via OpenClaw
        result = await openclaw_adapter.execute_task(
            task_id=task_id,
            instructions=instructions,
            context={
                "org_id": task.org_id,
                "agent_id": task.agent_id,
                "risk_level": task.risk_level
            }
        )
        
        if result["status"] == "success":
            # 4. Update task with results
            await task_service.update_task(
                task_id,
                {
                    "status": "reviewing",
                    "output": result["output"],
                    "files_changed": result.get("files_changed", [])
                }
            )
            
            # 5. Create approval request
            from app.services.approval_service import approval_service
            approval = await approval_service.create_approval(
                task_id=task_id,
                stage="review",
                agent_output=result["output"],
                files_changed=result.get("files_changed", [])
            )
            
            # 6. Notify human approvers
            await notification_service.send_approval_request(
                task_id=task_id,
                approval_id=approval.id,
                message=f"OpenClaw completed task: {task.title}. Please review."
            )
            
            return {
                "status": "awaiting_approval",
                "task_id": task_id,
                "approval_id": approval.id,
                "output_preview": result["output"][:500]  # First 500 chars
            }
        else:
            # Execution failed
            await task_service.update_task(
                task_id,
                {"status": "failed", "error": result.get("error")}
            )
            
            await notification_service.send_notification(
                task.org_id,
                f"Task {task.title} failed: {result.get('error')}"
            )
            
            return result

openclaw_task_service = OpenClawTaskService()
```

### Step 3: Add Route for Agent Execution

```python
# backend/app/api/routes/agent_execution.py
"""Routes for agent task execution"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.core.auth import get_current_user
from app.services.openclaw_task_service import openclaw_task_service
from app.services.task_service import task_service

router = APIRouter(prefix="/agent-execute", tags=["Agent Execution"])

@router.post("/execute/{task_id}")
async def execute_with_agent(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Execute a task using the assigned AI agent
    
    This is called by:
    - Frontend when user clicks "Execute with Agent"
    - Webhook from CI/CD pipeline
    - Scheduled job (cron)
    """
    task = await task_service.get_task(task_id)
    
    if task.org_id != current_user.org_id:
        raise HTTPException(403, "Not authorized")
    
    # Run execution in background so API responds immediately
    background_tasks.add_task(
        openclaw_task_service.execute_task,
        task_id
    )
    
    return {
        "message": "Task execution started",
        "task_id": task_id,
        "status": "executing",
        "check_status_at": f"/api/v1/tasks/{task_id}"
    }

@router.post("/approve/{approval_id}")
async def approve_agent_result(
    approval_id: str,
    decision: str,  # approve, reject, request_changes
    comments: str = None,
    current_user = Depends(get_current_user)
):
    """Human approves or rejects agent output
    
    This sends the decision back to the agent so it can:
    - Apply changes (if approved)
    - Retry with modifications (if rejected)
    - Escalate (if requested)
    """
    # ... approval logic ...
    
    # Send back to agent
    from app.adapters.openclaw_adapter import openclaw_adapter
    await openclaw_adapter.approve_result(
        execution_id=approval.execution_reference,
        approved=(decision == "approve"),
        comments=comments
    )
    
    return {"status": "success", "decision": decision}
```

### Step 4: Environment Variables

```bash
# .env
# OpenClaw Configuration
OPENCLAW_URL=http://localhost:8080
OPENCLAW_API_KEY=your-openclaw-api-key

# Hermes Configuration (if using Hermes)
HERMES_URL=http://localhost:9090
HERMES_API_KEY=your-hermes-api-key

# Generic Agent Configuration
AGENT_EXECUTION_TIMEOUT=300
AGENT_MAX_RETRIES=3
AGENT_REQUIRE_APPROVAL=true
```

### Step 5: Frontend Integration

```tsx
// frontend/src/components/AgentExecutionButton.tsx
import { useState } from 'react';
import { Bot, Loader, CheckCircle, AlertCircle } from 'lucide-react';
import { tasksAPI } from '../lib/api';
import { toast } from '../hooks/useToast';

export default function AgentExecutionButton({ taskId }: { taskId: string }) {
  const [status, setStatus] = useState('idle'); // idle, executing, completed, error

  const execute = async () => {
    setStatus('executing');
    try {
      const result = await tasksAPI.executeWithAgent(taskId);
      
      if (result.status === 'executing') {
        toast.success('Agent started working on this task');
        setStatus('executing');
        
        // Poll for status
        pollStatus(taskId);
      }
    } catch (err) {
      toast.error('Failed to start agent execution');
      setStatus('error');
    }
  };

  const pollStatus = async (id: string) => {
    const interval = setInterval(async () => {
      const task = await tasksAPI.get(id);
      
      if (task.status === 'reviewing') {
        clearInterval(interval);
        setStatus('completed');
        toast.success('Agent completed work! Review required.');
      } else if (task.status === 'failed') {
        clearInterval(interval);
        setStatus('error');
        toast.error('Agent execution failed');
      }
    }, 5000); // Check every 5 seconds
  };

  const statusConfig = {
    idle: { icon: Bot, text: 'Execute with Agent', class: 'bg-blue-600' },
    executing: { icon: Loader, text: 'Agent Working...', class: 'bg-yellow-600' },
    completed: { icon: CheckCircle, text: 'Review Results', class: 'bg-green-600' },
    error: { icon: AlertCircle, text: 'Retry', class: 'bg-red-600' }
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <button
      onClick={status === 'idle' || status === 'error' ? execute : undefined}
      disabled={status === 'executing'}
      className={`flex items-center gap-2 px-4 py-2 text-white rounded-lg transition-colors ${config.class} ${
        status === 'executing' ? 'opacity-75 cursor-not-allowed' : 'hover:opacity-90'
      }`}
    >
      <Icon className={`w-4 h-4 ${status === 'executing' ? 'animate-spin' : ''}`} />
      {config.text}
    </button>
  );
}
```

## Specific Agent Integrations

### OpenClaw Integration

OpenClaw is an autonomous agent framework. Integration points:

```python
# Adapter pattern for OpenClaw
class OpenClawAdapter(BaseAgentAdapter):
    async def execute(self, task: Task) -> ExecutionResult:
        # OpenClaw specific API calls
        session = await self.create_session(
            task_id=task.id,
            instructions=task.description
        )
        
        # OpenClaw works in a session with multiple steps
        while session.is_active:
            step = await session.next_step()
            
            # For each step, ask FleetOps for human approval
            approval = await self.request_step_approval(
                task_id=task.id,
                step_description=step.description,
                proposed_action=step.action
            )
            
            if approval.decision == 'approve':
                await session.approve_step(step.id)
            else:
                await session.reject_step(step.id, approval.comments)
        
        return session.final_result
```

### Hermes Integration

Hermes is a code generation agent:

```python
class HermesAdapter(BaseAgentAdapter):
    async def execute(self, task: Task) -> ExecutionResult:
        # Hermes generates code patches
        patch = await hermes.generate_patch(
            description=task.description,
            codebase_url=task.context.get('repo_url'),
            constraints={
                'max_files': 10,
                'max_lines_changed': 500,
                'tests_required': True
            }
        )
        
        # Send patch to FleetOps for review
        return ExecutionResult(
            status='awaiting_approval',
            output=patch.diff,
            files_changed=patch.files,
            requires_human_approval=True
        )
```

### GitHub Copilot Integration

Copilot is an IDE-integrated agent:

```python
class CopilotAdapter(BaseAgentAdapter):
    async def execute(self, task: Task) -> ExecutionResult:
        # Copilot works within IDE, so we send suggestions
        # rather than direct execution
        
        suggestions = await copilot.get_suggestions(
            file_path=task.context.get('file_path'),
            cursor_position=task.context.get('cursor_position'),
            language=task.context.get('language', 'python')
        )
        
        # Present suggestions in FleetOps for review
        return ExecutionResult(
            status='awaiting_approval',
            output=suggestions,
            type='suggestions',
            requires_human_approval=True
        )
```

## Webhook Integration (for CI/CD)

Trigger agent execution from external systems:

```python
# backend/app/api/routes/webhooks.py

@router.post("/github/pr")
async def github_pr_webhook(payload: dict):
    """GitHub PR webhook - triggers agent review"""
    
    if payload.get('action') == 'opened':
        # Create task for code review
        task = await task_service.create_task(
            title=f"Review PR #{payload['pull_request']['number']}",
            description=f"Review changes in {payload['pull_request']['title']}",
            agent_id='copilot',  # or 'openclaw'
            risk_level='medium',
            context={
                'pr_url': payload['pull_request']['html_url'],
                'diff_url': payload['pull_request']['diff_url'],
                'repo': payload['repository']['full_name']
            }
        )
        
        # Execute immediately
        await openclaw_task_service.execute_task(task.id)
```

## Configuration

Register adapters in `fleetops.yaml`:

```yaml
agents:
  openclaw:
    adapter: openclaw_adapter.OpenClawAdapter
    enabled: true
    config:
      url: ${OPENCLAW_URL}
      api_key: ${OPENCLAW_API_KEY}
      timeout: 300
    
  hermes:
    adapter: hermes_adapter.HermesAdapter
    enabled: true
    config:
      url: ${HERMES_URL}
      api_key: ${HERMES_API_KEY}
      max_files: 10
      
  copilot:
    adapter: copilot_adapter.CopilotAdapter
    enabled: true
    config:
      mode: suggestions  # vs direct_execution
      
default_agent: openclaw
```

## Summary

To add any agent:
1. Create adapter in `backend/app/adapters/`
2. Implement `execute()`, `get_status()`, `cancel()` methods
3. Register in `fleetops.yaml`
4. Add UI button in frontend
5. Set environment variables

FleetOps handles the rest: human approval, audit logging, evidence storage.

---

*Current integrations: Claude Code, Copilot, Cursor, Codex, Devin, v0*
*Easy to add: OpenClaw, Hermes, any agent with API*
