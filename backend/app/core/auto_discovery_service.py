"""Auto-Discovery Service for FleetOps

Automatically detects models when API keys are configured.
Uses the model_providers.py connectors for all supported providers.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.core.logging_config import get_logger
from app.core.model_registry import model_registry, LLMModel, ModelCapability, ModelTier
from app.core.model_discovery import discovery_service
from app.core.model_providers import (
    OpenAIConnector, AnthropicConnector, GeminiConnector,
    CohereConnector, MistralConnector,
    DeepSeekConnector, ZaiConnector, MiniMaxConnector,
    ElevenLabsConnector, OllamaConnector
)

logger = get_logger("fleetops.auto_discovery")


class AutoDiscoveryService:
    """Automatically discovers models when API keys are available"""

    # Map provider name -> connector class from model_providers.py
    ADAPTER_MAP = {
        "openai": OpenAIConnector,
        "anthropic": AnthropicConnector,
        "gemini": GeminiConnector,
        "cohere": CohereConnector,
        "mistral": MistralConnector,
        "deepseek": DeepSeekConnector,
        "zai": ZaiConnector,
        "minimax": MiniMaxConnector,
        "elevenlabs": ElevenLabsConnector,
        "ollama": OllamaConnector,
    }

    # Map provider name -> env var for API key
    ENV_KEY_MAP = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "cohere": "COHERE_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "zai": "ZAI_API_KEY",
        "minimax": "MINIMAX_API_KEY",
        "elevenlabs": "ELEVENLABS_API_KEY",
        "ollama": "OLLAMA_BASE_URL",
    }

    async def discover_provider(self, provider: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Discover models from a provider given an API key"""

        connector_class = self.ADAPTER_MAP.get(provider)
        if not connector_class:
            logger.warning(f"No connector for provider: {provider}")
            return []

        # Use provided key or fall back to env
        key = api_key or os.getenv(self.ENV_KEY_MAP.get(provider, ""), "")
        if not key:
            logger.info(f"No API key for {provider}, skipping discovery")
            return []

        connector = connector_class(api_key=key)
        try:
            models = await connector.list_models()
            logger.info(f"Discovered {len(models)} models from {provider}")

            # Enrich and register
            for m in models:
                model_data = self._normalize_model(m, provider)
                discovery_service._discovered_models[model_data["id"]] = model_data
                discovery_service.register_model(model_data)

            return models
        except Exception as e:
            logger.error(f"Discovery failed for {provider}: {e}")
            return []
        finally:
            await connector.close()

    async def discover_all_configured(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover from all providers that have API keys configured"""

        results = {}
        tasks = []

        for provider in self.ADAPTER_MAP.keys():
            task = asyncio.create_task(self.discover_provider(provider))
            tasks.append((provider, task))

        for provider, task in tasks:
            try:
                models = await task
                results[provider] = models
            except Exception as e:
                logger.error(f"Task failed for {provider}: {e}")
                results[provider] = []

        total = sum(len(v) for v in results.values())
        logger.info(f"Auto-discovery complete: {total} models from {len(results)} providers")

        return results

    def _normalize_model(self, raw: Dict, provider: str) -> Dict[str, Any]:
        """Normalize connector model output to discovery format"""

        model_id = raw.get("id", "")
        if "/" not in model_id:
            model_id = f"{provider}/{model_id}"

        return {
            "id": model_id,
            "name": raw.get("name", model_id),
            "provider": provider,
            "provider_model_id": raw.get("provider_model_id", raw.get("id", "").split("/")[-1]),
            "type": raw.get("type", "chat"),
            "context_length": raw.get("context_length", 128000),
            "pricing": raw.get("pricing", {"input": 0, "output": 0}),
            "capabilities": raw.get("capabilities", ["chat"]),
            "discovered_from": provider,
            "discovered_at": datetime.utcnow().isoformat(),
        }

    async def refresh_on_key_update(self, provider: str, api_key: str) -> Dict[str, Any]:
        """Called when a user updates an API key in settings.
        Returns the discovered models immediately."""

        models = await self.discover_provider(provider, api_key)

        return {
            "provider": provider,
            "models_discovered": len(models),
            "models": [
                {
                    "id": m.get("id", ""),
                    "name": m.get("name", ""),
                    "capabilities": m.get("capabilities", []),
                }
                for m in models
            ]
        }

    def get_provider_status(self) -> List[Dict[str, Any]]:
        """Get status of all providers (has key?, models count)"""

        status = []
        for provider, env_var in self.ENV_KEY_MAP.items():
            key = os.getenv(env_var, "")

            # Count registered models for this provider
            count = len([
                m for m in model_registry._models.values()
                if m.provider == provider
            ])

            status.append({
                "provider": provider,
                "has_api_key": bool(key),
                "env_var": env_var,
                "models_registered": count,
                "connector_available": provider in self.ADAPTER_MAP,
            })

        return status


# Singleton
auto_discovery = AutoDiscoveryService()
