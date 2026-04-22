"""Onboarding progress tracking for FleetOps

Track and guide new users through setup
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.auth import verify_token

router = APIRouter()

class OnboardingStep(BaseModel):
    id: str
    title: str
    description: str
    completed: bool
    required: bool
    order: int

class OnboardingProgress(BaseModel):
    org_id: str
    steps: List[OnboardingStep]
    completed_count: int
    total_count: int
    is_complete: bool
    started_at: str
    completed_at: Optional[str]

# Default onboarding steps
DEFAULT_STEPS = [
    OnboardingStep(
        id="welcome",
        title="Welcome to FleetOps",
        description="Learn what FleetOps can do for your team",
        completed=False,
        required=True,
        order=1
    ),
    OnboardingStep(
        id="org_setup",
        title="Organization Setup",
        description="Configure your organization name and settings",
        completed=False,
        required=True,
        order=2
    ),
    OnboardingStep(
        id="providers",
        title="Connect Providers",
        description="Choose your authentication, database, and hosting providers",
        completed=False,
        required=True,
        order=3
    ),
    OnboardingStep(
        id="first_agent",
        title="Create Your First Agent",
        description="Set up an AI agent to start automating tasks",
        completed=False,
        required=True,
        order=4
    ),
    OnboardingStep(
        id="first_task",
        title="Create Your First Task",
        description="Create a task and see the approval workflow in action",
        completed=False,
        required=True,
        order=5
    ),
    OnboardingStep(
        id="team_invite",
        title="Invite Your Team",
        description="Add team members to collaborate",
        completed=False,
        required=False,
        order=6
    ),
    OnboardingStep(
        id="customize",
        title="Customize Hierarchies",
        description="Set up your human and agent hierarchies",
        completed=False,
        required=False,
        order=7
    ),
]

# In-memory store (replace with database in production)
_onboarding_progress: dict = {}

@router.get("/onboarding/progress")
def get_progress(db: Session = Depends(get_db), user=Depends(verify_token)):
    """Get onboarding progress for current organization"""
    org_id = user.get("org_id", "default")
    
    if org_id not in _onboarding_progress:
        _onboarding_progress[org_id] = {
            "org_id": org_id,
            "steps": [step.dict() for step in DEFAULT_STEPS],
            "completed_count": 0,
            "total_count": len(DEFAULT_STEPS),
            "is_complete": False,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }
    
    return _onboarding_progress[org_id]

@router.post("/onboarding/steps/{step_id}/complete")
def complete_step(
    step_id: str,
    db: Session = Depends(get_db),
    user=Depends(verify_token)
):
    """Mark an onboarding step as complete"""
    org_id = user.get("org_id", "default")
    
    if org_id not in _onboarding_progress:
        get_progress(db, user)
    
    progress = _onboarding_progress[org_id]
    
    # Find and mark step as complete
    for step in progress["steps"]:
        if step["id"] == step_id:
            step["completed"] = True
            step["completed_at"] = datetime.utcnow().isoformat()
            break
    
    # Recalculate progress
    completed = sum(1 for s in progress["steps"] if s["completed"])
    progress["completed_count"] = completed
    
    # Check if all required steps are complete
    required_steps = [s for s in progress["steps"] if s["required"]]
    required_completed = sum(1 for s in required_steps if s["completed"])
    progress["is_complete"] = required_completed == len(required_steps)
    
    if progress["is_complete"] and not progress["completed_at"]:
        progress["completed_at"] = datetime.utcnow().isoformat()
    
    return progress

@router.post("/onboarding/steps/{step_id}/skip")
def skip_step(
    step_id: str,
    db: Session = Depends(get_db),
    user=Depends(verify_token)
):
    """Skip an optional onboarding step"""
    org_id = user.get("org_id", "default")
    
    if org_id not in _onboarding_progress:
        get_progress(db, user)
    
    progress = _onboarding_progress[org_id]
    
    for step in progress["steps"]:
        if step["id"] == step_id and not step["required"]:
            step["completed"] = True
            step["skipped"] = True
            break
    
    # Recalculate
    completed = sum(1 for s in progress["steps"] if s["completed"])
    progress["completed_count"] = completed
    
    return progress

@router.post("/onboarding/reset")
def reset_progress(
    db: Session = Depends(get_db),
    user=Depends(verify_token)
):
    """Reset onboarding progress (for testing)"""
    org_id = user.get("org_id", "default")
    
    if org_id in _onboarding_progress:
        del _onboarding_progress[org_id]
    
    return get_progress(db, user)

@router.get("/onboarding/status")
def get_status(user=Depends(verify_token)):
    """Quick check if onboarding is complete"""
    org_id = user.get("org_id", "default")
    
    if org_id not in _onboarding_progress:
        return {"is_complete": False, "needs_onboarding": True}
    
    progress = _onboarding_progress[org_id]
    return {
        "is_complete": progress["is_complete"],
        "needs_onboarding": not progress["is_complete"],
        "progress_percent": (progress["completed_count"] / progress["total_count"]) * 100
    }
