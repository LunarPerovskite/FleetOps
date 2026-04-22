"""Feedback Collection System for FleetOps

Collect in-app feedback, NPS scores, and feature requests
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

class FeedbackEntry(BaseModel):
    id: str
    user_id: str
    type: str  # "bug", "feature", "nps", "general"
    rating: Optional[int] = None  # 1-5 or 0-10 for NPS
    message: str
    category: Optional[str] = None
    screenshot_url: Optional[str] = None
    created_at: str
    status: str = "new"  # new, reviewing, in_progress, resolved, closed
    admin_notes: Optional[str] = None

class FeedbackService:
    """Collect and manage user feedback"""
    
    def __init__(self):
        # In production, store in database
        self._feedback: List[FeedbackEntry] = []
    
    def submit_feedback(self, user_id: str, type: str, message: str, 
                       rating: Optional[int] = None, category: Optional[str] = None,
                       screenshot_url: Optional[str] = None) -> FeedbackEntry:
        """Submit new feedback"""
        entry = FeedbackEntry(
            id=f"fb_{len(self._feedback) + 1}",
            user_id=user_id,
            type=type,
            message=message,
            rating=rating,
            category=category,
            screenshot_url=screenshot_url,
            created_at=datetime.utcnow().isoformat()
        )
        self._feedback.append(entry)
        return entry
    
    def get_feedback(self, type_filter: Optional[str] = None, 
                    status_filter: Optional[str] = None,
                    limit: int = 50) -> List[FeedbackEntry]:
        """Get feedback with optional filters"""
        results = self._feedback
        
        if type_filter:
            results = [f for f in results if f.type == type_filter]
        
        if status_filter:
            results = [f for f in results if f.status == status_filter]
        
        return sorted(results, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def update_status(self, feedback_id: str, status: str, admin_notes: Optional[str] = None) -> bool:
        """Update feedback status"""
        for entry in self._feedback:
            if entry.id == feedback_id:
                entry.status = status
                if admin_notes:
                    entry.admin_notes = admin_notes
                return True
        return False
    
    def get_nps_stats(self) -> Dict:
        """Calculate NPS statistics"""
        nps_responses = [f for f in self._feedback if f.type == "nps" and f.rating is not None]
        
        if not nps_responses:
            return {"nps": 0, "total": 0, "promoters": 0, "passives": 0, "detractors": 0}
        
        promoters = sum(1 for f in nps_responses if f.rating >= 9)
        passives = sum(1 for f in nps_responses if 7 <= f.rating <= 8)
        detractors = sum(1 for f in nps_responses if f.rating <= 6)
        total = len(nps_responses)
        
        nps_score = ((promoters - detractors) / total) * 100 if total > 0 else 0
        
        return {
            "nps": round(nps_score, 1),
            "total": total,
            "promoters": promoters,
            "passives": passives,
            "detractors": detractors,
            "promoter_percentage": round(promoters / total * 100, 1),
            "detractor_percentage": round(detractors / total * 100, 1)
        }
    
    def get_stats(self) -> Dict:
        """Get overall feedback statistics"""
        all_feedback = self._feedback
        
        return {
            "total": len(all_feedback),
            "by_type": {
                "bug": len([f for f in all_feedback if f.type == "bug"]),
                "feature": len([f for f in all_feedback if f.type == "feature"]),
                "nps": len([f for f in all_feedback if f.type == "nps"]),
                "general": len([f for f in all_feedback if f.type == "general"])
            },
            "by_status": {
                "new": len([f for f in all_feedback if f.status == "new"]),
                "reviewing": len([f for f in all_feedback if f.status == "reviewing"]),
                "in_progress": len([f for f in all_feedback if f.status == "in_progress"]),
                "resolved": len([f for f in all_feedback if f.status == "resolved"])
            },
            "nps": self.get_nps_stats()
        }

# Initialize service
feedback_service = FeedbackService()
