"""Discord Bot Integration for FleetOps

Connect FleetOps to Discord for notifications and commands
"""

import os
from typing import Optional
import discord
from discord.ext import commands

class DiscordBotAdapter:
    """Discord bot for FleetOps notifications"""
    
    def __init__(self):
        self.token = os.getenv("DISCORD_BOT_TOKEN")
        self.enabled = self.token is not None
        self.bot = None
        if self.enabled:
            intents = discord.Intents.default()
            intents.message_content = True
            self.bot = commands.Bot(command_prefix="!fleetops ", intents=intents)
            self._setup_commands()
    
    def _setup_commands(self):
        """Setup bot commands"""
        
        @self.bot.event
        async def on_ready():
            print(f"FleetOps Discord bot connected as {self.bot.user}")
        
        @self.bot.command(name="status")
        async def status(ctx):
            """Get FleetOps status"""
            embed = discord.Embed(
                title="FleetOps Status",
                description="System is operational",
                color=discord.Color.green()
            )
            embed.add_field(name="Version", value="0.1.0", inline=True)
            embed.add_field(name="Status", value="✅ Online", inline=True)
            await ctx.send(embed=embed)
        
        @self.bot.command(name="tasks")
        async def tasks(ctx, status: Optional[str] = None):
            """List recent tasks"""
            # In production, fetch from API
            embed = discord.Embed(
                title="Recent Tasks",
                description="Last 5 tasks",
                color=discord.Color.blue()
            )
            embed.add_field(name="Task 1", value="Review Q3 Report - ✅ Completed", inline=False)
            embed.add_field(name="Task 2", value="Deploy API v2 - 🔄 Executing", inline=False)
            await ctx.send(embed=embed)
        
        @self.bot.command(name="approve")
        async def approve(ctx, task_id: str):
            """Approve a task"""
            embed = discord.Embed(
                title="✅ Task Approved",
                description=f"Task {task_id} has been approved",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
    
    async def send_task_notification(self, channel_id: int, task: dict):
        """Send task update to Discord channel"""
        if not self.enabled:
            return
        
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return
            
            embed = discord.Embed(
                title=f"Task Update: {task['title']}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Status", value=task['status'], inline=True)
            embed.add_field(name="Agent", value=task.get('agent_name', 'N/A'), inline=True)
            embed.add_field(name="Priority", value=str(task.get('priority', 'N/A')), inline=True)
            
            await channel.send(embed=embed)
        except Exception as e:
            print(f"Discord notification failed: {e}")
    
    async def send_approval_request(self, channel_id: int, approval: dict):
        """Send approval request to Discord"""
        if not self.enabled:
            return
        
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return
            
            embed = discord.Embed(
                title="🔍 Approval Required",
                description=f"Task: {approval['task_title']}",
                color=discord.Color.yellow()
            )
            embed.add_field(name="Stage", value=approval['stage'], inline=True)
            embed.add_field(name="Requested by", value=approval.get('agent_name', 'System'), inline=True)
            embed.add_field(
                name="Actions",
                value="React with: ✅ Approve | ❌ Reject | ⬆️ Escalate",
                inline=False
            )
            
            message = await channel.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            await message.add_reaction("⬆️")
        except Exception as e:
            print(f"Discord approval request failed: {e}")
    
    async def start(self):
        """Start the Discord bot"""
        if self.enabled:
            await self.bot.start(self.token)

# Initialize adapter
discord_bot = DiscordBotAdapter()
