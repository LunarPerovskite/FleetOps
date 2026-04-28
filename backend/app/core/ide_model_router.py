"""IDE Agent Model Router

Handles model switching for IDE-based agents:
- Cline (VS Code extension)
- Cursor (AI IDE)
- GitHub Copilot
- Continue.dev
- Roo Code
- Aider

Each IDE has its own way of switching models:
- Cline: Settings -> API Provider dropdown
- Cursor: Settings -> AI -> Model
- Copilot: .github/copilot.yml or VS Code settings
- Continue.dev: config.json
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json
import os

from app.core.model_registry import ModelRegistry, LLMModel, ModelCapability
from app.core.agent_model_manager import AgentModelManager, AgentModelConfig
from app.core.logging_config import get_logger

logger = get_logger("fleetops.ide_router")


class IDEType(str, Enum):
    """Supported IDE/agent platforms"""
    CLINE = "cline"
    CURSOR = "cursor"
    COPILOT = "copilot"
    CONTINUE = "continue"
    ROO_CODE = "roo_code"
    AIDER = "aider"
    CLAUDE_CODE = "claude_code"
    CUSTOM = "custom"


@dataclass
class IDEModelMapping:
    """How FleetOps models map to IDE-specific model names"""
    fleetops_model: str
    ide_model_name: str       # What the IDE calls it
    ide_provider: str         # What the IDE calls the provider
    
    # IDE-specific config
    api_key_env: str = ""     # Environment variable for API key
    base_url: Optional[str] = None
    extra_headers: Optional[Dict] = None


class IDEModelRouter:
    """Routes model changes to IDE configurations"""
    
    # IDE-specific model name mappings
    IDE_MAPPINGS: Dict[IDEType, Dict[str, IDEModelMapping]] = {
        IDEType.CLINE: {
            "gpt-4o": IDEModelMapping("gpt-4o", "gpt-4o", "openai", "OPENAI_API_KEY"),
            "gpt-4o-mini": IDEModelMapping("gpt-4o-mini", "gpt-4o-mini", "openai", "OPENAI_API_KEY"),
            "claude-3-5-sonnet": IDEModelMapping("claude-3-5-sonnet", "claude-3-5-sonnet-20241022", "anthropic", "ANTHROPIC_API_KEY"),
            "claude-3-opus": IDEModelMapping("claude-3-opus", "claude-3-opus-20240229", "anthropic", "ANTHROPIC_API_KEY"),
            "gemini-1.5-pro": IDEModelMapping("gemini-1.5-pro", "gemini-1.5-pro", "gemini", "GEMINI_API_KEY"),
            "gemini-1.5-flash": IDEModelMapping("gemini-1.5-flash", "gemini-1.5-flash", "gemini", "GEMINI_API_KEY"),
            "azure-gpt-4o": IDEModelMapping("azure-gpt-4o", "gpt-4o", "azure", "AZURE_OPENAI_API_KEY", 
                                             base_url="${AZURE_OPENAI_ENDPOINT}"),
        },
        IDEType.CURSOR: {
            "gpt-4o": IDEModelMapping("gpt-4o", "gpt-4o", "openai", "OPENAI_API_KEY"),
            "claude-3-5-sonnet": IDEModelMapping("claude-3-5-sonnet", "claude-3-5-sonnet", "anthropic", "ANTHROPIC_API_KEY"),
            "claude-3-opus": IDEModelMapping("claude-3-opus", "claude-3-opus", "anthropic", "ANTHROPIC_API_KEY"),
        },
        IDEType.COPILOT: {
            "gpt-4o": IDEModelMapping("gpt-4o", "gpt-4o", "copilot", ""),
            # Copilot uses GitHub's models, limited choice
        },
        IDEType.CONTINUE: {
            "gpt-4o": IDEModelMapping("gpt-4o", "gpt-4o", "openai", "OPENAI_API_KEY"),
            "gpt-4o-mini": IDEModelMapping("gpt-4o-mini", "gpt-4o-mini", "openai", "OPENAI_API_KEY"),
            "claude-3-5-sonnet": IDEModelMapping("claude-3-5-sonnet", "claude-3-5-sonnet-20241022", "anthropic", "ANTHROPIC_API_KEY"),
            "gemini-1.5-pro": IDEModelMapping("gemini-1.5-pro", "gemini-1.5-pro", "gemini", "GEMINI_API_KEY"),
            "gemini-1.5-flash": IDEModelMapping("gemini-1.5-flash", "gemini-1.5-flash", "gemini", "GEMINI_API_KEY"),
        },
        IDEType.ROO_CODE: {
            "gpt-4o": IDEModelMapping("gpt-4o", "gpt-4o", "openai", "OPENAI_API_KEY"),
            "claude-3-5-sonnet": IDEModelMapping("claude-3-5-sonnet", "claude-3-5-sonnet-20241022", "anthropic", "ANTHROPIC_API_KEY"),
            "gemini-1.5-pro": IDEModelMapping("gemini-1.5-pro", "gemini-1.5-pro", "gemini", "GEMINI_API_KEY"),
        },
        IDEType.AIDER: {
            "gpt-4o": IDEModelMapping("gpt-4o", "gpt-4o", "openai", "OPENAI_API_KEY"),
            "claude-3-5-sonnet": IDEModelMapping("claude-3-5-sonnet", "claude-3-5-sonnet-20241022", "anthropic", "ANTHROPIC_API_KEY"),
            "gemini-1.5-pro": IDEModelMapping("gemini-1.5-pro", "gemini-1.5-pro", "gemini", "GEMINI_API_KEY"),
        },
        IDEType.CLAUDE_CODE: {
            "claude-3-5-sonnet": IDEModelMapping("claude-3-5-sonnet", "claude-3-5-sonnet-20241022", "anthropic", "ANTHROPIC_API_KEY"),
            "claude-3-opus": IDEModelMapping("claude-3-opus", "claude-3-opus-20240229", "anthropic", "ANTHROPIC_API_KEY"),
            "claude-3-haiku": IDEModelMapping("claude-3-haiku", "claude-3-haiku-20240307", "anthropic", "ANTHROPIC_API_KEY"),
        },
    }
    
    def __init__(self, model_manager: Optional[AgentModelManager] = None):
        self.model_manager = model_manager or AgentModelManager()
        self.registry = self.model_manager.registry
    
    def get_ide_config(self, ide_type: IDEType, model_id: str) -> Optional[Dict[str, Any]]:
        """Generate IDE-specific configuration for a model"""
        
        mapping = self.IDE_MAPPINGS.get(ide_type, {}).get(model_id)
        if not mapping:
            logger.warning(f"No mapping for {ide_type} -> {model_id}")
            return None
        
        model = self.registry.get(model_id)
        if not model:
            return None
        
        # Generate config based on IDE type
        if ide_type == IDEType.CLINE:
            return self._cline_config(mapping, model)
        elif ide_type == IDEType.CURSOR:
            return self._cursor_config(mapping, model)
        elif ide_type == IDEType.CONTINUE:
            return self._continue_config(mapping, model)
        elif ide_type == IDEType.ROO_CODE:
            return self._roo_code_config(mapping, model)
        elif ide_type == IDEType.AIDER:
            return self._aider_config(mapping, model)
        elif ide_type == IDEType.CLAUDE_CODE:
            return self._claude_code_config(mapping, model)
        elif ide_type == IDEType.COPILOT:
            return self._copilot_config(mapping, model)
        
        return None
    
    def _cline_config(self, mapping: IDEModelMapping, model: LLMModel) -> Dict[str, Any]:
        """Generate Cline VS Code extension config"""
        return {
            "apiProvider": mapping.ide_provider,
            "apiModelId": mapping.ide_model_name,
            "openAiCustomModelInfo": {
                "maxTokens": model.max_output_tokens,
                "contextWindow": model.max_input_tokens,
                "supportsImages": ModelCapability.VISION in model.capabilities,
                "supportsComputerUse": False,
                "supportsPromptCache": mapping.ide_provider == "anthropic",
                "inputPrice": model.input_cost_per_1m,
                "outputPrice": model.output_cost_per_1m,
            }
        }
    
    def _cursor_config(self, mapping: IDEModelMapping, model: LLMModel) -> Dict[str, Any]:
        """Generate Cursor IDE config"""
        return {
            "model": mapping.ide_model_name,
            "provider": mapping.ide_provider,
            "apiKey": f"${{{mapping.api_key_env}}}" if mapping.api_key_env else "",
        }
    
    def _continue_config(self, mapping: IDEModelMapping, model: LLMModel) -> Dict[str, Any]:
        """Generate Continue.dev config"""
        config = {
            "title": model.name,
            "provider": mapping.ide_provider,
            "model": mapping.ide_model_name,
            "apiKey": f"${{{mapping.api_key_env}}}" if mapping.api_key_env else "",
        }
        if mapping.base_url:
            config["apiBase"] = mapping.base_url
        return config
    
    def _roo_code_config(self, mapping: IDEModelMapping, model: LLMModel) -> Dict[str, Any]:
        """Generate Roo Code (Cline fork) config"""
        return {
            "apiProvider": mapping.ide_provider,
            "apiModelId": mapping.ide_model_name,
            "openAiCustomModelInfo": {
                "maxTokens": model.max_output_tokens,
                "contextWindow": model.max_input_tokens,
                "supportsImages": ModelCapability.VISION in model.capabilities,
            }
        }
    
    def _aider_config(self, mapping: IDEModelMapping, model: LLMModel) -> Dict[str, Any]:
        """Generate Aider config (CLI flags)"""
        return {
            "model": f"{mapping.ide_provider}/{mapping.ide_model_name}",
            "api_key_env": mapping.api_key_env,
            "edit_format": "diff" if ModelCapability.CODE in model.capabilities else "whole",
        }
    
    def _claude_code_config(self, mapping: IDEModelMapping, model: LLMModel) -> Dict[str, Any]:
        """Generate Claude Code CLI config"""
        return {
            "model": mapping.ide_model_name,
            "provider": mapping.ide_provider,
        }
    
    def _copilot_config(self, mapping: IDEModelMapping, model: LLMModel) -> Dict[str, Any]:
        """Generate GitHub Copilot config"""
        return {
            "model": mapping.ide_model_name,
        }
    
    def get_available_models(self, ide_type: IDEType) -> List[Dict[str, Any]]:
        """Get list of models available for a specific IDE"""
        mappings = self.IDE_MAPPINGS.get(ide_type, {})
        
        models = []
        for model_id, mapping in mappings.items():
            model = self.registry.get(model_id)
            if model and model.is_available:
                models.append({
                    "id": model_id,
                    "name": model.name,
                    "provider": model.provider,
                    "ide_name": mapping.ide_model_name,
                    "cost_per_1m": {
                        "input": model.input_cost_per_1m,
                        "output": model.output_cost_per_1m
                    },
                    "capabilities": [c.value for c in model.capabilities],
                    "max_tokens": model.max_total_tokens
                })
        
        return sorted(models, key=lambda m: m["cost_per_1m"]["input"])
    
    def generate_switch_command(self, ide_type: IDEType, model_id: str) -> Optional[str]:
        """Generate a shell command or script to switch models in an IDE"""
        
        mapping = self.IDE_MAPPINGS.get(ide_type, {}).get(model_id)
        if not mapping:
            return None
        
        if ide_type == IDEType.AIDER:
            return f"aider --model {mapping.ide_provider}/{mapping.ide_model_name}"
        
        elif ide_type == IDEType.CLAUDE_CODE:
            return f"claude --model {mapping.ide_model_name}"
        
        elif ide_type == IDEType.COPILOT:
            return "# Copilot models are set in VS Code settings"
        
        elif ide_type == IDEType.CONTINUE:
            return (
                f"# Add to ~/.continue/config.json:\n"
                f'  "models": [{{\n'
                f'    "title": "{mapping.ide_model_name}",\n'
                f'    "provider": "{mapping.ide_provider}",\n'
                f'    "model": "{mapping.ide_model_name}"\n'
                f'  }}]'
            )
        
        return None
    
    def switch_model(self,
                    agent_id: str,
                    ide_type: IDEType,
                    new_model_id: str) -> Dict[str, Any]:
        """Switch an agent's model and generate IDE config"""
        
        # Update FleetOps config
        success = self.model_manager.set_model(agent_id, new_model_id)
        if not success:
            return {
                "status": "error",
                "error": f"Failed to switch to {new_model_id}"
            }
        
        # Generate IDE-specific config
        ide_config = self.get_ide_config(ide_type, new_model_id)
        
        # Generate switch command
        switch_command = self.generate_switch_command(ide_type, new_model_id)
        
        model = self.registry.get(new_model_id)
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "new_model": new_model_id,
            "model_name": model.name if model else new_model_id,
            "ide_type": ide_type.value,
            "ide_config": ide_config,
            "switch_command": switch_command,
            "message": f"Switched to {model.name if model else new_model_id}"
        }
    
    def get_user_ide_setup(self, user_id: str, ide_type: IDEType) -> Dict[str, Any]:
        """Get complete setup guide for a user's IDE"""
        
        available = self.get_available_models(ide_type)
        
        # Find user's current agents
        agents = []
        for agent_id, config in self.model_manager._configs.items():
            if config.user_id == user_id:
                model = self.registry.get(config.primary_model)
                mapping = self.IDE_MAPPINGS.get(ide_type, {}).get(config.primary_model)
                
                agents.append({
                    "agent_id": agent_id,
                    "current_model": config.primary_model,
                    "model_name": model.name if model else config.primary_model,
                    "ide_name": mapping.ide_model_name if mapping else "unknown",
                    "strategy": config.strategy.value
                })
        
        return {
            "user_id": user_id,
            "ide_type": ide_type.value,
            "available_models": available,
            "configured_agents": agents,
            "setup_instructions": self._get_setup_instructions(ide_type),
            "env_vars_required": list(set(
                m.api_key_env 
                for models in self.IDE_MAPPINGS.get(ide_type, {}).values()
                for m in [models] if hasattr(m, 'api_key_env') and m.api_key_env
            ))
        }
    
    def _get_setup_instructions(self, ide_type: IDEType) -> str:
        """Get setup instructions for an IDE"""
        instructions = {
            IDEType.CLINE: (
                "1. Install Cline VS Code extension\n"
                "2. Set API key in VS Code settings or env var\n"
                "3. Select model from dropdown\n"
                "4. FleetOps will track usage automatically"
            ),
            IDEType.CURSOR: (
                "1. Install Cursor IDE\n"
                "2. Go to Settings -> AI\n"
                "3. Select model from dropdown\n"
                "4. Add API key if using non-default provider"
            ),
            IDEType.COPILOT: (
                "1. Install GitHub Copilot extension\n"
                "2. Sign in with GitHub\n"
                "3. Models are managed by GitHub\n"
                "4. Limited to Copilot's available models"
            ),
            IDEType.CONTINUE: (
                "1. Install Continue.dev extension\n"
                "2. Edit ~/.continue/config.json\n"
                "3. Add model configuration from above\n"
                "4. Restart the IDE"
            ),
            IDEType.AIDER: (
                "1. Install aider: pip install aider-chat\n"
                "2. Set API key in environment\n"
                "3. Run: aider --model provider/model\n"
                "4. FleetOps tracks via MCP or CLI"
            ),
            IDEType.ROO_CODE: (
                "1. Install Roo Code VS Code extension\n"
                "2. Similar to Cline setup\n"
                "3. Select provider and model\n"
                "4. FleetOps integration via API"
            ),
        }
        return instructions.get(ide_type, "See IDE documentation for setup")


# Singleton
ide_router = IDEModelRouter()


# ═══════════════════════════════════════
# API ENDPOINTS (for integration)
# ═══════════════════════════════════════

def get_available_models_for_ide(ide_type: str) -> List[Dict[str, Any]]:
    """API: Get available models for an IDE"""
    try:
        ide = IDEType(ide_type)
        return ide_router.get_available_models(ide)
    except ValueError:
        return []

def switch_agent_model(agent_id: str, ide_type: str, model_id: str) -> Dict[str, Any]:
    """API: Switch an agent's model for an IDE"""
    try:
        ide = IDEType(ide_type)
        return ide_router.switch_model(agent_id, ide, model_id)
    except ValueError as e:
        return {"status": "error", "error": str(e)}

def get_ide_setup_guide(user_id: str, ide_type: str) -> Dict[str, Any]:
    """API: Get setup guide for a user's IDE"""
    try:
        ide = IDEType(ide_type)
        return ide_router.get_user_ide_setup(user_id, ide)
    except ValueError as e:
        return {"status": "error", "error": str(e)}