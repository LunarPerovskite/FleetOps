"""FleetOps CLI — Terminal Companion Tool

Zero-friction approvals from your terminal.
Built with Typer + Rich for beautiful output.

Usage:
    fleetops status              Show system status
    fleetops list                List pending approvals
    fleetops approve <id>        Approve a pending request
    fleetops reject <id>         Reject a pending request
    fleetops agents              List active agents
    fleetops costs               Show cost summary
    fleetops config              Show current configuration
"""

import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich import box

import asyncio
import httpx
import json
import os

app = typer.Typer(
    name="fleetops",
    help="FleetOps CLI — Manage approvals, agents, and costs from your terminal",
    add_completion=False,
    rich_markup_mode="rich"
)

console = Console()

# ═══════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════

DEFAULT_API_URL = "http://localhost:8000"


def get_api_url() -> str:
    """Get FleetOps API URL from environment or default"""
    return os.getenv("FLEETOPS_API_URL", DEFAULT_API_URL)


def get_api_key() -> Optional[str]:
    """Get FleetOps API key from environment"""
    return os.getenv("FLEETOPS_API_KEY")


# ═══════════════════════════════════════════════════════
# HTTP CLIENT
# ═══════════════════════════════════════════════════════

async def api_get(endpoint: str) -> dict:
    """Make GET request to FleetOps API"""
    url = f"{get_api_url()}{endpoint}"
    headers = {}
    api_key = get_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


async def api_post(endpoint: str, data: dict) -> dict:
    """Make POST request to FleetOps API"""
    url = f"{get_api_url()}{endpoint}"
    headers = {"Content-Type": "application/json"}
    api_key = get_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()


# ═══════════════════════════════════════════════════════
# STATUS COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def status(
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch mode — refresh every 5 seconds")
):
    """Show FleetOps system status"""
    
    async def _get_status():
        try:
            # Simulated status (would call real API)
            return {
                "status": "healthy",
                "version": "0.1.0",
                "uptime": "2d 14h 33m",
                "agents": 5,
                "pending_approvals": 3,
                "total_cost_today": 47.83,
                "active_sessions": 2
            }
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None
    
    result = asyncio.run(_get_status())
    if not result:
        raise typer.Exit(1)
    
    # Build status panel
    grid = Table.grid(padding=1)
    grid.add_column(style="cyan", justify="right")
    grid.add_column(style="white")
    
    grid.add_row("Status:", f"[green]●[/green] {result['status'].upper()}")
    grid.add_row("Version:", result['version'])
    grid.add_row("Uptime:", result['uptime'])
    grid.add_row("Agents:", str(result['agents']))
    grid.add_row("Pending Approvals:", f"[yellow]{result['pending_approvals']}[/yellow]")
    grid.add_row("Cost Today:", f"[green]${result['total_cost_today']:.2f}[/green]")
    grid.add_row("Active Sessions:", str(result['active_sessions']))
    
    panel = Panel(
        grid,
        title="[bold]FleetOps Status[/bold]",
        border_style="blue",
        box=box.ROUNDED
    )
    console.print(panel)


# ═══════════════════════════════════════════════════════
# LIST COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def list(
    status_filter: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status: pending, approved, rejected"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Filter by agent name"),
    danger: Optional[str] = typer.Option(None, "--danger", "-d", help="Filter by danger: safe, low, medium, high, critical")
):
    """List pending approval requests"""
    
    async def _get_approvals():
        # Simulated data (would call real API)
        approvals = [
            {
                "id": "apr-001",
                "agent": "claude-code-prod",
                "action": "bash rm -rf /tmp/data",
                "danger": "high",
                "cost": 0.0,
                "status": "pending",
                "waiting": "5m 23s",
                "requester": "Claude Code"
            },
            {
                "id": "apr-002",
                "agent": "roo-code-dev",
                "action": "write file /app/auth.py",
                "danger": "critical",
                "cost": 0.0,
                "status": "pending",
                "waiting": "2m 15s",
                "requester": "Roo Code"
            },
            {
                "id": "apr-003",
                "agent": "crewai-research",
                "action": "api call OpenAI (gpt-4)",
                "danger": "medium",
                "cost": 0.15,
                "status": "pending",
                "waiting": "12m 47s",
                "requester": "CrewAI"
            }
        ]
        return approvals
    
    approvals = asyncio.run(_get_approvals())
    
    if not approvals:
        console.print("[green]No pending approvals! 🎉[/green]")
        return
    
    # Build table
    table = Table(
        title="[bold]Pending Approvals[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("ID", style="dim", width=10)
    table.add_column("Agent", style="cyan", min_width=15)
    table.add_column("Action", style="white", min_width=30)
    table.add_column("Danger", justify="center", width=10)
    table.add_column("Cost", justify="right", width=8)
    table.add_column("Waiting", justify="right", width=10)
    
    for apr in approvals:
        # Color by danger level
        danger_color = {
            "safe": "green",
            "low": "yellow",
            "medium": "orange3",
            "high": "red",
            "critical": "bold red"
        }.get(apr["danger"], "white")
        
        danger_emoji = {
            "safe": "🟢",
            "low": "🟡",
            "medium": "🟠",
            "high": "🔴",
            "critical": "🚨"
        }.get(apr["danger"], "⚪")
        
        table.add_row(
            apr["id"],
            apr["agent"],
            apr["action"][:50],
            f"[{danger_color}]{danger_emoji} {apr['danger'].upper()}[/{danger_color}]",
            f"${apr['cost']:.2f}",
            apr["waiting"]
        )
    
    console.print(table)
    console.print(f"\n[dim]Use [bold]fleetops approve <id>[/bold] or [bold]fleetops reject <id>[/bold] to respond[/dim]")


# ═══════════════════════════════════════════════════════
# APPROVE COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def approve(
    approval_id: str = typer.Argument(..., help="Approval ID to approve"),
    scope: str = typer.Option("once", "--scope", help="Approval scope: once, session, workspace, always"),
    comments: Optional[str] = typer.Option(None, "--comments", "-c", help="Optional comments"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """Approve a pending request"""
    
    # Validate scope
    valid_scopes = ["once", "session", "workspace", "always"]
    if scope not in valid_scopes:
        console.print(f"[red]Invalid scope: {scope}. Must be one of: {', '.join(valid_scopes)}[/red]")
        raise typer.Exit(1)
    
    # Show confirmation (unless --force)
    if not force:
        scope_desc = {
            "once": "this action only",
            "session": "this session (until agent stops)",
            "workspace": "this workspace/project",
            "always": "ALL future similar actions"
        }
        
        confirm = Confirm.ask(
            f"Approve [cyan]{approval_id}[/cyan]? Scope: [yellow]{scope_desc[scope]}[/yellow]",
            default=True
        )
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)
    
    async def _approve():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console
        ) as progress:
            task = progress.add_task("Sending approval...", total=None)
            
            # Simulated API call
            await asyncio.sleep(0.5)
            
            return {
                "status": "success",
                "approval_id": approval_id,
                "scope": scope,
                "message": f"Approved with scope: {scope}"
            }
    
    result = asyncio.run(_approve())
    
    console.print(f"[green]✅ Approved[/green] [cyan]{approval_id}[/cyan] (scope: [yellow]{scope}[/yellow])")
    
    if comments:
        console.print(f"[dim]Comments: {comments}[/dim]")


# ═══════════════════════════════════════════════════════
# REJECT COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def reject(
    approval_id: str = typer.Argument(..., help="Approval ID to reject"),
    comments: Optional[str] = typer.Option(None, "--comments", "-c", help="Optional reason for rejection"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """Reject a pending request"""
    
    if not force:
        confirm = Confirm.ask(
            f"Reject [cyan]{approval_id}[/cyan]?",
            default=False
        )
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)
    
    async def _reject():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console
        ) as progress:
            task = progress.add_task("Sending rejection...", total=None)
            await asyncio.sleep(0.5)
            
            return {
                "status": "success",
                "approval_id": approval_id,
                "message": "Rejected"
            }
    
    result = asyncio.run(_reject())
    
    console.print(f"[red]❌ Rejected[/red] [cyan]{approval_id}[/cyan]")
    
    if comments:
        console.print(f"[dim]Reason: {comments}[/dim]")


# ═══════════════════════════════════════════════════════
# AGENTS COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def agents(
    active_only: bool = typer.Option(True, "--active/--all", help="Show only active agents")
):
    """List active agents"""
    
    async def _get_agents():
        # Simulated data
        return [
            {
                "id": "agent-1",
                "name": "claude-code-prod",
                "type": "claude_code",
                "status": "running",
                "task": "Refactoring auth module",
                "tokens_used": 1240000,
                "cost_today": 12.40
            },
            {
                "id": "agent-2",
                "name": "roo-code-dev",
                "type": "roo_code",
                "status": "waiting_approval",
                "task": "Write tests for API",
                "tokens_used": 890000,
                "cost_today": 8.90
            },
            {
                "id": "agent-3",
                "name": "crewai-research",
                "type": "crewai",
                "status": "paused",
                "task": "Research competitors",
                "tokens_used": 450000,
                "cost_today": 4.50
            }
        ]
    
    agents_list = asyncio.run(_get_agents())
    
    table = Table(
        title="[bold]Active Agents[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("ID", style="dim", width=10)
    table.add_column("Name", style="cyan", min_width=20)
    table.add_column("Type", style="blue")
    table.add_column("Status", justify="center", width=15)
    table.add_column("Current Task", style="white", min_width=25)
    table.add_column("Tokens", justify="right", width=12)
    table.add_column("Cost Today", justify="right", width=10)
    
    for agent in agents_list:
        status_color = {
            "running": "green",
            "waiting_approval": "yellow",
            "paused": "orange3",
            "error": "red",
            "completed": "dim"
        }.get(agent["status"], "white")
        
        status_emoji = {
            "running": "🟢",
            "waiting_approval": "⏳",
            "paused": "⏸️",
            "error": "🔴",
            "completed": "✅"
        }.get(agent["status"], "⚪")
        
        table.add_row(
            agent["id"],
            agent["name"],
            agent["type"],
            f"[{status_color}]{status_emoji} {agent['status'].replace('_', ' ').title()}[/{status_color}]",
            agent["task"][:30],
            f"{agent['tokens_used']:,}",
            f"${agent['cost_today']:.2f}"
        )
    
    console.print(table)


# ═══════════════════════════════════════════════════════
# COSTS COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def costs(
    period: str = typer.Option("today", "--period", "-p", help="Period: today, week, month"),
    breakdown: bool = typer.Option(False, "--breakdown", "-b", help="Show per-agent breakdown")
):
    """Show cost summary"""
    
    async def _get_costs():
        return {
            "period": period,
            "total": 47.83,
            "budget_limit": 100.00,
            "percentage": 47.83,
            "by_agent": {
                "claude-code-prod": 25.40,
                "roo-code-dev": 15.20,
                "crewai-research": 7.23
            },
            "by_provider": {
                "OpenAI": 30.00,
                "Anthropic": 12.50,
                "Groq": 5.33
            }
        }
    
    costs_data = asyncio.run(_get_costs())
    
    # Main summary panel
    percentage = costs_data["percentage"]
    bar_width = 30
    filled = int((percentage / 100) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    color = "green" if percentage < 50 else "yellow" if percentage < 80 else "red"
    
    grid = Table.grid(padding=1)
    grid.add_column(style="cyan", justify="right")
    grid.add_column(style="white")
    
    grid.add_row("Period:", costs_data["period"].title())
    grid.add_row("Total Cost:", f"[bold]${costs_data['total']:.2f}[/bold]")
    grid.add_row("Budget Limit:", f"${costs_data['budget_limit']:.2f}")
    grid.add_row("Usage:", f"[{color}]{bar} {percentage:.1f}%[/{color}]")
    
    panel = Panel(
        grid,
        title="[bold]Cost Summary[/bold]",
        border_style="blue",
        box=box.ROUNDED
    )
    console.print(panel)
    
    if breakdown:
        # Agent breakdown
        agent_table = Table(title="[bold]By Agent[/bold]", box=box.SIMPLE)
        agent_table.add_column("Agent", style="cyan")
        agent_table.add_column("Cost", justify="right", style="green")
        
        for name, cost in costs_data["by_agent"].items():
            agent_table.add_row(name, f"${cost:.2f}")
        
        console.print(agent_table)
        
        # Provider breakdown
        provider_table = Table(title="[bold]By Provider[/bold]", box=box.SIMPLE)
        provider_table.add_column("Provider", style="cyan")
        provider_table.add_column("Cost", justify="right", style="green")
        
        for name, cost in costs_data["by_provider"].items():
            provider_table.add_row(name, f"${cost:.2f}")
        
        console.print(provider_table)


# ═══════════════════════════════════════════════════════
# CONFIG COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def config(
    show: bool = typer.Option(True, "--show", help="Show current config"),
    api_url: Optional[str] = typer.Option(None, "--api-url", help="Set FleetOps API URL"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="Set FleetOps API key")
):
    """Show or set FleetOps configuration"""
    
    if api_url:
        console.print(f"Setting API URL: {api_url}")
        # Would persist to config file
    
    if api_key:
        console.print("Setting API key: [dim]***[/dim]")
        # Would persist to config file
    
    if show:
        grid = Table.grid(padding=1)
        grid.add_column(style="cyan", justify="right")
        grid.add_column(style="white")
        
        grid.add_row("API URL:", get_api_url())
        grid.add_row("API Key:", "[dim]set[/dim]" if get_api_key() else "[red]not set[/red]")
        grid.add_row("Config File:", "~/.fleetops/config.json")
        
        panel = Panel(
            grid,
            title="[bold]FleetOps Config[/bold]",
            border_style="blue",
            box=box.ROUNDED
        )
        console.print(panel)


# ═══════════════════════════════════════════════════════
# MAIN ENTRYPOINT
# ═══════════════════════════════════════════════════════

def main():
    """Entry point for the CLI"""
    app()


if __name__ == "__main__":
    main()
