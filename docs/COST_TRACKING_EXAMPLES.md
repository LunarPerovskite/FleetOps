"""Example: How adapters use dynamic cost tracking

This shows how each adapter integrates with the new DynamicCostTracker
to record REAL usage data from APIs.
"""

from app.core.cost_tracking import cost_tracker


async def example_perplexity_usage():
    """Perplexity returns real usage in API response"""
    # ... make API call ...
    response = {
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 200,
            "total_tokens": 350
        }
    }
    
    # Track with actual usage
    result = await cost_tracker.track_usage(
        service="perplexity",
        model="sonar",
        agent_id="my_agent_01",
        task_id="task_123",
        input_tokens=response["usage"]["prompt_tokens"],
        output_tokens=response["usage"]["completion_tokens"],
        metadata={"source": "perplexity_api", "has_citations": True}
    )
    
    print(f"Cost: ${result['cost_usd']}")
    print(f"Pricing source: {result['pricing_source']}")
    # Pricing automatically fetched from OpenRouter or user config


async def example_openai_usage():
    """OpenAI returns usage in response"""
    # ... make API call ...
    response = {
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500
        }
    }
    
    result = await cost_tracker.track_usage(
        service="openai",
        model="gpt-4o",  # Will auto-discover pricing
        agent_id="claude_code_01",
        task_id="task_456",
        input_tokens=response["usage"]["prompt_tokens"],
        output_tokens=response["usage"]["completion_tokens"]
    )
    
    print(f"Cost: ${result['cost_usd']}")


async def example_ollama_usage():
    """Ollama doesn't return token counts, we estimate"""
    # Ollama doesn't return usage, so we estimate from response
    response_text = "...generated text..."
    
    # Rough estimate: 1 token ≈ 4 chars for English
    estimated_output_tokens = len(response_text) // 4
    
    result = await cost_tracker.track_usage(
        service="ollama",
        model="llama3.1:8b",
        agent_id="local_agent_01",
        task_id="task_789",
        input_tokens=100,  # From prompt
        output_tokens=estimated_output_tokens,
        metadata={"estimated": True, "source": "ollama_local"}
    )
    
    print(f"Estimated cost: ${result['cost_usd']}")
    # Will use local compute pricing (electricity) or user-configured rate


async def example_user_configured_model():
    """User adds pricing for a new model"""
    # User configures via API:
    # POST /pricing/configure
    # {
    #   "service": "custom_provider",
    #   "model": "new-model-v2",
    #   "input_rate_per_1m": 0.50,
    #   "output_rate_per_1m": 1.50,
    #   "notes": "My negotiated rate"
    # }
    
    # Now tracking uses this rate automatically
    result = await cost_tracker.track_usage(
        service="custom_provider",
        model="new-model-v2",
        agent_id="agent_01",
        task_id="task_abc",
        input_tokens=10000,
        output_tokens=5000
    )
    
    print(f"Cost with user rate: ${result['cost_usd']}")
    print(f"Rate source: {result['pricing_source']}")  # "user_configured"


async def example_openrouter_inside_agent():
    """Agent uses OpenRouter which uses Anthropic"""
    # OpenRouter returns usage
    response = {
        "usage": {
            "prompt_tokens": 2000,
            "completion_tokens": 1000
        },
        "model": "anthropic/claude-3.5-sonnet"
    }
    
    # Track the actual call (OpenRouter rate)
    result = await cost_tracker.track_usage(
        service="openrouter",
        model="anthropic/claude-3.5-sonnet",
        agent_id="roo_code_01",
        task_id="task_xyz",
        input_tokens=response["usage"]["prompt_tokens"],
        output_tokens=response["usage"]["completion_tokens"],
        metadata={
            "actual_provider": "anthropic",
            "nested_service": True
        }
    )
    
    print(f"OpenRouter cost: ${result['cost_usd']}")
    # Pricing fetched from OpenRouter API automatically


# ═══════════════════════════════════════
# USAGE IN ADAPTERS
# ═══════════════════════════════════════

"""
Every adapter should call track_usage() with REAL data:

class PerplexityAdapter:
    async def query(self, question, task_id):
        response = await self.client.post("/chat/completions", ...)
        data = response.json()
        
        # Get real usage
        usage = data.get("usage", {})
        
        # Track with real data
        await cost_tracker.track_usage(
            service="perplexity",
            model=data.get("model", "sonar"),
            agent_id="perplexity_adapter",
            task_id=task_id,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            metadata={"citations": len(data.get("citations", []))}
        )
        
        return data

class OpenRouterAdapter:
    async def chat(self, messages, task_id):
        response = await self.client.post("/chat/completions", ...)
        data = response.json()
        
        usage = data.get("usage", {})
        
        await cost_tracker.track_usage(
            service="openrouter",
            model=data.get("model"),
            agent_id="openrouter_adapter",
            task_id=task_id,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0)
        )
        
        return data
"""
