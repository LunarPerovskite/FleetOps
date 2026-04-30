"""Multi-Agent Orchestration API Routes

Endpoints for cross-agent workflows:
- Sequential pipelines
- Parallel execution
- Agent debates
- Consensus building
- Load balancing
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional

from app.api.routes.auth import get_current_user
from app.models.models import User
from app.services.multi_agent_orchestrator import multi_agent_orchestrator

router = APIRouter(prefix="/multi-agent", tags=["Multi-Agent Orchestration"])

# ═══════════════════════════════════════
# SEQUENTIAL PIPELINE
# ═══════════════════════════════════════

@router.post("/pipeline")
async def execute_pipeline(
    pipeline_id: str,
    steps: List[Dict[str, Any]],
    require_approval_between_steps: bool = True,
    stop_on_failure: bool = True,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """Execute a sequential pipeline of agents
    
    Each step's output becomes the next step's input.
    Human approval between steps (optional).
    
    Example:
    ```json
    {
        "pipeline_id": "build_feature_123",
        "steps": [
            {
                "agent": "crewai",
                "name": "research",
                "task": "Research best practices for authentication"
            },
            {
                "agent": "openclaw",
                "name": "implement",
                "task": "Implement JWT authentication",
                "depends_on": ["research"]
            },
            {
                "agent": "aider",
                "name": "test",
                "task": "Write tests",
                "depends_on": ["implement"]
            }
        ]
    }
    ```
    """
    try:
        # Run in background for long pipelines
        if background_tasks:
            background_tasks.add_task(
                multi_agent_orchestrator.sequential_pipeline,
                pipeline_id=pipeline_id,
                steps=steps,
                org_id=current_user.org_id,
                require_approval_between_steps=require_approval_between_steps,
                stop_on_failure=stop_on_failure
            )
            
            return {
                "status": "started",
                "pipeline_id": pipeline_id,
                "total_steps": len(steps),
                "message": "Pipeline started in background",
                "check_status_at": f"/api/v1/multi-agent/pipeline/{pipeline_id}/status"
            }
        
        else:
            # Run synchronously (for short pipelines)
            result = await multi_agent_orchestrator.sequential_pipeline(
                pipeline_id=pipeline_id,
                steps=steps,
                org_id=current_user.org_id,
                require_approval_between_steps=require_approval_between_steps,
                stop_on_failure=stop_on_failure
            )
            
            return result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pipeline/{pipeline_id}/status")
async def get_pipeline_status(
    pipeline_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get pipeline execution status"""
    # In production, query database for pipeline status
    return {
        "pipeline_id": pipeline_id,
        "status": "running",  # or completed, failed
        "message": "Status tracking not yet implemented"
    }

# ═══════════════════════════════════════
# PARALLEL EXECUTION
# ═══════════════════════════════════════

@router.post("/parallel")
async def execute_parallel(
    jobs: List[Dict[str, Any]],
    max_concurrent: int = 3,
    require_all_success: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Execute multiple agents in parallel
    
    Example:
    ```json
    {
        "jobs": [
            {"agent": "openclaw", "task": "Write backend", "name": "backend"},
            {"agent": "crewai", "task": "Write frontend", "name": "frontend"},
            {"agent": "hermes", "task": "Write docs", "name": "docs"}
        ],
        "max_concurrent": 3
    }
    ```
    """
    try:
        result = await multi_agent_orchestrator.parallel_execute(
            jobs=jobs,
            org_id=current_user.org_id,
            max_concurrent=max_concurrent,
            require_all_success=require_all_success
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# AGENT DEBATE
# ═══════════════════════════════════════

@router.post("/debate")
async def agent_debate(
    topic: str,
    agents: List[str],
    rounds: int = 1,
    require_consensus: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Multiple agents debate a topic
    
    Each agent provides perspective. Human selects winner.
    
    Example:
    ```json
    {
        "topic": "Should we use PostgreSQL or MongoDB for user data?",
        "agents": ["openclaw", "crewai", "autogen"],
        "rounds": 2
    }
    ```
    """
    try:
        result = await multi_agent_orchestrator.agent_debate(
            topic=topic,
            agents=agents,
            org_id=current_user.org_id,
            rounds=rounds,
            require_consensus=require_consensus
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# CONSENSUS BUILDING
# ═══════════════════════════════════════

@router.post("/consensus")
async def consensus_building(
    proposal: str,
    agents: List[str],
    threshold: float = 0.7,
    max_rounds: int = 3,
    current_user: User = Depends(get_current_user)
):
    """Agents must reach consensus on a proposal
    
    Agents review and approve/reject. If no consensus, agents discuss.
    
    Example:
    ```json
    {
        "proposal": "Deploy new authentication system to production",
        "agents": ["openclaw", "crewai", "autogen"],
        "threshold": 0.7
    }
    ```
    """
    try:
        result = await multi_agent_orchestrator.consensus_building(
            proposal=proposal,
            agents=agents,
            org_id=current_user.org_id,
            threshold=threshold,
            max_rounds=max_rounds
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# LOAD BALANCING
# ═══════════════════════════════════════

@router.post("/load-balance")
async def load_balanced_execute(
    tasks: List[Dict[str, Any]],
    available_agents: List[str],
    strategy: str = "round_robin",
    current_user: User = Depends(get_current_user)
):
    """Distribute tasks across agents
    
    Strategies: round_robin, least_busy, capability, random
    
    Example:
    ```json
    {
        "tasks": [
            {"task": "Analyze data", "name": "analysis"},
            {"task": "Generate report", "name": "report"}
        ],
        "available_agents": ["openclaw", "crewai", "hermes"],
        "strategy": "least_busy"
    }
    ```
    """
    try:
        result = await multi_agent_orchestrator.load_balanced_execute(
            tasks=tasks,
            available_agents=available_agents,
            org_id=current_user.org_id,
            strategy=strategy
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# CROSS-AGENT WORKFLOW
# ═══════════════════════════════════════

@router.post("/workflow")
async def cross_agent_workflow(
    workflow_id: str,
    workflow_definition: Dict[str, Any],
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """Execute a complex cross-agent workflow
    
    Example workflow:
    ```json
    {
        "workflow_id": "build_feature_1",
        "workflow_definition": {
            "name": "Build Feature",
            "steps": [
                {
                    "id": "design",
                    "agent": "crewai",
                    "task": "Design feature",
                    "next": ["implement", "document"]
                },
                {
                    "id": "implement",
                    "agent": "openclaw",
                    "task": "Implement",
                    "depends_on": ["design"],
                    "next": ["test"]
                },
                {
                    "id": "document",
                    "agent": "hermes",
                    "task": "Document",
                    "depends_on": ["design"],
                    "next": []
                },
                {
                    "id": "test",
                    "agent": "autogen",
                    "task": "Test",
                    "depends_on": ["implement"],
                    "next": []
                }
            ]
        }
    }
    ```
    """
    try:
        if background_tasks:
            background_tasks.add_task(
                multi_agent_orchestrator.cross_agent_workflow,
                workflow_id=workflow_id,
                workflow_definition=workflow_definition,
                org_id=current_user.org_id
            )
            
            return {
                "status": "started",
                "workflow_id": workflow_id,
                "message": "Workflow started in background"
            }
        
        else:
            result = await multi_agent_orchestrator.cross_agent_workflow(
                workflow_id=workflow_id,
                workflow_definition=workflow_definition,
                org_id=current_user.org_id
            )
            
            return result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# EXAMPLES AND TEMPLATES
# ═══════════════════════════════════════

@router.get("/templates")
async def list_workflow_templates(
    current_user: User = Depends(get_current_user)
):
    """List available workflow templates"""
    return {
        "templates": [
            {
                "id": "software_development",
                "name": "Software Development Pipeline",
                "description": "Research → Design → Implement → Test → Deploy",
                "agents_used": ["crewai", "openclaw", "aider", "devin"],
                "estimated_time": "2-4 hours"
            },
            {
                "id": "data_analysis",
                "name": "Data Analysis Workflow",
                "description": "Collect → Clean → Analyze → Visualize → Report",
                "agents_used": ["crewai", "taskweaver", "hermes"],
                "estimated_time": "1-2 hours"
            },
            {
                "id": "security_audit",
                "name": "Security Audit",
                "description": "Scan → Analyze → Report → Fix → Verify",
                "agents_used": ["openclaw", "autogen", "superagi"],
                "estimated_time": "3-5 hours"
            },
            {
                "id": "agent_debate",
                "name": "Architecture Decision",
                "description": "Multiple agents debate best approach",
                "agents_used": ["openclaw", "crewai", "autogen"],
                "estimated_time": "30-60 minutes"
            },
            {
                "id": "code_review",
                "name": "Comprehensive Code Review",
                "description": "Multiple agents review from different perspectives",
                "agents_used": ["copilot", "cody", "openclaw"],
                "estimated_time": "15-30 minutes"
            }
        ]
    }

@router.get("/templates/{template_id}")
async def get_workflow_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific workflow template"""
    templates = {
        "software_development": {
            "name": "Software Development Pipeline",
            "steps": [
                {
                    "id": "research",
                    "agent": "crewai",
                    "task": "Research requirements and best practices",
                    "next": ["design"]
                },
                {
                    "id": "design",
                    "agent": "openclaw",
                    "task": "Design architecture and data models",
                    "depends_on": ["research"],
                    "next": ["implement"]
                },
                {
                    "id": "implement",
                    "agent": "aider",
                    "task": "Implement the code",
                    "depends_on": ["design"],
                    "next": ["test"]
                },
                {
                    "id": "test",
                    "agent": "autogen",
                    "task": "Write and run tests",
                    "depends_on": ["implement"],
                    "next": ["review"]
                },
                {
                    "id": "review",
                    "agent": "copilot",
                    "task": "Review code quality",
                    "depends_on": ["test"],
                    "next": ["deploy"]
                },
                {
                    "id": "deploy",
                    "agent": "devin",
                    "task": "Deploy to production",
                    "depends_on": ["review"],
                    "next": [],
                    "requires_approval": True
                }
            ]
        },
        "data_analysis": {
            "name": "Data Analysis Workflow",
            "steps": [
                {
                    "id": "collect",
                    "agent": "crewai",
                    "task": "Collect data from sources",
                    "next": ["clean"]
                },
                {
                    "id": "clean",
                    "agent": "taskweaver",
                    "task": "Clean and preprocess data",
                    "depends_on": ["collect"],
                    "next": ["analyze"]
                },
                {
                    "id": "analyze",
                    "agent": "taskweaver",
                    "task": "Analyze patterns and insights",
                    "depends_on": ["clean"],
                    "next": ["report"]
                },
                {
                    "id": "report",
                    "agent": "hermes",
                    "task": "Generate comprehensive report",
                    "depends_on": ["analyze"],
                    "next": []
                }
            ]
        }
    }
    
    template = templates.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template
