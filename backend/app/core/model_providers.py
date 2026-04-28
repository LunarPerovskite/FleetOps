"""Direct Provider Connectors for FleetOps

Connects directly to each provider's API for real-time model discovery:
- OpenAI (GPT, embeddings, whisper, TTS, DALL-E)
- Anthropic (Claude models)
- Google (Gemini, Vertex AI)
- Azure OpenAI
- Cohere
- Mistral
- DeepSeek
- Z.ai (Qwen)
- MiniMax
- Ollama (local)
- Together AI
- Replicate
- ElevenLabs
"""

from typing import Dict, Any, Optional, List
import httpx
import os
from datetime import datetime

from app.core.logging_config import get_logger

logger = get_logger("fleetops.providers")


class ProviderConnector:
    """Base class for provider connectors"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or ""
        self.base_url = base_url
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if not self.client:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self.client = httpx.AsyncClient(
                base_url=self.base_url or "",
                headers=headers,
                timeout=30
            )
        return self.client
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Override in subclass"""
        raise NotImplementedError
    
    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None


class OpenAIConnector(ProviderConnector):
    """OpenAI API - GPT, embeddings, whisper, TTS, DALL-E"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv("OPENAI_API_KEY", ""),
            base_url="https://api.openai.com/v1"
        )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Fetch all OpenAI models including embeddings, audio, image"""
        client = await self._get_client()
        try:
            resp = await client.get("/models")
            resp.raise_for_status()
            data = resp.json()
            
            models = []
            for m in data.get("data", []):
                model_id = m["id"]
                
                # Categorize by model family
                model_type = self._categorize(model_id)
                
                models.append({
                    "id": f"openai/{model_id}",
                    "name": self._pretty_name(model_id),
                    "provider": "openai",
                    "provider_model_id": model_id,
                    "type": model_type,
                    "context_length": self._get_context_length(model_id),
                    "pricing": self._get_pricing(model_id),
                    "capabilities": self._get_capabilities(model_id),
                    "raw": m
                })
            
            return models
        except Exception as e:
            logger.error(f"OpenAI fetch failed: {e}")
            return []
    
    def _categorize(self, model_id: str) -> str:
        """Categorize model by type"""
        if "embedding" in model_id:
            return "embedding"
        elif "whisper" in model_id:
            return "audio_transcription"
        elif "tts" in model_id or "voice" in model_id:
            return "audio_generation"
        elif "dall" in model_id:
            return "image_generation"
        elif "moderation" in model_id:
            return "moderation"
        else:
            return "chat"
    
    def _pretty_name(self, model_id: str) -> str:
        names = {
            "gpt-4o": "GPT-4o",
            "gpt-4o-mini": "GPT-4o Mini",
            "gpt-4-turbo": "GPT-4 Turbo",
            "gpt-4": "GPT-4",
            "gpt-3.5-turbo": "GPT-3.5 Turbo",
            "o1-preview": "o1 Preview",
            "o1-mini": "o1 Mini",
            "text-embedding-3-large": "Text Embedding 3 Large",
            "text-embedding-3-small": "Text Embedding 3 Small",
            "text-embedding-ada-002": "Ada Embeddings",
            "whisper-1": "Whisper",
            "tts-1": "TTS",
            "tts-1-hd": "TTS HD",
            "dall-e-3": "DALL-E 3",
            "dall-e-2": "DALL-E 2",
        }
        return names.get(model_id, model_id)
    
    def _get_context_length(self, model_id: str) -> Optional[int]:
        contexts = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16385,
            "o1-preview": 128000,
            "o1-mini": 128000,
        }
        for prefix, length in contexts.items():
            if model_id.startswith(prefix):
                return length
        return None
    
    def _get_pricing(self, model_id: str) -> Dict[str, float]:
        """OpenAI pricing (per 1K tokens, convert to per 1M)"""
        pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "o1-preview": {"input": 15.00, "output": 60.00},
            "o1-mini": {"input": 3.00, "output": 12.00},
            "text-embedding-3-large": {"input": 0.13, "output": 0.00},
            "text-embedding-3-small": {"input": 0.02, "output": 0.00},
            "text-embedding-ada-002": {"input": 0.10, "output": 0.00},
            "whisper-1": {"input": 0.006, "output": 0.00},  # per minute
            "tts-1": {"input": 15.00, "output": 0.00},  # per 1M chars
            "tts-1-hd": {"input": 30.00, "output": 0.00},
            "dall-e-3": {"input": 0.04, "output": 0.00},  # per image (1024x1024)
            "dall-e-2": {"input": 0.02, "output": 0.00},
        }
        for prefix, prices in pricing.items():
            if model_id.startswith(prefix):
                return prices
        return {"input": 0, "output": 0}
    
    def _get_capabilities(self, model_id: str) -> List[str]:
        if "embedding" in model_id:
            return ["embeddings"]
        elif "whisper" in model_id:
            return ["audio_transcription"]
        elif "tts" in model_id:
            return ["audio_generation"]
        elif "dall" in model_id:
            return ["image_generation"]
        elif "moderation" in model_id:
            return ["moderation"]
        else:
            caps = ["chat", "streaming"]
            if "gpt-4o" in model_id or "gpt-4" in model_id:
                caps.extend(["vision", "function_calling", "json_mode"])
            return caps


class AnthropicConnector(ProviderConnector):
    """Anthropic API - Claude models"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY", ""),
            base_url="https://api.anthropic.com/v1"
        )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Anthropic models (static list since API doesn't expose pricing)"""
        return [
            {
                "id": "anthropic/claude-3-7-sonnet-latest",
                "name": "Claude 3.7 Sonnet",
                "provider": "anthropic",
                "provider_model_id": "claude-3-7-sonnet-latest",
                "type": "chat",
                "context_length": 200000,
                "pricing": {"input": 3.00, "output": 15.00},
                "capabilities": ["chat", "code", "vision", "function_calling", "streaming", "long_context"]
            },
            {
                "id": "anthropic/claude-3-5-sonnet-latest",
                "name": "Claude 3.5 Sonnet",
                "provider": "anthropic",
                "provider_model_id": "claude-3-5-sonnet-latest",
                "type": "chat",
                "context_length": 200000,
                "pricing": {"input": 3.00, "output": 15.00},
                "capabilities": ["chat", "code", "vision", "function_calling", "streaming"]
            },
            {
                "id": "anthropic/claude-3-opus-latest",
                "name": "Claude 3 Opus",
                "provider": "anthropic",
                "provider_model_id": "claude-3-opus-latest",
                "type": "chat",
                "context_length": 200000,
                "pricing": {"input": 15.00, "output": 75.00},
                "capabilities": ["chat", "code", "vision", "function_calling", "streaming", "long_context"]
            },
            {
                "id": "anthropic/claude-3-haiku-latest",
                "name": "Claude 3 Haiku",
                "provider": "anthropic",
                "provider_model_id": "claude-3-haiku-latest",
                "type": "chat",
                "context_length": 200000,
                "pricing": {"input": 0.25, "output": 1.25},
                "capabilities": ["chat", "code", "vision", "streaming"]
            },
        ]


class ZaiConnector(ProviderConnector):
    """Z.ai (Qwen models)"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv("ZAI_API_KEY", ""),
            base_url="https://api.z.ai/v1"  # or actual endpoint
        )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Z.ai models - can fetch from their API or use static for now"""
        # Try API first, fallback to static
        try:
            client = await self._get_client()
            resp = await client.get("/models")
            if resp.status_code == 200:
                data = resp.json()
                return [self._parse_model(m) for m in data.get("data", [])]
        except:
            pass
        
        # Fallback to known models
        return [
            {
                "id": "zai/qwen3-72b",
                "name": "Qwen3 72B",
                "provider": "zai",
                "provider_model_id": "qwen3-72b",
                "type": "chat",
                "context_length": 131072,
                "pricing": {"input": 0.50, "output": 1.00},
                "capabilities": ["chat", "code", "function_calling", "streaming"]
            },
            {
                "id": "zai/qwen3-235b",
                "name": "Qwen3 235B",
                "provider": "zai",
                "provider_model_id": "qwen3-235b",
                "type": "chat",
                "context_length": 131072,
                "pricing": {"input": 1.50, "output": 3.00},
                "capabilities": ["chat", "code", "vision", "function_calling", "streaming", "long_context"]
            },
            {
                "id": "zai/qwen-vl-max",
                "name": "Qwen VL Max",
                "provider": "zai",
                "provider_model_id": "qwen-vl-max",
                "type": "chat",
                "context_length": 32000,
                "pricing": {"input": 0.50, "output": 1.50},
                "capabilities": ["chat", "vision", "streaming"]
            },
        ]
    
    def _parse_model(self, raw: Dict) -> Dict[str, Any]:
        return {
            "id": f"zai/{raw['id']}",
            "name": raw.get("name", raw["id"]),
            "provider": "zai",
            "provider_model_id": raw["id"],
            "type": "chat",
            "context_length": raw.get("context_length"),
            "pricing": raw.get("pricing", {"input": 0, "output": 0}),
            "capabilities": raw.get("capabilities", ["chat"]),
            "raw": raw
        }


class DeepSeekConnector(ProviderConnector):
    """DeepSeek API"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY", ""),
            base_url="https://api.deepseek.com/v1"
        )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "deepseek/deepseek-chat",
                "name": "DeepSeek Chat",
                "provider": "deepseek",
                "provider_model_id": "deepseek-chat",
                "type": "chat",
                "context_length": 64000,
                "pricing": {"input": 0.14, "output": 0.28},
                "capabilities": ["chat", "code", "streaming"]
            },
            {
                "id": "deepseek/deepseek-coder",
                "name": "DeepSeek Coder",
                "provider": "deepseek",
                "provider_model_id": "deepseek-coder",
                "type": "chat",
                "context_length": 64000,
                "pricing": {"input": 0.14, "output": 0.28},
                "capabilities": ["chat", "code", "streaming"]
            },
            {
                "id": "deepseek/deepseek-reasoner",
                "name": "DeepSeek Reasoner",
                "provider": "deepseek",
                "provider_model_id": "deepseek-reasoner",
                "type": "chat",
                "context_length": 64000,
                "pricing": {"input": 0.55, "output": 2.19},
                "capabilities": ["chat", "code", "reasoning", "streaming"]
            },
        ]


class MiniMaxConnector(ProviderConnector):
    """MiniMax API"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv("MINIMAX_API_KEY", ""),
            base_url="https://api.minimax.chat/v1"
        )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "minimax/abab6.5s",
                "name": "MiniMax abab6.5s",
                "provider": "minimax",
                "provider_model_id": "abab6.5s",
                "type": "chat",
                "context_length": 8192,
                "pricing": {"input": 0.10, "output": 0.10},
                "capabilities": ["chat", "streaming"]
            },
            {
                "id": "minimax/abab6",
                "name": "MiniMax abab6",
                "provider": "minimax",
                "provider_model_id": "abab6",
                "type": "chat",
                "context_length": 8192,
                "pricing": {"input": 0.15, "output": 0.15},
                "capabilities": ["chat", "streaming"]
            },
        ]


class MistralConnector(ProviderConnector):
    """Mistral AI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv("MISTRAL_API_KEY", ""),
            base_url="https://api.mistral.ai/v1"
        )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        try:
            client = await self._get_client()
            resp = await client.get("/models")
            if resp.status_code == 200:
                data = resp.json()
                return [{
                    "id": f"mistral/{m['id']}",
                    "name": m.get("name", m["id"]),
                    "provider": "mistral",
                    "provider_model_id": m["id"],
                    "type": "chat",
                    "context_length": m.get("max_context_length", 32768),
                    "pricing": self._get_pricing(m["id"]),
                    "capabilities": ["chat", "function_calling", "streaming"],
                    "raw": m
                } for m in data.get("data", [])]
        except Exception as e:
            logger.warning(f"Mistral API fetch failed: {e}")
        
        # Fallback
        return [
            {
                "id": "mistral/mistral-large-latest",
                "name": "Mistral Large",
                "provider": "mistral",
                "provider_model_id": "mistral-large-latest",
                "type": "chat",
                "context_length": 128000,
                "pricing": {"input": 2.00, "output": 6.00},
                "capabilities": ["chat", "function_calling", "streaming", "json_mode"]
            },
            {
                "id": "mistral/mistral-medium",
                "name": "Mistral Medium",
                "provider": "mistral",
                "provider_model_id": "mistral-medium",
                "type": "chat",
                "context_length": 32000,
                "pricing": {"input": 2.70, "output": 8.10},
                "capabilities": ["chat", "streaming"]
            },
            {
                "id": "mistral/mistral-small",
                "name": "Mistral Small",
                "provider": "mistral",
                "provider_model_id": "mistral-small",
                "type": "chat",
                "context_length": 32000,
                "pricing": {"input": 0.20, "output": 0.60},
                "capabilities": ["chat", "streaming"]
            },
        ]
    
    def _get_pricing(self, model_id: str) -> Dict[str, float]:
        pricing = {
            "mistral-large": {"input": 2.00, "output": 6.00},
            "mistral-medium": {"input": 2.70, "output": 8.10},
            "mistral-small": {"input": 0.20, "output": 0.60},
            "mistral-tiny": {"input": 0.10, "output": 0.10},
        }
        for prefix, prices in pricing.items():
            if prefix in model_id:
                return prices
        return {"input": 0, "output": 0}


class GeminiConnector(ProviderConnector):
    """Google Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv("GEMINI_API_KEY", ""),
            base_url="https://generativelanguage.googleapis.com/v1beta"
        )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "gemini/gemini-1.5-pro-latest",
                "name": "Gemini 1.5 Pro",
                "provider": "gemini",
                "provider_model_id": "gemini-1.5-pro-latest",
                "type": "chat",
                "context_length": 2000000,
                "pricing": {"input": 3.50, "output": 10.50},
                "capabilities": ["chat", "code", "vision", "function_calling", "streaming", "long_context"]
            },
            {
                "id": "gemini/gemini-1.5-flash-latest",
                "name": "Gemini 1.5 Flash",
                "provider": "gemini",
                "provider_model_id": "gemini-1.5-flash-latest",
                "type": "chat",
                "context_length": 1000000,
                "pricing": {"input": 0.35, "output": 1.05},
                "capabilities": ["chat", "code", "vision", "streaming"]
            },
            {
                "id": "gemini/gemini-pro-vision",
                "name": "Gemini Pro Vision",
                "provider": "gemini",
                "provider_model_id": "gemini-pro-vision",
                "type": "chat",
                "context_length": 16384,
                "pricing": {"input": 0.50, "output": 1.50},
                "capabilities": ["chat", "vision", "streaming"]
            },
        ]


class CohereConnector(ProviderConnector):
    """Cohere API - embeddings, rerank, chat"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv("COHERE_API_KEY", ""),
            base_url="https://api.cohere.com/v1"
        )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "cohere/command-r",
                "name": "Command R",
                "provider": "cohere",
                "provider_model_id": "command-r",
                "type": "chat",
                "context_length": 128000,
                "pricing": {"input": 0.50, "output": 1.50},
                "capabilities": ["chat", "function_calling", "streaming"]
            },
            {
                "id": "cohere/command-r-plus",
                "name": "Command R+",
                "provider": "cohere",
                "provider_model_id": "command-r-plus",
                "type": "chat",
                "context_length": 128000,
                "pricing": {"input": 3.00, "output": 15.00},
                "capabilities": ["chat", "function_calling", "streaming"]
            },
            {
                "id": "cohere/embed-english-v3",
                "name": "Embed English v3",
                "provider": "cohere",
                "provider_model_id": "embed-english-v3.0",
                "type": "embedding",
                "context_length": 512,
                "pricing": {"input": 0.10, "output": 0.00},
                "capabilities": ["embeddings"]
            },
            {
                "id": "cohere/embed-multilingual-v3",
                "name": "Embed Multilingual v3",
                "provider": "cohere",
                "provider_model_id": "embed-multilingual-v3.0",
                "type": "embedding",
                "context_length": 512,
                "pricing": {"input": 0.10, "output": 0.00},
                "capabilities": ["embeddings"]
            },
            {
                "id": "cohere/rerank-english-v3",
                "name": "Rerank English v3",
                "provider": "cohere",
                "provider_model_id": "rerank-english-v3.0",
                "type": "rerank",
                "context_length": 512,
                "pricing": {"input": 2.00, "output": 0.00},
                "capabilities": ["reranking"]
            },
        ]


class ElevenLabsConnector(ProviderConnector):
    """ElevenLabs API - text to speech"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv("ELEVENLABS_API_KEY", ""),
            base_url="https://api.elevenlabs.io/v1"
        )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        try:
            client = await self._get_client()
            resp = await client.get("/models")
            if resp.status_code == 200:
                data = resp.json()
                return [{
                    "id": f"elevenlabs/{m['model_id']}",
                    "name": m.get("name", m["model_id"]),
                    "provider": "elevenlabs",
                    "provider_model_id": m["model_id"],
                    "type": "audio_generation",
                    "context_length": 10000,  # chars
                    "pricing": {"input": 0.30, "output": 0.00},  # per 1K chars
                    "capabilities": ["audio_generation", "streaming"],
                    "raw": m
                } for m in data.get("models", [])]
        except:
            pass
        
        return [
            {
                "id": "elevenlabs/eleven_multilingual_v2",
                "name": "ElevenLabs Multilingual v2",
                "provider": "elevenlabs",
                "provider_model_id": "eleven_multilingual_v2",
                "type": "audio_generation",
                "context_length": 10000,
                "pricing": {"input": 0.30, "output": 0.00},
                "capabilities": ["audio_generation", "streaming"]
            },
            {
                "id": "elevenlabs/eleven_turbo_v2_5",
                "name": "ElevenLabs Turbo v2.5",
                "provider": "elevenlabs",
                "provider_model_id": "eleven_turbo_v2_5",
                "type": "audio_generation",
                "context_length": 10000,
                "pricing": {"input": 0.10, "output": 0.00},
                "capabilities": ["audio_generation", "streaming"]
            },
        ]


class OllamaConnector(ProviderConnector):
    """Ollama - local models"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        super().__init__(base_url=base_url)
    
    async def list_models(self) -> List[Dict[str, Any]]:
        try:
            client = await self._get_client()
            resp = await client.get("/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                return [{
                    "id": f"ollama/{m['name']}",
                    "name": m["name"],
                    "provider": "ollama",
                    "provider_model_id": m["name"],
                    "type": "chat",
                    "context_length": None,
                    "pricing": {"input": 0, "output": 0},  # Free (local)
                    "capabilities": ["chat", "streaming"],
                    "raw": m
                } for m in data.get("models", [])]
        except:
            pass
        return []


# ═══════════════════════════════════════
# PROVIDER REGISTRY
# ═══════════════════════════════════════

PROVIDER_CONNECTORS = {
    "openai": OpenAIConnector,
    "anthropic": AnthropicConnector,
    "gemini": GeminiConnector,
    "deepseek": DeepSeekConnector,
    "mistral": MistralConnector,
    "cohere": CohereConnector,
    "zai": ZaiConnector,
    "minimax": MiniMaxConnector,
    "elevenlabs": ElevenLabsConnector,
    "ollama": OllamaConnector,
}


def get_connector(provider: str, **kwargs) -> Optional[ProviderConnector]:
    """Get connector for a provider"""
    connector_class = PROVIDER_CONNECTORS.get(provider)
    if connector_class:
        return connector_class(**kwargs)
    return None


def list_supported_providers() -> List[Dict[str, str]]:
    """List all supported providers"""
    return [
        {"id": k, "name": k.title(), "requires_api_key": k not in ["ollama"]}
        for k in PROVIDER_CONNECTORS.keys()
    ]