"""Database Seeder for FleetOps Demo

Populates the database with sample data for testing/demos
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Organization, Team, User, Agent, Task, Event, Approval
from app.core.auth import hash_password

class DemoSeeder:
    """Seed database with demo data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def seed(self):
        """Seed all demo data"""
        print("🌱 Seeding demo data...")
        
        # Create organization
        org = Organization(
            id="org_demo",
            name="Acme Corporation",
            tier="pro",
            created_at=datetime.utcnow()
        )
        self.db.add(org)
        
        # Create team
        team = Team(
            id="team_demo",
            name="Engineering",
            org_id="org_demo",
            created_at=datetime.utcnow()
        )
        self.db.add(team)
        
        # Create users
        users = [
            User(id="user_exec", email="ceo@acme.com", name="CEO", role="executive", org_id="org_demo", password_hash=hash_password("demo123")),
            User(id="user_dir", email="director@acme.com", name="Director", role="director", org_id="org_demo", password_hash=hash_password("demo123")),
            User(id="user_op", email="operator@acme.com", name="Operator", role="operator", org_id="org_demo", password_hash=hash_password("demo123")),
        ]
        for user in users:
            self.db.add(user)
        
        # Create agents
        agents = [
            Agent(id="agent_1", name="Claude Code", provider="anthropic", model="claude-3-sonnet", level="senior", capabilities=["coding", "review"], org_id="org_demo", status="active"),
            Agent(id="agent_2", name="GitHub Copilot", provider="github", model="gpt-4", level="junior", capabilities=["coding", "analysis"], org_id="org_demo", status="active"),
            Agent(id="agent_3", name="Data Analyst", provider="openai", model="gpt-4", level="specialist", capabilities=["analysis", "reporting"], org_id="org_demo", status="active"),
        ]
        for agent in agents:
            self.db.add(agent)
        
        # Create tasks
        tasks = [
            Task(id="task_1", title="Review Q3 Report", description="Analyze quarterly financial data", status="completed", risk_level="medium", stage="reviewing", agent_id="agent_3", org_id="org_demo", created_at=datetime.utcnow() - timedelta(days=5)),
            Task(id="task_2", title="Deploy API v2", description="Update production API", status="executing", risk_level="high", stage="execution", agent_id="agent_1", org_id="org_demo", created_at=datetime.utcnow() - timedelta(days=2)),
            Task(id="task_3", title="Code Review", description="Review pull request #234", status="planning", risk_level="low", stage="planning", agent_id="agent_2", org_id="org_demo", created_at=datetime.utcnow() - timedelta(hours=4)),
        ]
        for task in tasks:
            self.db.add(task)
        
        # Create approvals
        approvals = [
            Approval(id="approval_1", task_id="task_2", human_id="user_dir", stage="execution", decision="pending", comments="", created_at=datetime.utcnow() - timedelta(days=1)),
        ]
        for approval in approvals:
            self.db.add(approval)
        
        # Create events
        events = [
            Event(id="event_1", task_id="task_1", event_type="task_created", user_id="user_op", timestamp=datetime.utcnow() - timedelta(days=5)),
            Event(id="event_2", task_id="task_1", event_type="task_completed", agent_id="agent_3", timestamp=datetime.utcnow() - timedelta(days=3)),
        ]
        for event in events:
            self.db.add(event)
        
        # Commit
        self.db.commit()
        print("✅ Demo data seeded successfully!")
        print(f"   Organization: {org.name}")
        print(f"   Users: {len(users)}")
        print(f"   Agents: {len(agents)}")
        print(f"   Tasks: {len(tasks)}")
        print(f"   Approvals: {len(approvals)}")
        print(f"   Events: {len(events)}")

async def run_seeder():
    """Run the seeder"""
    db = next(get_db())
    seeder = DemoSeeder(db)
    await seeder.seed()

if __name__ == "__main__":
    asyncio.run(run_seeder())
