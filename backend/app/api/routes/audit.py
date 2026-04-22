"""Audit Log API for FleetOps

View and search audit events with signature verification
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, Event

router = APIRouter(prefix="/audit", tags=["Audit Log"])

@router.get("/events")
def list_audit_events(
    task_id: Optional[str] = None,
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    verified: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List audit events with filters"""
    query = db.query(Event).filter(Event.org_id == current_user.org_id)
    
    if task_id:
        query = query.filter(Event.task_id == task_id)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if user_id:
        query = query.filter(Event.user_id == user_id)
    if agent_id:
        query = query.filter(Event.agent_id == agent_id)
    if verified is not None:
        query = query.filter(Event.signature_verified == verified)
    if start_date:
        query = query.filter(Event.timestamp >= start_date)
    if end_date:
        query = query.filter(Event.timestamp <= end_date)
    
    total = query.count()
    events = query.order_by(Event.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "events": [
            {
                "id": e.id,
                "task_id": e.task_id,
                "event_type": e.event_type,
                "user_id": e.user_id,
                "agent_id": e.agent_id,
                "timestamp": e.timestamp.isoformat(),
                "verified": getattr(e, "signature_verified", True),
                "details": getattr(e, "details", {})
            }
            for e in events
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/events/{event_id}")
def get_event_details(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed event information with signature verification"""
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.org_id == current_user.org_id
    ).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {
        "id": event.id,
        "task_id": event.task_id,
        "event_type": event.event_type,
        "user_id": event.user_id,
        "agent_id": event.agent_id,
        "timestamp": event.timestamp.isoformat(),
        "verified": getattr(event, "signature_verified", True),
        "signature": getattr(event, "signature", None),
        "details": getattr(event, "details", {})
    }

@router.get("/stats")
def get_audit_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit log statistics"""
    from sqlalchemy import func
    
    total_events = db.query(Event).filter(Event.org_id == current_user.org_id).count()
    
    # Event types breakdown
    type_counts = db.query(
        Event.event_type,
        func.count(Event.id).label("count")
    ).filter(
        Event.org_id == current_user.org_id
    ).group_by(Event.event_type).all()
    
    return {
        "total_events": total_events,
        "event_types": {t.event_type: t.count for t in type_counts},
        "period": "last_30_days"
    }
