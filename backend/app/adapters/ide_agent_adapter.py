"""IDE Agent Adapter for FleetOps

Integration with IDE-based AI agents:
- Claude Code (Anthropic's CLI tool)
- GitHub Copilot (VS Code/JetBrains extension)
- Cursor (AI-powered IDE)
- GitHub Copilot Chat
- Cody (Sourcegraph)
- Tabnine
- Codeium
- Continue.dev

These agents work inside the development environment and use:
- CLI commands (Claude Code)
- LSP protocol (Copilot)
- WebSocket (Cursor, Continue.dev)
- Extension APIs

FleetOps integrates by:
1. Sending tasks to IDE agent via CLI/API
2. Receiving proposed changes (diffs)
3. Human reviews in FleetOps UI
4. Approved changes applied via git patch
"""

import os
import json
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from enum import Enum

class IDEAgentType(str, Enum):
    """Supported IDE-based agents"""
    CLAUDE_CODE = "claude_code"           # Anthropic's CLI
    COPILOT = "copilot"                   # GitHub Copilot
    CURSOR = "cursor"                     # Cursor IDE
    CODY = "cody"                         # Sourcegraph Cody
    TABNINE = "tabnine"                   # Tabnine
    CODEIUM = "codeium"                   # Codeium
    CONTINUE = "continue"                 # Continue.dev
    AIDER = "aider"                       # Aider (AI pair programming)
    DEVIN = "devin"                       # Cognition Devin
    ROO_CODE = "roo_code"                 # Roo Code (VS Code extension)


class ClaudeCodeAdapter:
    """FleetOps adapter for Claude Code (Anthropic)
    
    Claude Code is a CLI tool that:
    - Runs in terminal
    - Understands natural language
    - Edits files directly
    - Uses git for version control
    
    FleetOps integration:
    - Execute claude CLI commands
    - Capture proposed changes (git diff)
    - Present diff to human for approval
    - Apply approved changes via git
    """
    
    def __init__(self):
        self.cli_path = os.getenv("CLAUDE_CODE_CLI", "claude")
        self.timeout = int(os.getenv("CLAUDE_CODE_TIMEOUT", "600"))
        self.working_dir = os.getenv("CLAUDE_CODE_WORKDIR", "/tmp/claude-work")
        self.auto_commit = os.getenv("CLAUDE_CODE_AUTO_COMMIT", "false").lower() == "true"
    
    async def execute_task(self, task_id: str, instructions: str,
                          repo_path: Optional[str] = None,
                          files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute task using Claude Code CLI
        
        Args:
            task_id: FleetOps task ID
            instructions: Natural language instructions
            repo_path: Path to git repository
            files: Specific files to work on
        
        Returns:
            Execution result with diff
        """
        try:
            # Build command
            cmd = [
                self.cli_path,
                "--print",  # Print mode (non-interactive)
                "--output-format", "json",
            ]
            
            if repo_path:
                cmd.extend(["--working-dir", repo_path])
            
            # Add instructions
            cmd.append(instructions)
            
            # Run Claude Code
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=repo_path or self.working_dir
            )
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "error": f"Claude Code exited with code {result.returncode}",
                    "stderr": result.stderr[:1000]
                }
            
            # Parse output
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError:
                output = {"raw_output": result.stdout}
            
            # Get git diff of changes
            diff = await self._get_git_diff(repo_path or self.working_dir)
            
            return {
                "status": "success",
                "output": output,
                "diff": diff,
                "files_changed": self._parse_changed_files(diff),
                "requires_approval": True  # Always require approval for IDE agents
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": f"Claude Code timed out after {self.timeout}s"
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "error": f"Claude Code CLI not found at {self.cli_path}. Install with: npm install -g @anthropic-ai/claude-code"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_git_diff(self, repo_path: str) -> str:
        """Get git diff of changes"""
        try:
            result = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            return result.stdout
        except:
            return ""
    
    def _parse_changed_files(self, diff: str) -> List[str]:
        """Parse changed files from git diff"""
        files = []
        for line in diff.split('\n'):
            if line.startswith('diff --git'):
                parts = line.split(' ')
                if len(parts) >= 3:
                    file_path = parts[2].replace('b/', '')
                    files.append(file_path)
        return files
    
    async def apply_changes(self, repo_path: str, approved: bool = True) -> Dict[str, Any]:
        """Apply or discard changes
        
        If approved: git add + git commit
        If rejected: git checkout -- .
        """
        try:
            if approved:
                # Stage and commit changes
                subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True)
                
                if self.auto_commit:
                    subprocess.run(
                        ["git", "commit", "-m", f"Claude Code changes (FleetOps approved)"],
                        cwd=repo_path,
                        check=True
                    )
                
                return {
                    "status": "success",
                    "message": "Changes applied and staged"
                }
            else:
                # Discard changes
                subprocess.run(["git", "checkout", "--", "."], cwd=repo_path, check=True)
                
                return {
                    "status": "discarded",
                    "message": "Changes discarded"
                }
                
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error": f"Git operation failed: {e}"
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Check if Claude Code is available"""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return {
                "available": result.returncode == 0,
                "version": result.stdout.strip() if result.returncode == 0 else None
            }
        except:
            return {"available": False}


class CopilotAdapter:
    """FleetOps adapter for GitHub Copilot
    
    Copilot provides:
    - Code suggestions (inline)
    - Chat interface
    - PR summaries
    - Code explanations
    
    FleetOps integration:
    - Request code suggestions for tasks
    - Get PR summaries for review
    - Explain code changes
    """
    
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.api_base = "https://api.github.com"
        self.timeout = int(os.getenv("COPILOT_TIMEOUT", "300"))
        
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        } if self.github_token else {}
        
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def get_code_suggestions(self, code: str, language: str,
                                  task_id: str,
                                  context: Optional[str] = None) -> Dict[str, Any]:
        """Get code suggestions from Copilot
        
        Uses GitHub Copilot API (if available) or simulates
        with GitHub's code review API.
        """
        try:
            # In production, this would call Copilot's API
            # For now, we structure the request for future integration
            payload = {
                "prompt": f"# Task: {context or 'Improve this code'}\n\n```{language}\n{code}\n```",
                "language": language,
                "max_tokens": 500,
                "temperature": 0.2
            }
            
            # Return structured response
            return {
                "status": "success",
                "suggestions": [
                    {
                        "description": "Copilot suggestion (mock - requires GitHub Copilot API access)",
                        "code": "# Placeholder for Copilot suggestion",
                        "confidence": 0.9
                    }
                ],
                "requires_approval": True,
                "note": "Full Copilot integration requires GitHub Copilot Business/Enterprise API access"
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_pr_summary(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """Get Copilot-generated PR summary"""
        try:
            # Get PR details
            response = await self.client.get(
                f"/repos/{repo}/pulls/{pr_number}"
            )
            response.raise_for_status()
            pr = response.json()
            
            # Get diff
            diff_response = await self.client.get(
                f"/repos/{repo}/pulls/{pr_number}",
                headers={"Accept": "application/vnd.github.v3.diff"}
            )
            diff = diff_response.text
            
            # Generate summary (in production, this would use Copilot)
            summary = self._generate_summary(diff)
            
            return {
                "status": "success",
                "pr_title": pr.get("title"),
                "summary": summary,
                "files_changed": pr.get("changed_files", 0),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0)
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _generate_summary(self, diff: str) -> str:
        """Generate human-readable summary of diff"""
        files = []
        additions = 0
        deletions = 0
        
        for line in diff.split('\n'):
            if line.startswith('diff --git'):
                parts = line.split(' ')
                if len(parts) >= 3:
                    files.append(parts[2].replace('b/', ''))
            elif line.startswith('+') and not line.startswith('+++'):
                additions += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1
        
        return f"Modified {len(files)} files (+{additions}/-{deletions})"
    
    async def explain_code(self, code: str, language: str) -> Dict[str, Any]:
        """Get Copilot explanation of code"""
        return {
            "status": "success",
            "explanation": f"Code explanation for {language} (requires Copilot API)",
            "improvements": [
                "Consider adding error handling",
                "Add type hints for better clarity"
            ]
        }
    
    async def close(self):
        await self.client.aclose()


class CursorAdapter:
    """FleetOps adapter for Cursor IDE
    
    Cursor has:
    - AI chat (Cmd+L)
    - Cmd+K inline editing
    - Composer for multi-file edits
    - Agent mode for autonomous work
    
    FleetOps integration:
    - Trigger Cursor via CLI or API
    - Receive proposed changes
    - Review in FleetOps UI
    """
    
    def __init__(self):
        self.api_url = os.getenv("CURSOR_API_URL", "http://localhost:3001")
        self.api_key = os.getenv("CURSOR_API_KEY", "")
        self.timeout = int(os.getenv("CURSOR_TIMEOUT", "300"))
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def execute_composer(self, task_id: str, instructions: str,
                               files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute Cursor Composer task
        
        Composer is Cursor's multi-file editing feature.
        """
        try:
            payload = {
                "fleetops_task_id": task_id,
                "instructions": instructions,
                "files": files or [],
                "mode": "composer",  # composer, chat, agent
                "governance": {
                    "require_approval": True,
                    "max_files": 20
                }
            }
            
            response = await self.client.post("/api/v1/composer", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "success",
                "composition_id": data.get("id"),
                "proposed_changes": data.get("changes", []),
                "diff": data.get("diff"),
                "requires_approval": True
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get Cursor agent mode status"""
        try:
            response = await self.client.get(f"/api/v1/agents/{agent_id}")
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def approve_changes(self, composition_id: str,
                             approved: bool = True) -> Dict[str, Any]:
        """Approve or reject Cursor Composer changes"""
        try:
            payload = {"approved": approved}
            
            response = await self.client.post(
                f"/api/v1/composer/{composition_id}/approve",
                json=payload
            )
            return response.json()
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()


class AiderAdapter:
    """FleetOps adapter for Aider (AI pair programming)
    
    Aider is a CLI tool for AI pair programming:
    - Edit files in your local git repo
    - Works with multiple LLMs (GPT-4, Claude, etc.)
    - Automatic git commits
    - Undo changes with git
    
    FleetOps integration:
    - Execute aider commands
    - Review diffs
    - Approve/reject changes
    """
    
    def __init__(self):
        self.cli_path = os.getenv("AIDER_CLI", "aider")
        self.model = os.getenv("AIDER_MODEL", "gpt-4")
        self.timeout = int(os.getenv("AIDER_TIMEOUT", "600"))
    
    async def execute_task(self, task_id: str, instructions: str,
                          repo_path: str,
                          files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute task using Aider
        
        Example:
            aider --message "Refactor this function" file1.py file2.py
        """
        try:
            cmd = [
                self.cli_path,
                "--model", self.model,
                "--message", instructions,
                "--no-pretty",  # Plain output for parsing
                "--no-auto-commit"  # Don't auto-commit, let FleetOps handle it
            ]
            
            if files:
                cmd.extend(files)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=repo_path
            )
            
            # Get diff
            diff_result = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout,
                "diff": diff_result.stdout,
                "files_changed": self._parse_files_from_diff(diff_result.stdout),
                "requires_approval": True
            }
            
        except FileNotFoundError:
            return {
                "status": "error",
                "error": f"Aider not found. Install: pip install aider-chat"
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": f"Aider timed out after {self.timeout}s"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _parse_files_from_diff(self, diff: str) -> List[str]:
        """Parse files from git diff"""
        files = []
        for line in diff.split('\n'):
            if line.startswith('diff --git'):
                parts = line.split(' ')
                if len(parts) >= 3:
                    files.append(parts[2].replace('b/', ''))
        return files
    
    async def apply_changes(self, repo_path: str, approved: bool) -> Dict[str, Any]:
        """Apply or discard Aider changes"""
        try:
            if approved:
                subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True)
                return {"status": "applied"}
            else:
                subprocess.run(["git", "checkout", "--", "."], cwd=repo_path, check=True)
                return {"status": "discarded"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "error": str(e)}


class RooCodeAdapter:
    """FleetOps adapter for Roo Code
    
    Roo Code is a VS Code extension (forked from Cline) that:
    - Operates as an autonomous coding agent inside VS Code
    - Supports multiple LLM providers (Claude, OpenAI, Ollama, etc.)
    - Can read files, edit code, run terminal commands, use browser
    - Works with any codebase opened in VS Code
    - Has Plan/Act/Ask modes for different autonomy levels
    
    FleetOps integration:
    - Trigger Roo Code via CLI or API
    - Capture proposed changes (git diff)
    - Human reviews in FleetOps UI
    - Approve/reject changes via git patch
    """
    
    def __init__(self):
        self.cli_path = os.getenv("ROO_CODE_CLI", "roo")
        self.api_url = os.getenv("ROO_CODE_API_URL", "http://localhost:3002")
        self.api_key = os.getenv("ROO_CODE_API_KEY", "")
        self.timeout = int(os.getenv("ROO_CODE_TIMEOUT", "600"))
        self.working_dir = os.getenv("ROO_CODE_WORKDIR", "/tmp/roo-work")
        self.mode = os.getenv("ROO_CODE_MODE", "act")  # plan, act, ask
        self.model = os.getenv("ROO_CODE_MODEL", "claude-3-5-sonnet-20241022")
    
    async def execute_task(self, task_id: str, instructions: str,
                          repo_path: Optional[str] = None,
                          files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute task using Roo Code
        
        Args:
            task_id: FleetOps task ID
            instructions: Natural language instructions
            repo_path: Path to git repository
            files: Specific files to work on
        """
        try:
            # Build command for Roo Code CLI
            cmd = [
                self.cli_path,
                "--mode", self.mode,
                "--model", self.model,
                "--output", "json"
            ]
            
            if repo_path:
                cmd.extend(["--working-dir", repo_path])
            
            if files:
                cmd.extend(["--files"] + files)
            
            # Add instructions
            cmd.extend(["--message", instructions])
            
            # Run Roo Code
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=repo_path or self.working_dir
            )
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "error": f"Roo Code exited with code {result.returncode}",
                    "stderr": result.stderr[:1000]
                }
            
            # Parse output
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError:
                output = {"raw_output": result.stdout}
            
            # Get git diff of changes
            diff = await self._get_git_diff(repo_path or self.working_dir)
            
            return {
                "status": "success",
                "output": output,
                "diff": diff,
                "files_changed": self._parse_changed_files(diff),
                "requires_approval": True,  # Always require approval for IDE agents
                "mode": self.mode,
                "model": self.model
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": f"Roo Code timed out after {self.timeout}s"
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "error": f"Roo Code CLI not found at {self.cli_path}. Install: npm install -g @roocode/cli"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_git_diff(self, repo_path: str) -> str:
        """Get git diff of changes"""
        try:
            result = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            return result.stdout
        except:
            return ""
    
    def _parse_changed_files(self, diff: str) -> List[str]:
        """Parse changed files from git diff"""
        files = []
        for line in diff.split('\n'):
            if line.startswith('diff --git'):
                parts = line.split(' ')
                if len(parts) >= 3:
                    file_path = parts[2].replace('b/', '')
                    files.append(file_path)
        return files
    
    async def apply_changes(self, repo_path: str, approved: bool = True) -> Dict[str, Any]:
        """Apply or discard changes"""
        try:
            if approved:
                subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True)
                return {
                    "status": "success",
                    "message": "Changes applied and staged"
                }
            else:
                subprocess.run(["git", "checkout", "--", "."], cwd=repo_path, check=True)
                return {
                    "status": "discarded",
                    "message": "Changes discarded"
                }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error": f"Git operation failed: {e}"
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Check if Roo Code is available"""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return {
                "available": result.returncode == 0,
                "version": result.stdout.strip() if result.returncode == 0 else None
            }
        except:
            return {"available": False}


class DevinAdapter:
    """FleetOps adapter for Cognition Devin
    
    Devin is an autonomous AI software engineer:
    - Plans and executes complex engineering tasks
    - Uses browser, terminal, and code editor
    - Can deploy applications
    
    FleetOps integration:
    - Assign tasks to Devin
    - Monitor progress
    - Review completed work
    """
    
    def __init__(self):
        self.api_url = os.getenv("DEVIN_API_URL", "https://api.cognition.ai")
        self.api_key = os.getenv("DEVIN_API_KEY", "")
        self.timeout = int(os.getenv("DEVIN_TIMEOUT", "3600"))
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def create_session(self, task_id: str, prompt: str,
                          capabilities: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a Devin session
        
        Args:
            task_id: FleetOps task ID
            prompt: Task description
            capabilities: List of capabilities (browse, code, deploy)
        """
        try:
            payload = {
                "fleetops_task_id": task_id,
                "prompt": prompt,
                "capabilities": capabilities or ["code", "browse"],
                "governance": {
                    "require_approval_before_deploy": True,
                    "notify_on_milestones": True
                }
            }
            
            response = await self.client.post("/api/v1/sessions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "created",
                "session_id": data.get("id"),
                "url": data.get("url"),
                "devin_data": data
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get Devin session status"""
        try:
            response = await self.client.get(f"/api/v1/sessions/{session_id}")
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": data.get("status"),
                "progress": data.get("progress"),
                "current_action": data.get("current_action"),
                "completed_actions": data.get("completed_actions", []),
                "artifacts": data.get("artifacts", []),
                "requires_approval": data.get("pending_approval") is not None,
                "pending_approval": data.get("pending_approval")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def approve_action(self, session_id: str, action_id: str,
                            approved: bool = True,
                            comments: Optional[str] = None) -> Dict[str, Any]:
        """Approve a pending Devin action"""
        try:
            payload = {
                "action_id": action_id,
                "approved": approved,
                "comments": comments or ""
            }
            
            response = await self.client.post(
                f"/api/v1/sessions/{session_id}/actions/{action_id}/approve",
                json=payload
            )
            return response.json()
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_artifacts(self, session_id: str) -> List[Dict]:
        """Get artifacts produced by Devin"""
        try:
            response = await self.client.get(f"/api/v1/sessions/{session_id}/artifacts")
            return response.json().get("artifacts", [])
        except:
            return []
    
    async def close(self):
        await self.client.aclose()


class UnifiedIDEAgentAdapter:
    """Unified adapter for all IDE-based agents
    
    Provides common interface for:
    - Claude Code
    - Copilot
    - Cursor
    - Aider
    - Devin
    - And others
    """
    
    def __init__(self, agent_type: IDEAgentType):
        self.agent_type = agent_type
        self._adapter = None
        self._initialize()
    
    def _initialize(self):
        """Initialize specific adapter"""
        if self.agent_type == IDEAgentType.CLAUDE_CODE:
            self._adapter = ClaudeCodeAdapter()
        elif self.agent_type == IDEAgentType.COPILOT:
            self._adapter = CopilotAdapter()
        elif self.agent_type == IDEAgentType.CURSOR:
            self._adapter = CursorAdapter()
        elif self.agent_type == IDEAgentType.AIDER:
            self._adapter = AiderAdapter()
        elif self.agent_type == IDEAgentType.ROO_CODE:
            self._adapter = RooCodeAdapter()
        elif self.agent_type == IDEAgentType.DEVIN:
            self._adapter = DevinAdapter()
        else:
            raise ValueError(f"Unsupported IDE agent: {self.agent_type}")
    
    async def execute(self, task_id: str, instructions: str,
                     context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute task with IDE agent
        
        Common flow:
        1. Execute task
        2. Get diff/changes
        3. Return for human approval
        """
        context = context or {}
        
        if self.agent_type == IDEAgentType.CLAUDE_CODE:
            return await self._adapter.execute_task(
                task_id=task_id,
                instructions=instructions,
                repo_path=context.get("repo_path"),
                files=context.get("files")
            )
        
        elif self.agent_type == IDEAgentType.COPILOT:
            return await self._adapter.get_code_suggestions(
                code=context.get("code", ""),
                language=context.get("language", "python"),
                task_id=task_id,
                context=instructions
            )
        
        elif self.agent_type == IDEAgentType.CURSOR:
            return await self._adapter.execute_composer(
                task_id=task_id,
                instructions=instructions,
                files=context.get("files")
            )
        
        elif self.agent_type == IDEAgentType.AIDER:
            return await self._adapter.execute_task(
                task_id=task_id,
                instructions=instructions,
                repo_path=context.get("repo_path", "."),
                files=context.get("files")
            )
        
        elif self.agent_type == IDEAgentType.ROO_CODE:
            return await self._adapter.execute_task(
                task_id=task_id,
                instructions=instructions,
                repo_path=context.get("repo_path"),
                files=context.get("files")
            )
        
        elif self.agent_type == IDEAgentType.DEVIN:
            return await self._adapter.create_session(
                task_id=task_id,
                prompt=instructions,
                capabilities=context.get("capabilities")
            )
        
        else:
            return {"status": "error", "error": f"Execution not implemented for {self.agent_type}"}
    
    async def approve_changes(self, execution_id: str, approved: bool = True,
                             context: Optional[Dict] = None) -> Dict[str, Any]:
        """Approve or reject changes"""
        context = context or {}
        
        if self.agent_type in [IDEAgentType.CLAUDE_CODE, IDEAgentType.AIDER, IDEAgentType.ROO_CODE]:
            return await self._adapter.apply_changes(
                repo_path=context.get("repo_path", "."),
                approved=approved
            )
        
        elif self.agent_type == IDEAgentType.CURSOR:
            return await self._adapter.approve_changes(execution_id, approved)
        
        elif self.agent_type == IDEAgentType.DEVIN:
            return await self._adapter.approve_action(execution_id, "action_1", approved)
        
        else:
            return {"status": "not_supported"}
    
    async def get_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status"""
        if self.agent_type == IDEAgentType.DEVIN:
            return await self._adapter.get_session_status(execution_id)
        elif self.agent_type == IDEAgentType.CURSOR:
            return await self._adapter.get_agent_status(execution_id)
        else:
            return {"status": "completed"}  # Others are synchronous
    
    def get_capabilities(self) -> List[str]:
        """Get capabilities for this agent type"""
        capabilities = {
            IDEAgentType.CLAUDE_CODE: [
                "cli_execution",
                "file_editing",
                "git_integration",
                "natural_language",
                "full_project_context"
            ],
            IDEAgentType.COPILOT: [
                "code_suggestions",
                "inline_completion",
                "pr_summaries",
                "code_explanation"
            ],
            IDEAgentType.CURSOR: [
                "composer_multi_file",
                "chat_interface",
                "agent_mode",
                "inline_editing"
            ],
            IDEAgentType.CODY: [
                "code_intelligence",
                "repo_search",
                "code_explanation"
            ],
            IDEAgentType.AIDER: [
                "pair_programming",
                "git_aware",
                "multi_llm",
                "automatic_commits"
            ],
            IDEAgentType.ROO_CODE: [
                "vs_code_extension",
                "multi_llm_support",
                "plan_mode",
                "act_mode",
                "browser_usage",
                "terminal_commands",
                "file_editing",
                "git_integration",
                "autonomous_coding"
            ],
            IDEAgentType.DEVIN: [
                "autonomous_execution",
                "browser_usage",
                "deployment",
                "complex_planning"
            ]
        }
        return capabilities.get(self.agent_type, ["generic"])
    
    async def close(self):
        """Close adapter connections"""
        if hasattr(self._adapter, 'close'):
            await self._adapter.close()


# Singleton instances
claude_code_adapter = ClaudeCodeAdapter()
copilot_adapter = CopilotAdapter()
cursor_adapter = CursorAdapter()
aider_adapter = AiderAdapter()
devin_adapter = DevinAdapter()
