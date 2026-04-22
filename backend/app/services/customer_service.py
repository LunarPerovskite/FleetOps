"""Customer Service Management for FleetOps

Features:
- Conversation routing to right agent based on expertise/workload
- Cross-channel context (WhatsApp -> Email -> Web)
- SLA monitoring and breach alerts
- Customer profiles and history
- Queue management with prioritization
- Sentiment tracking over time
- Handoff notes for human escalation
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.models import (
    Agent, Organization, Team, User, Task, Event, 
    LLMUsage, Approval
)

class CustomerProfile:
    """Customer profile with interaction history"""
    def __init__(self, customer_id: str, org_id: str):
        self.customer_id = customer_id
        self.org_id = org_id
        self.channels: List[str] = []
        self.interactions: List[Dict] = []
        self.sentiment_history: List[Dict] = []
        self.tags: List[str] = []
        self.vip: bool = False
        self.language: str = "en"
        self.created_at: datetime = datetime.utcnow()
        self.last_interaction: Optional[datetime] = None
        self.total_conversations: int = 0
        self.resolution_rate: float = 0.0
        self.avg_response_time: float = 0.0

class ConversationContext:
    """Cross-channel conversation context"""
    def __init__(self, conversation_id: str, customer_id: str):
        self.conversation_id = conversation_id
        self.customer_id = customer_id
        self.messages: List[Dict] = []
        self.channel_history: List[str] = []
        self.current_channel: str = None
        self.agent_id: Optional[str] = None
        self.human_id: Optional[str] = None
        self.status: str = "active"
        self.priority: int = 0  # 0-100
        self.created_at: datetime = datetime.utcnow()
        self.last_message_at: datetime = datetime.utcnow()
        self.sla_deadline: Optional[datetime] = None
        self.escalation_count: int = 0

class SLAMonitor:
    """SLA monitoring and breach detection"""
    def __init__(self):
        self.rules = {
            "critical": {"first_response": 5, "resolution": 30},
            "high": {"first_response": 15, "resolution": 60},
            "medium": {"first_response": 60, "resolution": 240},
            "low": {"first_response": 240, "resolution": 1440},
            "vip": {"first_response": 2, "resolution": 15}  # VIP override
        }
    
    def get_sla(self, priority: str, is_vip: bool = False) -> Dict:
        """Get SLA times in minutes"""
        if is_vip:
            return self.rules["vip"]
        return self.rules.get(priority, self.rules["medium"])
    
    def check_breach(self, created_at: datetime, priority: str, 
                     is_vip: bool = False, now: Optional[datetime] = None) -> Dict:
        """Check if SLA is breached"""
        if now is None:
            now = datetime.utcnow()
        
        sla = self.get_sla(priority, is_vip)
        elapsed = (now - created_at).total_seconds() / 60  # minutes
        
        first_response_breach = elapsed > sla["first_response"]
        resolution_breach = elapsed > sla["resolution"]
        
        return {
            "breached": first_response_breach or resolution_breach,
            "first_response_breach": first_response_breach,
            "resolution_breach": resolution_breach,
            "elapsed_minutes": elapsed,
            "sla_minutes": sla,
            "remaining_first_response": max(0, sla["first_response"] - elapsed),
            "remaining_resolution": max(0, sla["resolution"] - elapsed)
        }

class CustomerServiceManager:
    """Main customer service management class"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sla_monitor = SLAMonitor()
        self.profiles: Dict[str, CustomerProfile] = {}
        self.conversations: Dict[str, ConversationContext] = {}
        self.agent_queues: Dict[str, List[str]] = {}  # agent_id -> conversation_ids
    
    async def get_or_create_profile(self, customer_id: str, org_id: str,
                                     channel: str = None) -> CustomerProfile:
        """Get existing customer profile or create new one"""
        key = f"{org_id}:{customer_id}"
        if key not in self.profiles:
            profile = CustomerProfile(customer_id, org_id)
            if channel:
                profile.channels.append(channel)
            self.profiles[key] = profile
        else:
            profile = self.profiles[key]
            if channel and channel not in profile.channels:
                profile.channels.append(channel)
        
        return profile
    
    async def route_conversation(self, conversation_id: str, 
                                  customer_id: str, org_id: str,
                                  channel: str, message: str,
                                  sentiment_score: float = 0.5) -> Dict:
        """Route conversation to best agent based on expertise and workload"""
        # Get customer profile
        profile = await self.get_or_create_profile(customer_id, org_id, channel)
        profile.total_conversations += 1
        profile.last_interaction = datetime.utcnow()
        
        # Determine priority
        priority = self._calculate_priority(profile, sentiment_score, message)
        
        # Create or get conversation
        if conversation_id not in self.conversations:
            conv = ConversationContext(conversation_id, customer_id)
            conv.current_channel = channel
            conv.priority = priority
            conv.sla_deadline = datetime.utcnow() + timedelta(
                minutes=self.sla_monitor.get_sla(
                    "high" if priority > 70 else "medium",
                    profile.vip
                )["first_response"]
            )
            self.conversations[conversation_id] = conv
        else:
            conv = self.conversations[conversation_id]
            conv.messages.append({
                "channel": channel,
                "direction": "inbound",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            conv.last_message_at = datetime.utcnow()
        
        # Find best agent
        agent = await self._find_best_agent(org_id, channel, priority)
        
        if agent:
            conv.agent_id = agent["id"]
            
            # Add to agent queue
            if agent["id"] not in self.agent_queues:
                self.agent_queues[agent["id"]] = []
            if conversation_id not in self.agent_queues[agent["id"]]:
                self.agent_queues[agent["id"]].append(conversation_id)
            
            return {
                "conversation_id": conversation_id,
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "priority": priority,
                "sla_deadline": conv.sla_deadline.isoformat(),
                "queue_position": len(self.agent_queues[agent["id"]]),
                "routed": True
            }
        
        # No agent available - add to general queue
        return {
            "conversation_id": conversation_id,
            "agent_id": None,
            "priority": priority,
            "sla_deadline": conv.sla_deadline.isoformat(),
            "queue_position": -1,
            "routed": False,
            "message": "No agents available, added to queue"
        }
    
    def _calculate_priority(self, profile: CustomerProfile, 
                           sentiment_score: float, message: str) -> int:
        """Calculate conversation priority (0-100)"""
        priority = 0
        
        # VIP boost
        if profile.vip:
            priority += 40
        
        # Sentiment (lower = more urgent)
        if sentiment_score < 0.2:
            priority += 30
        elif sentiment_score < 0.4:
            priority += 15
        
        # Keyword urgency
        urgent_keywords = ["urgent", "asap", "emergency", "angry", "frustrated",
                          "cancel", "refund", "complaint", "lawsuit", "legal"]
        if any(kw in message.lower() for kw in urgent_keywords):
            priority += 20
        
        # Repeat customer (negative - might be frustrated)
        if profile.total_conversations > 5:
            priority += 10
        
        return min(100, priority)
    
    async def _find_best_agent(self, org_id: str, channel: str, 
                               priority: int) -> Optional[Dict]:
        """Find best available agent for this conversation"""
        # Query active agents with customer service capability
        result = await self.db.execute(
            select(Agent).where(
                and_(
                    Agent.org_id == org_id,
                    Agent.status == "active",
                    Agent.capabilities.contains(["customer_service"])
                )
            )
        )
        agents = result.scalars().all()
        
        if not agents:
            return None
        
        # Score each agent
        best_agent = None
        best_score = -1
        
        for agent in agents:
            score = 0
            
            # Prefer agents with channel-specific capability
            if channel in (agent.capabilities or []):
                score += 20
            
            # Prefer less busy agents
            queue_length = len(self.agent_queues.get(agent.id, []))
            score -= queue_length * 5
            
            # Prefer higher-level agents for high priority
            if priority > 50 and agent.level in ["senior", "lead"]:
                score += 15
            
            # Prefer specialist agents
            if "specialist" in (agent.capabilities or []):
                score += 10
            
            if score > best_score:
                best_score = score
                best_agent = {
                    "id": agent.id,
                    "name": agent.name,
                    "level": agent.level,
                    "queue_length": queue_length
                }
        
        return best_agent
    
    async def check_sla_breaches(self, org_id: str) -> List[Dict]:
        """Check all active conversations for SLA breaches"""
        breaches = []
        
        for conv_id, conv in self.conversations.items():
            if conv.status != "active":
                continue
            
            profile = await self.get_or_create_profile(
                conv.customer_id, org_id
            )
            
            priority = "high" if conv.priority > 70 else "medium"
            check = self.sla_monitor.check_breach(
                conv.created_at, priority, profile.vip
            )
            
            if check["breached"]:
                breaches.append({
                    "conversation_id": conv_id,
                    "customer_id": conv.customer_id,
                    "agent_id": conv.agent_id,
                    "breach_type": "first_response" if check["first_response_breach"] else "resolution",
                    "elapsed_minutes": check["elapsed_minutes"],
                    "priority": conv.priority,
                    "channel": conv.current_channel
                })
        
        return breaches
    
    async def generate_handoff_notes(self, conversation_id: str) -> Dict:
        """Generate handoff notes for human escalation"""
        if conversation_id not in self.conversations:
            return {"error": "Conversation not found"}
        
        conv = self.conversations[conversation_id]
        profile = await self.get_or_create_profile(
            conv.customer_id, "unknown"
        )
        
        # Get last 10 messages
        recent_messages = conv.messages[-10:] if len(conv.messages) > 10 else conv.messages
        
        # Calculate sentiment trend
        sentiment_trend = "stable"
        if len(profile.sentiment_history) >= 2:
            recent = profile.sentiment_history[-3:]
            scores = [s["score"] for s in recent]
            if scores[-1] < scores[0]:
                sentiment_trend = "declining"
            elif scores[-1] > scores[0]:
                sentiment_trend = "improving"
        
        return {
            "conversation_id": conversation_id,
            "customer_id": conv.customer_id,
            "channels_used": conv.channel_history,
            "current_channel": conv.current_channel,
            "priority": conv.priority,
            "escalation_count": conv.escalation_count,
            "total_messages": len(conv.messages),
            "conversation_duration_minutes": (
                datetime.utcnow() - conv.created_at
            ).total_seconds() / 60,
            "sentiment_trend": sentiment_trend,
            "customer_summary": {
                "total_conversations": profile.total_conversations,
                "is_vip": profile.vip,
                "tags": profile.tags,
                "channels": profile.channels
            },
            "recent_messages": [
                {
                    "channel": m["channel"],
                    "direction": m["direction"],
                    "content": m["content"][:200] + "..." if len(m["content"]) > 200 else m["content"],
                    "timestamp": m["timestamp"]
                }
                for m in recent_messages
            ],
            "suggested_actions": self._suggest_actions(conv, profile)
        }
    
    def _suggest_actions(self, conv: ConversationContext, 
                        profile: CustomerProfile) -> List[str]:
        """Suggest actions based on conversation context"""
        actions = []
        
        if conv.priority > 70:
            actions.append("Escalate to senior agent immediately")
        
        if profile.vip:
            actions.append("VIP customer - prioritize response")
        
        if conv.escalation_count > 2:
            actions.append("Multiple escalations - consider manager involvement")
        
        if "refund" in str(conv.messages).lower():
            actions.append("Refund request - verify policy before proceeding")
        
        if "cancel" in str(conv.messages).lower():
            actions.append("Cancellation risk - retention offer may be appropriate")
        
        return actions
    
    async def get_queue_stats(self, org_id: str) -> Dict:
        """Get customer service queue statistics"""
        total_active = len([c for c in self.conversations.values() if c.status == "active"])
        total_pending = len([c for c in self.conversations.values() if c.status == "pending"])
        
        # Count by priority
        priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for conv in self.conversations.values():
            if conv.priority >= 80:
                priority_counts["critical"] += 1
            elif conv.priority >= 50:
                priority_counts["high"] += 1
            elif conv.priority >= 20:
                priority_counts["medium"] += 1
            else:
                priority_counts["low"] += 1
        
        # Count by channel
        channel_counts = {}
        for conv in self.conversations.values():
            ch = conv.current_channel
            channel_counts[ch] = channel_counts.get(ch, 0) + 1
        
        # SLA breaches
        breaches = await self.check_sla_breaches(org_id)
        
        return {
            "total_conversations": total_active + total_pending,
            "active": total_active,
            "pending": total_pending,
            "by_priority": priority_counts,
            "by_channel": channel_counts,
            "sla_breaches": len(breaches),
            "breach_details": breaches[:5],  # Top 5
            "agent_utilization": {
                agent_id: len(queue)
                for agent_id, queue in self.agent_queues.items()
            }
        }
