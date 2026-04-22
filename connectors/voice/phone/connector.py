"""Voice/Phone Connector for FleetOps

Handles voice calls with speech-to-text and human handoff.
"""

import asyncio
from typing import Optional
from connectors.base import FleetOpsConnector, AgentConfig, AgentMode, AgentType

class VoiceConnector(FleetOpsConnector):
    """Voice phone agent with human handoff"""
    
    PROVIDER = "voice"
    DEFAULT_MODEL = "whisper-1"
    
    def __init__(self, api_key: str, fleetops_url: str,
                 phone_number: str, name: str = "Voice Agent",
                 level: str = "senior", parent_agent_id: Optional[str] = None):
        config = AgentConfig(
            name=name, provider=self.PROVIDER, model=self.DEFAULT_MODEL,
            mode=AgentMode.CLOUD, agent_type=AgentType.VOICE,
            capabilities=["voice", "transcribe", "escalate", "support"],
            level=level, parent_agent_id=parent_agent_id,
            metadata={"phone_number": phone_number, "channels": ["voice"]}
        )
        super().__init__(api_key, fleetops_url, config)
        self.phone_number = phone_number
    
    async def handle_call(self, call_id: str, transcript: str):
        """Handle voice call transcript"""
        if await self._needs_escalation(transcript):
            await self.request_approval(
                task_id=call_id, stage="voice_support",
                required_role="operator", sla_minutes=5,
                context={"call_id": call_id, "transcript": transcript, "channel": "voice"}
            )
            return {"status": "escalated", "action": "transfer_to_human"}
        
        response = await self._generate_response(transcript)
        await self.report_task_event(
            task_id=call_id, status="completed", stage="auto_response",
            data={"call_id": call_id, "transcript": transcript, "response": response}
        )
        return {"status": "responded", "message": response}
    
    async def _needs_escalation(self, transcript: str) -> bool:
        keywords = ["angry", "frustrated", "manager", "supervisor", "escalate",
                    "complaint", "legal", "lawyer", "refund", "chargeback", "fraud"]
        return any(kw in transcript.lower() for kw in keywords)
    
    async def _generate_response(self, transcript: str) -> str:
        return "I understand. Let me connect you with a specialist."

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--url", default="https://api.fleetops.io")
    parser.add_argument("--phone", required=True)
    args = parser.parse_args()
    connector = VoiceConnector(api_key=args.api_key, fleetops_url=args.url, phone_number=args.phone)
    asyncio.run(connector.connect())
    print(f"Voice connector running on {args.phone}")
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        asyncio.run(connector.disconnect())
