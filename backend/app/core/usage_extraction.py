"""Real Usage Extraction from Provider APIs

Shows exactly what data each provider returns.
"""

import httpx
import os
from typing import Dict, Any, Optional

class RealUsageExtractor:
    """Extracts real usage data from various provider APIs"""

    @staticmethod
    def _estimate_tokens(text: Optional[str]) -> int:
        """Estimate token count from text."""
        if not text:
            return 0
        # Rough estimate: ~4 chars per token for English
        return len(text) // 4

    @staticmethod
    def extract_openai_usage(response_json: Dict) -> Dict:
        """
        OpenAI returns in response body:
        {
            "usage": {
                "prompt_tokens": 1234,
                "completion_tokens": 567,
                "total_tokens": 1801,
                "prompt_tokens_details": {
                    "cached_tokens": 1000,
                    "audio_tokens": 0
                },
                "completion_tokens_details": {
                    "reasoning_tokens": 200,
                    "audio_tokens": 0
                }
            }
        }
        """
        usage = response_json.get("usage", {})
        has_real = "usage" in response_json
        content = ""
        if response_json.get("choices"):
            content = response_json["choices"][0].get("message", {}).get("content", "")

        return {
            "input_tokens": usage.get("prompt_tokens", 0) if has_real else 0,
            "output_tokens": usage.get("completion_tokens", 0) if has_real else RealUsageExtractor._estimate_tokens(content),
            "total_tokens": usage.get("total_tokens", 0) if has_real else RealUsageExtractor._estimate_tokens(content),
            "cached_tokens": usage.get("prompt_tokens_details", {}).get("cached_tokens", 0),
            "model": response_json.get("model", "unknown"),
            "has_real_usage": has_real
        }

    @staticmethod
    def extract_anthropic_usage(response_json: Dict) -> Dict:
        """
        Anthropic returns in response body:
        {
            "usage": {
                "input_tokens": 1234,
                "output_tokens": 567
            }
        }

        Anthropic does NOT return total_tokens, we calculate it.
        Anthropic does NOT return cached tokens (they don't cache).
        """
        usage = response_json.get("usage", {})
        has_real = "usage" in response_json
        input_tok = usage.get("input_tokens", 0)
        output_tok = usage.get("output_tokens", 0)

        return {
            "input_tokens": input_tok,
            "output_tokens": output_tok,
            "total_tokens": input_tok + output_tok,
            "cached_tokens": 0,
            "model": response_json.get("model", "unknown"),
            "has_real_usage": has_real
        }

    @staticmethod
    def extract_groq_usage(response_json: Dict) -> Dict:
        """
        Groq returns in response body:
        {
            "usage": {
                "prompt_tokens": 1234,
                "completion_tokens": 567,
                "total_tokens": 1801
            }
        }

        Groq also returns in headers (sometimes):
        X-Request-Id: req_123
        """
        usage = response_json.get("usage", {})
        return {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "cached_tokens": 0,
            "model": response_json.get("model", "unknown"),
            "has_real_usage": True
        }

    @staticmethod
    def extract_perplexity_usage(response_json: Dict) -> Dict:
        """
        Perplexity returns in response body:
        {
            "usage": {
                "prompt_tokens": 1234,
                "completion_tokens": 567,
                "total_tokens": 1801
            }
        }

        Perplexity also returns citations count (unique to them).
        """
        usage = response_json.get("usage", {})
        return {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "cached_tokens": 0,
            "citations": len(response_json.get("citations", [])),
            "model": response_json.get("model", "unknown"),
            "has_real_usage": True
        }

    @staticmethod
    def extract_openrouter_usage(response_json: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        OpenRouter returns in response body:
        {
            "usage": {
                "prompt_tokens": 1234,
                "completion_tokens": 567,
                "total_tokens": 1801
            },
            "model": "anthropic/claude-3.5-sonnet"
        }

        OpenRouter ALSO returns cost info in headers when available:
        X-OpenRouter-Cost: 0.00567

        OpenRouter also exposes pricing via API:
        GET https://openrouter.ai/api/v1/models
        """
        usage = response_json.get("usage", {})

        # Try to get cost from headers
        cost_from_header = None
        if headers:
            cost_header = headers.get("x-openrouter-cost") or headers.get("X-OpenRouter-Cost")
            if cost_header:
                cost_from_header = float(cost_header)

        return {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "cached_tokens": 0,
            "cost_from_provider": cost_from_header,
            "model": response_json.get("model", "unknown"),
            "has_real_usage": True,
            "has_real_cost": cost_from_header is not None
        }

    @staticmethod
    def extract_together_usage(response_json: Dict) -> Dict:
        """
        Together AI returns in response body:
        {
            "usage": {
                "prompt_tokens": 1234,
                "completion_tokens": 567,
                "total_tokens": 1801
            }
        }
        """
        usage = response_json.get("usage", {})
        return {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "cached_tokens": 0,
            "model": response_json.get("model", "unknown"),
            "has_real_usage": True
        }

    @staticmethod
    def extract_ollama_usage(response_json: Dict) -> Dict:
        """
        Ollama returns in response body:
        {
            "message": {"content": "Hello"},
            "prompt_eval_count": 100,
            "eval_count": 50,
            "model": "llama3.1:8b"
        }

        Or if no counts, we must estimate.
        """
        prompt_eval = response_json.get("prompt_eval_count", 0)
        eval_count = response_json.get("eval_count", 0)
        has_real = "prompt_eval_count" in response_json or "eval_count" in response_json

        if not has_real:
            content = response_json.get("message", {}).get("content", "")
            prompt_eval = 0
            eval_count = RealUsageExtractor._estimate_tokens(content)

        return {
            "input_tokens": prompt_eval,
            "output_tokens": eval_count,
            "total_tokens": prompt_eval + eval_count,
            "cached_tokens": 0,
            "model": response_json.get("model", "ollama"),
            "has_real_usage": has_real
        }

    @staticmethod
    def extract_azure_openai_usage(response_json: Dict) -> Dict:
        """
        Azure OpenAI returns same as OpenAI:
        {
            "usage": {
                "prompt_tokens": 1234,
                "completion_tokens": 567,
                "total_tokens": 1801
            }
        }

        Azure also returns in headers:
        x-ms-client-request-id: abc-123
        """
        usage = response_json.get("usage", {})
        return {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "cached_tokens": 0,
            "model": response_json.get("model", "unknown"),
            "has_real_usage": True
        }

    @staticmethod
    def extract_gemini_usage(response_json: Dict) -> Dict:
        """
        Google Gemini returns in response body:
        {
            "usageMetadata": {
                "promptTokenCount": 1234,
                "candidatesTokenCount": 567,
                "totalTokenCount": 1801
            }
        }

        Different field names!
        """
        usage = response_json.get("usageMetadata", {})
        return {
            "input_tokens": usage.get("promptTokenCount", 0),
            "output_tokens": usage.get("candidatesTokenCount", 0),
            "total_tokens": usage.get("totalTokenCount", 0),
            "cached_tokens": 0,
            "model": response_json.get("modelVersion", "unknown"),
            "has_real_usage": True
        }

    @classmethod
    def extract(cls, provider: str, response_data: Any,
                prompt_text: str = "", headers: Optional[Dict] = None) -> Dict:
        """Extract usage from any provider"""
        extractors = {
            "openai": cls.extract_openai_usage,
            "anthropic": cls.extract_anthropic_usage,
            "groq": cls.extract_groq_usage,
            "perplexity": cls.extract_perplexity_usage,
            "openrouter": cls.extract_openrouter_usage,
            "together": cls.extract_together_usage,
            "azure": cls.extract_azure_openai_usage,
            "gemini": cls.extract_gemini_usage,
            "ollama": cls.extract_ollama_usage,
        }

        extractor = extractors.get(provider)
        if extractor:
            if provider == "openrouter":
                return extractor(response_data, headers)
            else:
                return extractor(response_data)

        # Unknown provider - try generic extraction
        usage = response_data.get("usage", {})
        return {
            "input_tokens": usage.get("prompt_tokens", usage.get("input_tokens", 0)),
            "output_tokens": usage.get("completion_tokens", usage.get("output_tokens", 0)),
            "total_tokens": usage.get("total_tokens", 0),
            "cached_tokens": 0,
            "model": response_data.get("model", "unknown"),
            "has_real_usage": "usage" in response_data
        }


class ProviderCostAPI:
    """Fetch cost data directly from provider APIs"""

    @staticmethod
    async def fetch_openrouter_cost(model_id: str) -> Optional[Dict]:
        """
        OpenRouter exposes pricing via API:
        GET https://openrouter.ai/api/v1/models

        Returns:
        {
            "data": [{
                "id": "anthropic/claude-3.5-sonnet",
                "pricing": {
                    "prompt": 0.000003,    # per token
                    "completion": 0.000015 # per token
                }
            }]
        }
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://openrouter.ai/api/v1/models")
                response.raise_for_status()
                data = response.json()

                for model in data.get("data", []):
                    if model.get("id") == model_id:
                        pricing = model.get("pricing", {})
                        return {
                            "input_rate_per_1m": float(pricing.get("prompt", 0)) * 1_000_000,
                            "output_rate_per_1m": float(pricing.get("completion", 0)) * 1_000_000,
                            "source": "openrouter_api",
                            "model": model_id
                        }
        except Exception as e:
            print(f"Failed to fetch OpenRouter pricing: {e}")

        return None

    @staticmethod
    async def fetch_together_pricing() -> Optional[Dict]:
        """
        Together AI pricing:
        GET https://api.together.xyz/v1/models

        Returns model list with pricing.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.together.xyz/v1/models")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Failed to fetch Together pricing: {e}")
        return None

    @staticmethod
    async def fetch_groq_pricing() -> Optional[Dict]:
        """
        Groq pricing is flat rate per model:
        https://groq.com/pricing

        They don't have a pricing API, but rates are published.
        """
        # Groq rates (as of 2024) - could scrape or hardcode as fallback
        return {
            "llama3-8b": {"input_per_1m": 0.05, "output_per_1m": 0.08},
            "llama3-70b": {"input_per_1m": 0.59, "output_per_1m": 0.79},
            "mixtral-8x7b": {"input_per_1m": 0.24, "output_per_1m": 0.24},
            "source": "groq_published"
        }

    @staticmethod
    async def fetch_perplexity_pricing() -> Optional[Dict]:
        """
        Perplexity pricing:
        https://docs.perplexity.ai/guides/pricing

        Sonar: $0.0005 / 1K input, $0.0015 / 1K output
        Sonar Pro: $0.003 / 1K input, $0.015 / 1K output
        """
        return {
            "sonar": {"input_per_1m": 0.50, "output_per_1m": 1.50},
            "sonar-pro": {"input_per_1m": 3.00, "output_per_1m": 15.00},
            "source": "perplexity_docs"
        }

    @staticmethod
    async def fetch_openai_pricing() -> Optional[Dict]:
        """
        OpenAI pricing page: https://openai.com/api/pricing/

        No API for pricing, must scrape or use known rates.
        Could use web scraping or manual updates.
        """
        # Return known rates (OpenAI updates these occasionally)
        return {
            "gpt-4o": {"input_per_1m": 5.00, "output_per_1m": 15.00},
            "gpt-4o-mini": {"input_per_1m": 0.15, "output_per_1m": 0.60},
            "gpt-4-turbo": {"input_per_1m": 10.00, "output_per_1m": 30.00},
            "gpt-3.5-turbo": {"input_per_1m": 0.50, "output_per_1m": 1.50},
            "source": "openai_published"
        }

    @staticmethod
    async def fetch_anthropic_pricing() -> Optional[Dict]:
        """
        Anthropic pricing: https://www.anthropic.com/pricing

        Claude 3 Opus: $15 / 1M input, $75 / 1M output
        Claude 3.5 Sonnet: $3 / 1M input, $15 / 1M output
        Claude 3 Haiku: $0.25 / 1M input, $1.25 / 1M output
        """
        return {
            "claude-3-opus": {"input_per_1m": 15.00, "output_per_1m": 75.00},
            "claude-3-sonnet": {"input_per_1m": 3.00, "output_per_1m": 15.00},
            "claude-3-haiku": {"input_per_1m": 0.25, "output_per_1m": 1.25},
            "claude-3-5-sonnet": {"input_per_1m": 3.00, "output_per_1m": 15.00},
            "source": "anthropic_published"
        }


# ═══════════════════════════════════════
# REAL USAGE IN ACTION
# ═══════════════════════════════════════

async def track_real_openai_request():
    """Example: Make request and track real usage"""
    import openai

    client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}]
    )

    # Extract REAL usage from response
    usage = RealUsageExtractor.extract_openai_usage(response.model_dump())

    print(f"Real usage:")
    print(f"  Input tokens: {usage['input_tokens']}")
    print(f"  Output tokens: {usage['output_tokens']}")
    print(f"  Total tokens: {usage['total_tokens']}")
    print(f"  Cached: {usage['cached_tokens']}")

    # Calculate cost with real pricing
    from app.core.cost_tracking import cost_tracker
    result = await cost_tracker.track_usage(
        service="openai",
        model="gpt-4o",
        agent_id="test_agent",
        task_id="task_123",
        input_tokens=usage['input_tokens'],
        output_tokens=usage['output_tokens'],
        cached_tokens=usage['cached_tokens']
    )

    print(f"Cost: ${result['cost_usd']}")
    return result


async def track_real_openrouter_request():
    """Example: OpenRouter returns cost in headers"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
            json={
                "model": "anthropic/claude-3.5-sonnet",
                "messages": [{"role": "user", "content": "Hello!"}]
            }
        )

        data = response.json()
        headers = dict(response.headers)

        # Extract usage AND cost from response
        usage = RealUsageExtractor.extract_openrouter_usage(data, headers)

        print(f"Real usage: {usage['input_tokens']} in, {usage['output_tokens']} out")

        if usage.get("has_real_cost"):
            print(f"Cost from provider: ${usage['cost_from_provider']}")
        else:
            # Calculate from our pricing
            from app.core.cost_tracking import cost_tracker
            result = await cost_tracker.track_usage(
                service="openrouter",
                model="anthropic/claude-3.5-sonnet",
                agent_id="test_agent",
                task_id="task_456",
                input_tokens=usage['input_tokens'],
                output_tokens=usage['output_tokens']
            )
            print(f"Calculated cost: ${result['cost_usd']}")
