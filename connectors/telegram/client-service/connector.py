"""Telegram Customer Service Connector for FleetOps

Handles customer service via Telegram with human escalation.
"""

import asyncio
from typing import Optional
from connectors.base import FleetOpsConnector, AgentConfig, AgentMode, AgentType, Message

class TelegramServiceConnector(FleetOpsConnector):
    """Telegram customer service agent with human escalation"""
    
    PROVIDER = "telegram"
    DEFAULT_MODEL = "gpt-4.1"
    
    def __init__(self, api_key: str, fleetops_url: str,
                 bot_token: str, name: str = "Telegram Service",
                 level: str = "senior", parent_agent_id: Optional[str] = None):
        config = AgentConfig(
            name=name, provider=self.PROVIDER, model=self.DEFAULT_MODEL,
            mode=AgentMode.CLOUD, agent_type=AgentType.CUSTOMER_SERVICE,
            capabilities=["chat", "escalate", "ticket", "faq", "support"],
            level=level, parent_agent_id=parent_agent_id,
            metadata={"bot_token": bot_token, "channels": ["telegram"]}
        )
        super().__init__(api_key, fleetops_url, config)
        self.bot_token = bot_token
        self.conversations: dict = {}
    
    async def handle_customer_message(self, chat_id: str, message_text: str):
        """Handle incoming Telegram message"""
        thread_id = self.conversations.get(chat_id, {}).get("thread_id")
        
        if await self._needs_escalation(message_text):
            await self.request_approval(
                task_id=thread_id or "new", stage="customer_support",
                required_role="operator", sla_minutes=15,
                context={"chat_id": chat_id, "message": message_text, "channel": "telegram"}
            )
            return {"status": "escalated"}
        
        response = await self._generate_response(message_text)
        await self.report_task_event(
            task_id=thread_id or "new", status="completed", stage="auto_response",
            data={"chat_id": chat_id, "message": message_text, "response": response}
        )
        return {"status": "responded", "message": response}
    
    async def _needs_escalation(self, message: str) -> bool:
        escalation_keywords = ["refund", "complaint", "cancel", "chargeback", "fraud",
                               "legal", "lawyer", "sue", "angry", "manager", "supervisor",
                               "human", "real person", "escalate"]
        return any(keyword in message.lower() for keyword in escalation_keywords)
    
    async def _generate_response(self, message: str) -> str:
        return f"Thank you for contacting us. How can we assist you today?"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--url", default="https://api.fleetops.io")
    parser.add_argument("--bot-token", required=True)
    args = parser.parse_args()
    
    connector = TelegramServiceConnector(
        api_key=args.api_key, fleetops_url=args.url, bot_token=args.bot_token
    )
    asyncio.run(connector.connect())
    print(f"Telegram Service connector running")
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        asyncio.run(connector.disconnect())
