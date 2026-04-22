"""Discord Community Connector for FleetOps

Handles community management, moderation, and support via Discord.
"""

import asyncio
from typing import Optional
from connectors.base import FleetOpsConnector, AgentConfig, AgentMode, AgentType

class DiscordCommunityConnector(FleetOpsConnector):
    """Discord community agent with moderation and support"""
    
    PROVIDER = "discord"
    DEFAULT_MODEL = "gpt-4.1"
    
    def __init__(self, api_key: str, fleetops_url: str,
                 bot_token: str, guild_id: str,
                 name: str = "Discord Community", level: str = "senior",
                 parent_agent_id: Optional[str] = None):
        config = AgentConfig(
            name=name, provider=self.PROVIDER, model=self.DEFAULT_MODEL,
            mode=AgentMode.CLOUD, agent_type=AgentType.COMMUNITY,
            capabilities=["moderate", "escalate", "support", "faq", "announce"],
            level=level, parent_agent_id=parent_agent_id,
            metadata={
                "bot_token": bot_token,
                "guild_id": guild_id,
                "channels": ["discord"]
            }
        )
        super().__init__(api_key, fleetops_url, config)
        self.bot_token = bot_token
        self.guild_id = guild_id
    
    async def handle_message(self, message_id: str, channel_id: str,
                          author_id: str, content: str):
        """Handle Discord message"""
        # Check for moderation issues
        if await self._needs_moderation(content):
            await self.request_approval(
                task_id=message_id, stage="moderation",
                required_role="operator", sla_minutes=5,
                context={
                    "channel_id": channel_id,
                    "author_id": author_id,
                    "content": content,
                    "channel": "discord"
                }
            )
            return {"status": "flagged", "action": "awaiting_moderation"}
        
        # Check for support questions
        if await self._is_support_question(content):
            response = await self._generate_response(content)
            await self.report_task_event(
                task_id=message_id, status="completed", stage="auto_response",
                data={"channel_id": channel_id, "author_id": author_id,
                      "content": content, "response": response}
            )
            return {"status": "responded", "response": response}
        
        return {"status": "ignored"}
    
    async def _needs_moderation(self, content: str) -> bool:
        keywords = ["spam", "scam", "inappropriate", "offensive", "abuse",
                   "harassment", "toxic", "nsfw", "hate", "violence"]
        return any(kw in content.lower() for kw in keywords)
    
    async def _is_support_question(self, content: str) -> bool:
        keywords = ["help", "how to", "question", "issue", "problem",
                   "bug", "error", "support", "assist"]
        return any(kw in content.lower() for kw in keywords)
    
    async def _generate_response(self, content: str) -> str:
        return "Thanks for your question! Let me help you with that."


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--url", default="https://api.fleetops.io")
    parser.add_argument("--bot-token", required=True)
    parser.add_argument("--guild-id", required=True)
    args = parser.parse_args()
    
    connector = DiscordCommunityConnector(
        api_key=args.api_key, fleetops_url=args.url,
        bot_token=args.bot_token, guild_id=args.guild_id
    )
    asyncio.run(connector.connect())
    print(f"Discord Community connector running")
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        asyncio.run(connector.disconnect())
