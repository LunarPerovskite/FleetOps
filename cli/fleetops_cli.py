"""FleetOps CLI Tool

Command-line interface for managing FleetOps deployments
"""

import click
import requests
import json
from typing import Optional

API_BASE = "http://localhost:8000/api/v1"

@click.group()
@click.option('--api-url', default='http://localhost:8000/api/v1', help='FleetOps API URL')
@click.option('--token', help='API authentication token')
@click.pass_context
def cli(ctx, api_url, token):
    """FleetOps CLI - Manage your human-agent workforce"""
    ctx.ensure_object(dict)
    ctx.obj['API_URL'] = api_url
    ctx.obj['TOKEN'] = token
    
    if not token:
        click.echo("⚠️  No token provided. Some commands may fail.")
        click.echo("   Get a token from /auth/login or set FLEETOPS_TOKEN env var")

# Helper function for API calls
def api_call(ctx, method, endpoint, data=None):
    """Make API call with auth"""
    url = f"{ctx.obj['API_URL']}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    if ctx.obj.get('TOKEN'):
        headers['Authorization'] = f"Bearer {ctx.obj['TOKEN']}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Error: {e}")
        return None

@cli.command()
@click.pass_context
def status(ctx):
    """Check FleetOps status"""
    result = api_call(ctx, 'GET', '/health')
    if result:
        click.echo(f"✅ FleetOps is {result.get('status', 'unknown')}")
        click.echo(f"   Version: {result.get('version', 'unknown')}")

@cli.command()
@click.option('--email', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
@click.pass_context
def login(ctx, email, password):
    """Authenticate and get token"""
    result = api_call(ctx, 'POST', '/auth/login', {'email': email, 'password': password})
    if result and 'access_token' in result:
        click.echo(f"✅ Logged in as {result['user']['email']}")
        click.echo(f"   Token: {result['access_token']}")
        click.echo("\n   Set this as your token:")
        click.echo(f"   export FLEETOPS_TOKEN={result['access_token']}")
    else:
        click.echo("❌ Login failed")

@cli.command()
@click.pass_context
def tasks(ctx):
    """List recent tasks"""
    result = api_call(ctx, 'GET', '/tasks')
    if result and 'tasks' in result:
        click.echo(f"📋 Tasks ({result.get('total', 0)} total):\n")
        for task in result['tasks'][:10]:
            status_emoji = "✅" if task['status'] == 'completed' else "🔄" if task['status'] == 'executing' else "⏳"
            click.echo(f"   {status_emoji} {task['title']} — {task['status']}")

@cli.command()
@click.option('--title', prompt=True, help='Task title')
@click.option('--description', default='', help='Task description')
@click.option('--agent-id', prompt=True, help='Agent ID to assign')
@click.option('--risk-level', type=click.Choice(['low', 'medium', 'high', 'critical']), default='medium')
@click.pass_context
def create_task(ctx, title, description, agent_id, risk_level):
    """Create a new task"""
    data = {
        'title': title,
        'description': description,
        'agent_id': agent_id,
        'risk_level': risk_level,
        'priority': 50
    }
    result = api_call(ctx, 'POST', '/tasks', data)
    if result and 'id' in result:
        click.echo(f"✅ Created task: {result['title']} (ID: {result['id']})")
    else:
        click.echo("❌ Failed to create task")

@cli.command()
@click.pass_context
def agents(ctx):
    """List agents"""
    result = api_call(ctx, 'GET', '/agents')
    if result and 'agents' in result:
        click.echo(f"🤖 Agents ({len(result['agents'])}):\n")
        for agent in result['agents']:
            status = "🟢" if agent['status'] == 'active' else "🔴"
            click.echo(f"   {status} {agent['name']} — {agent['provider']} ({agent['level']})")

@cli.command()
@click.pass_context
def approvals(ctx):
    """List pending approvals"""
    result = api_call(ctx, 'GET', '/approvals?status=pending')
    if result and 'approvals' in result:
        pending = [a for a in result['approvals'] if a['decision'] == 'pending']
        click.echo(f"🔍 Pending Approvals ({len(pending)}):\n")
        for approval in pending[:10]:
            click.echo(f"   ⏳ {approval.get('task_title', 'Unknown')} — {approval['stage']} stage")
            click.echo(f"      Approve: fleetops approve {approval['id']}")

@cli.command()
@click.argument('approval_id')
@click.option('--comment', default='', help='Approval comment')
@click.pass_context
def approve(ctx, approval_id, comment):
    """Approve a pending approval"""
    result = api_call(ctx, 'POST', f'/approvals/{approval_id}/decide', {
        'decision': 'approve',
        'comments': comment
    })
    if result:
        click.echo(f"✅ Approved {approval_id}")
    else:
        click.echo("❌ Failed to approve")

@cli.command()
@click.pass_context
def stats(ctx):
    """Show dashboard statistics"""
    result = api_call(ctx, 'GET', '/dashboard/stats')
    if result:
        click.echo("📊 Dashboard Stats:\n")
        click.echo(f"   Total Tasks: {result.get('total_tasks', 0)}")
        click.echo(f"   Active Agents: {result.get('active_agents', 0)}")
        click.echo(f"   Pending Approvals: {result.get('pending_approvals', 0)}")
        click.echo(f"   Cost Today: ${result.get('cost_today', 0):.2f}")

@cli.command()
@click.pass_context
def onboard(ctx):
    """Show onboarding progress"""
    result = api_call(ctx, 'GET', '/onboarding/progress')
    if result and 'progress' in result:
        click.echo("🚀 Onboarding Progress:\n")
        for step in result['progress']:
            status = "✅" if step['completed'] else "⬜"
            click.echo(f"   {status} {step['title']}")

if __name__ == '__main__':
    cli()
