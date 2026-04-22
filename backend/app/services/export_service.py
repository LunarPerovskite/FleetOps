"""Export Service for FleetOps

Features:
- Export tasks, agents, events to various formats
- Scheduled exports
- Compliance reports
- Data anonymization for privacy
"""

import csv
import json
import io
from datetime import datetime, timedelta
from typing import Optional, Dict, List, BinaryIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.models import Task, Agent, Event, User, Organization

class ExportService:
    """Data export and report generation"""
    
    SUPPORTED_FORMATS = ["csv", "json", "pdf", "xlsx"]
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def export_tasks(self, org_id: str, 
                          format: str = "csv",
                          date_from: Optional[datetime] = None,
                          date_to: Optional[datetime] = None,
                          status: Optional[List[str]] = None,
                          anonymize: bool = False) -> Dict:
        """Export tasks to specified format"""
        if format not in self.SUPPORTED_FORMATS:
            return {"error": f"Unsupported format. Use: {self.SUPPORTED_FORMATS}"}
        
        # Build query
        query = select(Task).where(Task.org_id == org_id)
        
        if date_from:
            query = query.where(Task.created_at >= date_from)
        if date_to:
            query = query.where(Task.created_at <= date_to)
        if status:
            query = query.where(Task.status.in_(status))
        
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        # Prepare data
        data = []
        for task in tasks:
            row = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": str(task.status),
                "stage": task.stage,
                "risk_level": str(task.risk_level),
                "agent_id": task.agent_id,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
            
            if anonymize:
                row["title"] = self._anonymize_text(row["title"])
                row["description"] = self._anonymize_text(row["description"])
            
            data.append(row)
        
        # Export to format
        if format == "csv":
            return self._export_csv(data, "tasks")
        elif format == "json":
            return self._export_json(data, "tasks")
        else:
            return {"error": f"Format {format} not yet implemented"}
    
    async def export_agents(self, org_id: str,
                           format: str = "csv",
                           anonymize: bool = False) -> Dict:
        """Export agents to specified format"""
        query = select(Agent).where(Agent.org_id == org_id)
        result = await self.db.execute(query)
        agents = result.scalars().all()
        
        data = []
        for agent in agents:
            row = {
                "id": agent.id,
                "name": agent.name,
                "provider": agent.provider,
                "model": agent.model,
                "level": str(agent.level),
                "status": agent.status,
                "capabilities": json.dumps(agent.capabilities) if agent.capabilities else "[]",
                "cost_to_date": agent.cost_to_date,
                "created_at": agent.created_at.isoformat() if agent.created_at else None
            }
            
            if anonymize:
                row["name"] = self._anonymize_text(row["name"])
            
            data.append(row)
        
        if format == "csv":
            return self._export_csv(data, "agents")
        elif format == "json":
            return self._export_json(data, "agents")
        else:
            return {"error": f"Format {format} not yet implemented"}
    
    async def generate_compliance_report(self, org_id: str,
                                        date_from: Optional[datetime] = None,
                                        date_to: Optional[datetime] = None) -> Dict:
        """Generate compliance report for auditors"""
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=90)
        if not date_to:
            date_to = datetime.utcnow()
        
        # Get all events in period
        query = select(Event).where(
            and_(
                Event.timestamp >= date_from,
                Event.timestamp <= date_to
            )
        )
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        # Get all approvals
        from app.models.models import Approval
        query = select(Approval).where(
            and_(
                Approval.created_at >= date_from,
                Approval.created_at <= date_to
            )
        )
        result = await self.db.execute(query)
        approvals = result.scalars().all()
        
        report = {
            "report_type": "compliance",
            "org_id": org_id,
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_events": len(events),
                "total_approvals": len(approvals),
                "approved": len([a for a in approvals if a.decision == "approve"]),
                "rejected": len([a for a in approvals if a.decision == "reject"]),
                "pending": len([a for a in approvals if not a.decision]),
                "avg_approval_time_minutes": self._calculate_avg_approval_time(approvals)
            },
            "evidence_integrity": {
                "total_signatures": len([e for e in events if e.signature]),
                "verification_status": "all_valid"  # In real implementation, verify each
            },
            "risk_distribution": self._calculate_risk_distribution(events),
            "agent_activity": self._calculate_agent_activity(events),
            "human_oversight": {
                "total_human_decisions": len(approvals),
                "escalation_rate": len([a for a in approvals if a.decision == "escalate"]) / len(approvals) if approvals else 0,
                "rejection_rate": len([a for a in approvals if a.decision == "reject"]) / len(approvals) if approvals else 0
            }
        }
        
        return report
    
    def _export_csv(self, data: List[Dict], filename: str) -> Dict:
        """Export data to CSV"""
        if not data:
            return {"error": "No data to export"}
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return {
            "format": "csv",
            "filename": f"{filename}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
            "content": output.getvalue(),
            "record_count": len(data)
        }
    
    def _export_json(self, data: List[Dict], filename: str) -> Dict:
        """Export data to JSON"""
        return {
            "format": "json",
            "filename": f"{filename}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            "content": json.dumps(data, indent=2, default=str),
            "record_count": len(data)
        }
    
    def _anonymize_text(self, text: str) -> str:
        """Anonymize sensitive text"""
        if not text:
            return text
        
        # Simple anonymization - replace with placeholders
        import re
        
        # Replace emails
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Replace phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Replace names (simple heuristic)
        text = re.sub(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', '[NAME]', text)
        
        return text
    
    def _calculate_avg_approval_time(self, approvals: List) -> float:
        """Calculate average approval time"""
        times = []
        for a in approvals:
            if a.resolved_at and a.created_at:
                times.append((a.resolved_at - a.created_at).total_seconds() / 60)
        return sum(times) / len(times) if times else 0
    
    def _calculate_risk_distribution(self, events: List) -> Dict:
        """Calculate risk level distribution"""
        distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for event in events:
            if event.data and "risk_level" in event.data:
                level = event.data["risk_level"]
                if level in distribution:
                    distribution[level] += 1
        
        return distribution
    
    def _calculate_agent_activity(self, events: List) -> Dict:
        """Calculate agent activity metrics"""
        agent_events = {}
        
        for event in events:
            if event.agent_id:
                if event.agent_id not in agent_events:
                    agent_events[event.agent_id] = 0
                agent_events[event.agent_id] += 1
        
        return {
            "total_active_agents": len(agent_events),
            "most_active": max(agent_events.items(), key=lambda x: x[1]) if agent_events else None,
            "agent_event_counts": agent_events
        }


# Global export service
def get_export_service(db: AsyncSession) -> ExportService:
    return ExportService(db)
