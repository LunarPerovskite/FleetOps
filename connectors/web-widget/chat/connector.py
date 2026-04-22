"""Web Chat Widget Connector for FleetOps

Embeddable chat widget for websites with human escalation.
"""

import asyncio
from typing import Optional
from connectors.base import FleetOpsConnector, AgentConfig, AgentMode, AgentType

class WebChatConnector(FleetOpsConnector):
    """Web chat widget with human escalation"""
    
    PROVIDER = "web"
    DEFAULT_MODEL = "gpt-4.1"
    
    def __init__(self, api_key: str, fleetops_url: str,
                 website_id: str, name: str = "Web Chat",
                 level: str = "senior", parent_agent_id: Optional[str] = None):
        config = AgentConfig(
            name=name, provider=self.PROVIDER, model=self.DEFAULT_MODEL,
            mode=AgentMode.CLOUD, agent_type=AgentType.CHAT,
            capabilities=["chat", "escalate", "ticket", "faq", "lead_capture"],
            level=level, parent_agent_id=parent_agent_id,
            metadata={"website_id": website_id, "channels": ["web"]}
        )
        super().__init__(api_key, fleetops_url, config)
        self.website_id = website_id
        self.sessions: dict = {}
    
    async def handle_chat_message(self, session_id: str, message: str, 
                                  visitor_data: dict = None):
        """Handle incoming web chat message"""
        if await self._needs_escalation(message):
            await self.request_approval(
                task_id=session_id, stage="chat_support",
                required_role="operator", sla_minutes=10,
                context={"session_id": session_id, "message": message, 
                        "visitor": visitor_data, "channel": "web"}
            )
            return {"status": "escalated", "agent_name": "Human Agent"}
        
        response = await self._generate_response(message)
        await self.report_task_event(
            task_id=session_id, status="completed", stage="auto_response",
            data={"session_id": session_id, "message": message, "response": response}
        )
        return {"status": "responded", "message": response}
    
    async def _needs_escalation(self, message: str) -> bool:
        keywords = ["refund", "complaint", "cancel", "chargeback", "fraud",
                    "legal", "lawyer", "sue", "angry", "manager", "human",
                    "real person", "escalate", "supervisor"]
        return any(kw in message.lower() for kw in keywords)
    
    async def _generate_response(self, message: str) -> str:
        return "Thank you for reaching out. How can I assist you today?"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--url", default="https://api.fleetops.io")
    parser.add_argument("--website-id", required=True)
    args = parser.parse_args()
    connector = WebChatConnector(api_key=args.api_key, fleetops_url=args.url, website_id=args.website_id)
    asyncio.run(connector.connect())
    print(f"Web Chat connector running for website {args.website_id}")
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        asyncio.run(connector.disconnect())
