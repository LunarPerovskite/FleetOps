"""WhatsApp Customer Service Connector for FleetOps

Handles customer service via WhatsApp with human escalation.
"""

import asyncio
from typing import Optional
from connectors.base import FleetOpsConnector, AgentConfig, AgentMode, AgentType, Message

class WhatsAppServiceConnector(FleetOpsConnector):
    """WhatsApp customer service agent with human escalation"""
    
    PROVIDER = "whatsapp"
    DEFAULT_MODEL = "gpt-4.1"
    
    def __init__(self, api_key: str, fleetops_url: str, 
                 phone_number: str, business_id: str,
                 name: str = "WhatsApp Service", 
                 level: str = "senior",
                 parent_agent_id: Optional[str] = None):
        config = AgentConfig(
            name=name,
            provider=self.PROVIDER,
            model=self.DEFAULT_MODEL,
            mode=AgentMode.CLOUD,
            agent_type=AgentType.CUSTOMER_SERVICE,
            capabilities=["chat", "escalate", "ticket", "faq", "support"],
            level=level,
            parent_agent_id=parent_agent_id,
            metadata={
                "phone_number": phone_number,
                "business_id": business_id,
                "channels": ["whatsapp"]
            }
        )
        super().__init__(api_key, fleetops_url, config)
        self.phone_number = phone_number
        self.business_id = business_id
        self.conversations: dict = {}
    
    async def handle_customer_message(self, from_number: str, message_text: str):
        """Handle incoming WhatsApp message"""
        # Create or get conversation thread
        thread_id = self.conversations.get(from_number, {}).get("thread_id")
        
        # Check if needs human escalation
        if await self._needs_escalation(message_text):
            await self.request_approval(
                task_id=thread_id or "new",
                stage="customer_support",
                required_role="operator",
                sla_minutes=15,
                context={
                    "customer_phone": from_number,
                    "message": message_text,
                    "channel": "whatsapp"
                }
            )
            return {"status": "escalated", "message": "Human agent will respond shortly"}
        
        # Auto-respond
        response = await self._generate_response(message_text)
        
        # Report to FleetOps
        await self.report_task_event(
            task_id=thread_id or "new",
            status="completed",
            stage="auto_response",
            data={
                "customer_phone": from_number,
                "message": message_text,
                "response": response,
                "channel": "whatsapp"
            }
        )
        
        return {"status": "responded", "message": response}
    
    async def _needs_escalation(self, message: str) -> bool:
        """Determine if message needs human escalation"""
        escalation_keywords = [
            "refund", "complaint", "cancel subscription", "chargeback",
            "fraud", "legal", "lawyer", "sue", "angry", "frustrated",
            "manager", "supervisor", "human", "real person"
        ]
        return any(keyword in message.lower() for keyword in escalation_keywords)
    
    async def _generate_response(self, message: str) -> str:
        """Generate automated response"""
        # In production, this calls LLM
        return f"Thank you for contacting us. An agent will assist you shortly."
    
    async def send_whatsapp_message(self, to_number: str, message: str):
        """Send message via WhatsApp API"""
        # Integration with WhatsApp Business API
        pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--url", default="https://api.fleetops.io")
    parser.add_argument("--phone", required=True)
    parser.add_argument("--business-id", required=True)
    args = parser.parse_args()
    
    connector = WhatsAppServiceConnector(
        api_key=args.api_key,
        fleetops_url=args.url,
        phone_number=args.phone,
        business_id=args.business_id
    )
    
    asyncio.run(connector.connect())
    print(f"WhatsApp Service connector running on {args.phone}")
    
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        asyncio.run(connector.disconnect())
