# FleetOps MCP Server

Model Context Protocol (MCP) server for FleetOps — connect any MCP-compatible agent to governance, approvals, and cost tracking.

## Why MCP?

MCP is the modern standard for agent-tool connections. Instead of custom integrations for every agent, you get:

- **One protocol** for all agents
- **Standardized tools** and resources
- **Automatic discovery** — agents see available tools
- **Type-safe** interactions

## Installation

```bash
pip install fleetops-mcp
```

Or from source:
```bash
cd mcp-server
pip install -e .
```

## Configuration

### Environment Variables
```bash
export FLEETOPS_API_URL="http://localhost:8000"
export FLEETOPS_API_KEY="your-api-key"  # optional
export FLEETOPS_ORG_ID="default"
```

### Claude Desktop Config

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fleetops": {
      "command": "python",
      "args": ["-m", "fleetops_mcp.server"],
      "env": {
        "FLEETOPS_API_URL": "http://localhost:8000",
        "FLEETOPS_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Available Tools

### `request_approval`
Request approval before executing a potentially dangerous action.

**When to use:** Before any command that might:
- Delete files or data
- Modify production systems
- Execute shell commands
- Make API calls that cost money
- Access sensitive files

**Parameters:**
- `action` (string): Type of action (bash, write, delete, api, db)
- `arguments` (string): Command or arguments being executed
- `file_path` (string): File being modified
- `environment` (string): development, staging, production
- `estimated_cost` (float): Estimated cost in USD
- `agent_name` (string): Name of the agent

**Returns:**
```json
{
  "can_proceed": true,
  "status": "approved",
  "danger_level": "medium",
  "message": "Approved. Agent can proceed."
}
```

### `track_execution_cost`
Track the cost of an executed action.

**When to use:** After executing an action to report actual costs.

**Parameters:**
- `action` (string): Description of what was executed
- `cost` (float): Actual cost in USD
- `tokens` (int): Number of tokens consumed
- `duration` (float): Execution time in seconds
- `agent_id` (string): ID of the agent

### `get_pending_approvals`
Get list of pending approvals that need human action.

**Returns:** List of pending approvals with IDs, agents, actions.

### `approve_request`
Approve a pending request.

**Parameters:**
- `approval_id` (string): ID of the approval
- `scope` (string): once, session, workspace, always
- `comments` (string): Optional comments

### `check_danger_level`
Preview danger level without requesting approval.

**Parameters:**
- `action` (string): Type of action
- `arguments` (string): Command arguments
- `file_path` (string): Target file
- `environment` (string): Environment

**Returns:** Danger level and whether approval would be required.

## Available Resources

### `fleetops://status`
Get current FleetOps system status (JSON).

### `fleetops://pending`
Get pending approvals (JSON).

### `fleetops://agents`
Get active agents (JSON).

### `fleetops://costs`
Get cost summary (JSON).

## Usage Example

### In Claude Desktop:

```
User: Delete the old database
Claude: I'll check with FleetOps before deleting anything.

[Claude calls request_approval with action="bash", arguments="dropdb old_db"]

FleetOps: ❌ BLOCKED: High risk action detected
Danger level: HIGH
Approval required: Yes

Claude: FleetOps has blocked this action because it's high risk. 
You need to approve it in the FleetOps dashboard or Slack.
```

### In Claude Code:

```python
# Before executing any tool
approval = await mcp_client.call_tool("request_approval", {
    "action": "bash",
    "arguments": "rm -rf /tmp/data",
    "environment": "development"
})

if approval.can_proceed:
    # Execute the command
    os.system("rm -rf /tmp/data")
    
    # Track cost
    await mcp_client.call_tool("track_execution_cost", {
        "action": "rm -rf /tmp/data",
        "cost": 0.0,
        "duration": 0.5
    })
else:
    print(f"Blocked: {approval.message}")
```

## Architecture

```
Claude Desktop / Claude Code / Roo Code / Cursor
    ↓
MCP Protocol (stdio or HTTP)
    ↓
fleetops-mcp server
    ↓
FleetOps API (REST)
    ↓
Danger Detection → Approval Flow → Cost Tracking
```

## Agent Support

| Agent | Status | Notes |
|-------|--------|-------|
| Claude Desktop | ✅ | Add to claude_desktop_config.json |
| Claude Code | ✅ | Use `--mcp` flag or config |
| Roo Code | ✅ | Add MCP server in settings |
| Cursor | ✅ | Add MCP server in settings |
| Any MCP client | ✅ | Standard MCP protocol |

## Development

```bash
# Run locally
python fleetops-mcp.py

# Run with stdio (for Claude Desktop)
python fleetops-mcp.py --transport stdio

# Test
pytest tests/
```

## License

MIT
