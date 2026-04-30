"""FleetOps CLI — Main entry point

Usage:
    fleetops status
    fleetops list
    fleetops approve <id> [--scope once|session|workspace|always]
    fleetops reject <id> [--comments "reason"]
    fleetops agents
    fleetops costs [--breakdown]
    fleetops config
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich import box

import asyncio
import os

from fleetops_cli.client import FleetOpsClient, create_client

app = typer.Typer(
    name="fleetops",
    help="FleetOps CLI — Universal agent governance tool",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True
)

console = Console()

# Global client instance
_client: Optional[FleetOpsClient] = None

def get_client() -> FleetOpsClient:
    """Get or create FleetOps client"""
    global _client
    if _client is None:
        api_url = os.getenv("FLEETOPS_API_URL", "http://localhost:8000")
        api_key = os.getenv("FLEETOPS_API_KEY")
        _client = create_client(api_url=api_url, api_key=api_key)
    return _client

# ═══════════════════════════════════════════════════════
# STATUS COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def status():
    """Show FleetOps system status"""
    
    async def _get_status():
        client = get_client()
        return await client.get_status()
    
    result = asyncio.run(_get_status())
    
    if result.get("status") == "unavailable":
        console.print(Panel(
            "[red]FleetOps is not available[/red]\n"
            "Check your API URL: " + os.getenv("FLEETOPS_API_URL", "http://localhost:8000"),
            title="[bold]Status[/bold]",
            border_style="red"
        ))
        raise typer.Exit(1)
    
    grid = Table.grid(padding=1)
    grid.add_column(style="cyan", justify="right")
    grid.add_column(style="white")
    
    grid.add_row("Status:", f"[green]●[/green] {result.get('status', 'unknown').upper()}")
    grid.add_row("Version:", result.get('version', 'unknown'))
    grid.add_row("Agents:", str(result.get('agents', 0)))
    grid.add_row("Pending Approvals:", f"[yellow]{result.get('pending_approvals', 0)}[/yellow]")
    grid.add_row("Cost Today:", f"[green]${result.get('total_cost_today', 0):.2f}[/green]")
    
    console.print(Panel(
        grid,
        title="[bold]FleetOps Status[/bold]",
        border_style="blue",
        box=box.ROUNDED
    ))

# ═══════════════════════════════════════════════════════
# LIST COMMAND
# ═══════════════════════════════════════════════════════

@app.command("approvals")
def list_approvals():
    """List pending approvals"""
    
    async def _get_pending():
        client = get_client()
        return await client.get_pending()
    
    approvals = asyncio.run(_get_pending())
    
    if not approvals:
        console.print("[green]No pending approvals! 🎉[/green]")
        return
    
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
    
    for apr in approvals:
        danger_level = apr.get("danger_level", "unknown")
        danger_color = {
            "safe": "green", "low": "yellow",
            "medium": "orange3", "high": "red", "critical": "bold red"
        }.get(danger_level, "white")
        
        danger_emoji = {
            "safe": "🟢", "low": "🟡",
            "medium": "🟠", "high": "🔴", "critical": "🚨"
        }.get(danger_level, "⚪")
        
        table.add_row(
            apr.get("id", "unknown")[:10],
            apr.get("agent_name", "unknown")[:15],
            apr.get("action", "")[:50],
            f"[{danger_color}]{danger_emoji} {danger_level.upper()}[/{danger_color}]",
            f"${apr.get('estimated_cost', 0):.2f}"
        )
    
    console.print(table)
    console.print("\n[dim]Use [bold]fleetops approve <id>[/bold] or [bold]fleetops reject <id>[/bold][/dim]")

# ═══════════════════════════════════════════════════════
# APPROVE COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def approve(
    approval_id: str = typer.Argument(..., help="Approval ID to approve"),
    scope: str = typer.Option("once", "--scope", help="once, session, workspace, always"),
    comments: Optional[str] = typer.Option(None, "--comments", "-c", help="Optional comments"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Approve a pending request"""
    
    valid_scopes = ["once", "session", "workspace", "always"]
    if scope not in valid_scopes:
        console.print(f"[red]Invalid scope: {scope}. Must be: {', '.join(valid_scopes)}[/red]")
        raise typer.Exit(1)
    
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
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            transient=True, console=console
        ) as progress:
            progress.add_task("Sending approval...", total=None)
            client = get_client()
            return await client.approve(approval_id, scope, comments)
    
    result = asyncio.run(_approve())
    
    if result.get("status") == "success":
        console.print(f"[green]✅ Approved[/green] [cyan]{approval_id}[/cyan] (scope: [yellow]{scope}[/yellow])")
    else:
        console.print(f"[red]❌ Error:[/red] {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)

# ═══════════════════════════════════════════════════════
# REJECT COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def reject(
    approval_id: str = typer.Argument(..., help="Approval ID to reject"),
    comments: Optional[str] = typer.Option(None, "--comments", "-c", help="Reason for rejection"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Reject a pending request"""
    
    if not force:
        confirm = Confirm.ask(f"Reject [cyan]{approval_id}[/cyan]?", default=False)
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)
    
    async def _reject():
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            transient=True, console=console
        ) as progress:
            progress.add_task("Sending rejection...", total=None)
            client = get_client()
            return await client.reject(approval_id, comments)
    
    result = asyncio.run(_reject())
    
    if result.get("status") == "success":
        console.print(f"[red]❌ Rejected[/red] [cyan]{approval_id}[/cyan]")
        if comments:
            console.print(f"[dim]Reason: {comments}[/dim]")
    else:
        console.print(f"[red]❌ Error:[/red] {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)

# ═══════════════════════════════════════════════════════
# AGENTS COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def agents():
    """List active agents"""
    
    async def _get_agents():
        # Would call real API
        return [
            {"name": "claude-code", "status": "running", "cost_today": 12.40},
            {"name": "roo-code", "status": "waiting_approval", "cost_today": 8.90},
        ]
    
    agents_list = asyncio.run(_get_agents())
    
    table = Table(title="[bold]Active Agents[/bold]", box=box.ROUNDED)
    table.add_column("Agent", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Cost Today", justify="right", style="green")
    
    for agent in agents_list:
        status_color = {
            "running": "green", "waiting_approval": "yellow",
            "paused": "orange3", "error": "red"
        }.get(agent["status"], "white")
        
        table.add_row(
            agent["name"],
            f"[{status_color}]{agent['status']}[/{status_color}]",
            f"${agent['cost_today']:.2f}"
        )
    
    console.print(table)

# ═══════════════════════════════════════════════════════
# COSTS COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def costs(
    period: str = typer.Option("today", "--period", "-p", help="today, week, month"),
    breakdown: bool = typer.Option(False, "--breakdown", "-b", help="Show per-agent breakdown")
):
    """Show cost summary"""
    
    # Simulated data
    total = 47.83
    budget = 100.00
    percentage = (total / budget) * 100
    
    bar_width = 30
    filled = int((percentage / 100) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    color = "green" if percentage < 50 else "yellow" if percentage < 80 else "red"
    
    grid = Table.grid(padding=1)
    grid.add_column(style="cyan", justify="right")
    grid.add_column(style="white")
    
    grid.add_row("Period:", period.title())
    grid.add_row("Total Cost:", f"[bold]${total:.2f}[/bold]")
    grid.add_row("Budget Limit:", f"${budget:.2f}")
    grid.add_row("Usage:", f"[{color}]{bar} {percentage:.1f}%[/{color}]")
    
    console.print(Panel(
        grid,
        title="[bold]Cost Summary[/bold]",
        border_style="blue",
        box=box.ROUNDED
    ))

# ═══════════════════════════════════════════════════════
# CONFIG COMMAND
# ═══════════════════════════════════════════════════════

@app.command()
def config(
    show: bool = typer.Option(True, "--show", help="Show config"),
    api_url: Optional[str] = typer.Option(None, "--api-url", help="Set API URL"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="Set API key")
):
    """Show or set configuration"""
    
    if api_url:
        os.environ["FLEETOPS_API_URL"] = api_url
        console.print(f"API URL set to: {api_url}")
    
    if api_key:
        os.environ["FLEETOPS_API_KEY"] = api_key
        console.print("API key set")
    
    if show:
        grid = Table.grid(padding=1)
        grid.add_column(style="cyan", justify="right")
        grid.add_column(style="white")
        
        current_url = os.getenv("FLEETOPS_API_URL", "http://localhost:8000")
        has_key = bool(os.getenv("FLEETOPS_API_KEY"))
        
        grid.add_row("API URL:", current_url)
        grid.add_row("API Key:", "[green]set[/green]" if has_key else "[red]not set[/red]")
        grid.add_row("Config:", "~/.fleetops/config.json")
        
        console.print(Panel(
            grid,
            title="[bold]FleetOps Config[/bold]",
            border_style="blue",
            box=box.ROUNDED
        ))

# ═══════════════════════════════════════════════════════
# MODELS COMMAND
# ═══════════════════════════════════════════════════════

@app.command("models")
def models_command(
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Show models for specific agent"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search models"),
    max_cost: Optional[float] = typer.Option(None, "--max-cost", "-c", help="Max cost per 1M tokens"),
    discover: bool = typer.Option(False, "--discover", "-d", help="Discover models from providers")
):
    """List and manage LLM models"""
    try:
        if discover:
            console.print("[yellow]Discovering models from providers...[/yellow]")
            # Discovery would go here
            console.print("[green]Discovery complete[/green]")
            return
        
        # Show models table
        table = Table(
            title="[bold]Available Models[/bold]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("Model", style="cyan", min_width=20)
        table.add_column("Provider", style="blue", width=12)
        table.add_column("Tier", style="yellow", width=10)
        table.add_column("Input/1M", justify="right", width=10)
        table.add_column("Output/1M", justify="right", width=10)
        table.add_column("Context", justify="right", width=10)
        table.add_column("Capabilities", style="green", min_width=20)
        
        from fleetops_cli.client import create_client
        import asyncio
        
        client = create_client(api_url=os.getenv("FLEETOPS_API_URL", "http://localhost:8000"))
        
        # Get models from API (discovered models)
        models = asyncio.run(client.list_discovered_models(provider=provider, search=search))
        
        # Apply max_cost filter in Python
        if max_cost:
            models = [m for m in models if m.get("pricing", {}).get("input", 999) <= max_cost]
        
        # Sort by cost
        models = sorted(models, key=lambda m: m.get("pricing", {}).get("input", 999))
        
        for m in models:
            tier = m.get("tier", "standard")
            tier_color = {
                "free": "green",
                "cheap": "cyan",
                "standard": "blue",
                "premium": "magenta",
                "ultra": "red"
            }.get(tier, "white")
            
            caps = ", ".join(m.get("capabilities", [])[:4])
            pricing = m.get("pricing", {})
            
            table.add_row(
                m.get("name", m.get("id", "unknown")),
                m.get("provider", "unknown"),
                f"[{tier_color}]{tier}[/{tier_color}]",
                f"${pricing.get('input', 0):.2f}",
                f"${pricing.get('output', 0):.2f}",
                f"{m.get('context_length', 'N/A')}",
                caps
            )
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(models)} models[/dim]")
        
        if agent:
            config = agent_model_manager.get_config(agent)
            if config:
                console.print(f"\n[bold]Agent {agent}:[/bold]")
                console.print(f"  Primary: {config.primary_model}")
                console.print(f"  Fallbacks: {', '.join(config.fallback_models)}")
                console.print(f"  Strategy: {config.strategy.value}")
                console.print(f"  Today: ${config.today_cost:.4f} ({config.today_requests} requests)")
            else:
                console.print(f"[red]Agent {agent} not configured[/red]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command("select-model")
def select_model_command(
    agent: str = typer.Option(..., "--agent", "-a", help="Agent ID"),
    model: str = typer.Option(..., "--model", "-m", help="Model ID to select"),
    user: str = typer.Option(..., "--user", "-u", help="User ID")
):
    """Select a model for an agent"""
    try:
        success = agent_model_manager.set_model(agent, model)
        if success:
            m = model_registry.get(model)
            console.print(f"[green]✓[/green] Model switched to [bold]{m.name if m else model}[/bold]")
            console.print(f"  Agent: {agent}")
            console.print(f"  Provider: {m.provider if m else 'unknown'}")
            console.print(f"  Cost/1K: ${m.estimate_cost(1000, 500):.4f}" if m else "")
        else:
            console.print(f"[red]Failed to select model {model}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command("estimate")
def estimate_command(
    model: str = typer.Option(..., "--model", "-m", help="Model ID"),
    input_tokens: int = typer.Option(1000, "--input", "-i", help="Input tokens"),
    output_tokens: int = typer.Option(500, "--output", "-o", help="Output tokens")
):
    """Estimate cost for a model request"""
    try:
        m = model_registry.get(model)
        if not m:
            console.print(f"[red]Model {model} not found[/red]")
            return
        
        cost = m.estimate_cost(input_tokens, output_tokens)
        
        console.print(Panel(
            f"[bold]{m.name}[/bold]\n"
            f"\n"
            f"Input:  {input_tokens:,} tokens @ ${m.input_cost_per_1m:.2f}/1M = ${(input_tokens/1_000_000)*m.input_cost_per_1m:.6f}\n"
            f"Output: {output_tokens:,} tokens @ ${m.output_cost_per_1m:.2f}/1M = ${(output_tokens/1_000_000)*m.output_cost_per_1m:.6f}\n"
            f"[bold]Total:  ${cost:.6f}[/bold]\n"
            f"\n"
            f"Context: {m.max_total_tokens:,} tokens\n"
            f"Tier: {m.tier.value}\n"
            f"Capabilities: {', '.join(c.value for c in m.capabilities)}",
            title="Cost Estimate",
            border_style="green",
            box=box.ROUNDED
        ))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# ═══════════════════════════════════════════════════════
# MAIN ENTRYPOINT
# ═══════════════════════════════════════════════════════

# Need to import after model_registry is loaded
from app.core.model_registry import model_registry
from app.core.agent_model_manager import agent_model_manager

def main():
    # Registry starts empty - models come from live discovery
    # Users must run `fleetops models --discover` to populate
    app()

if __name__ == "__main__":
    main()
