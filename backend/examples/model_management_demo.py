"""Example: LLM Model Management in FleetOps

Shows how FleetOps handles model switching for different agents:
1. Cline user switching from Claude to GPT-4o
2. CrewAI agent using fallback models
3. Cursor user with multiple agents
4. LangGraph workflow with model routing
"""

import asyncio
from app.core.model_registry import model_registry, ModelCapability, ModelTier
from app.core.agent_model_manager import AgentModelManager, RoutingStrategy
from app.core.ide_model_router import IDEModelRouter, IDEType


async def example_1_cline_user_switches_models():
    """Cline user switches between Claude and GPT-4o"""
    
    print("=" * 60)
    print("Example 1: Cline User Switching Models")
    print("=" * 60)
    
    manager = AgentModelManager()
    
    # User "juanes" configures Cline agent
    config = manager.configure_agent(
        agent_id="juanes-cline-001",
        user_id="juanes",
        primary_model="claude-3-5-sonnet",
        fallback_models=["gpt-4o", "gemini-1.5-pro"],
        strategy=RoutingStrategy.FIXED,
        allowed_providers=["anthropic", "openai", "gemini"],
        max_cost_per_day=10.0,
        required_capabilities=[ModelCapability.CODE, ModelCapability.STREAMING]
    )
    
    print(f"Configured agent: {config.agent_id}")
    print(f"Primary model: {config.primary_model}")
    print(f"Fallbacks: {config.fallback_models}")
    
    # User decides to switch to GPT-4o in Cline settings
    print("\n--- User switches to GPT-4o ---")
    success = manager.set_model("juanes-cline-001", "gpt-4o")
    print(f"Switch successful: {success}")
    
    config = manager.get_config("juanes-cline-001")
    print(f"New primary model: {config.primary_model}")
    
    # Get IDE-specific config
    router = IDEModelRouter(manager)
    cline_config = router.get_ide_config(IDEType.CLINE, "gpt-4o")
    print(f"\nCline config: {cline_config}")
    
    # Get available models for Cline
    available = router.get_available_models(IDEType.CLINE)
    print(f"\nAvailable models for Cline:")
    for m in available:
        print(f"  - {m['name']} (${m['cost_per_1m']['input']}/1M input)")


async def example_2_crewai_agent_with_fallback():
    """CrewAI agent automatically falls back when Claude is down"""
    
    print("\n" + "=" * 60)
    print("Example 2: CrewAI Agent with Fallback")
    print("=" * 60)
    
    manager = AgentModelManager()
    
    # Configure CrewAI agent
    config = manager.configure_agent(
        agent_id="crewai-researcher-001",
        user_id="research-team",
        primary_model="claude-3-opus",
        fallback_models=["gpt-4o", "gemini-1.5-pro", "claude-3-5-sonnet"],
        strategy=RoutingStrategy.FALLBACK,
        auto_fallback=True,
        cost_optimization=True
    )
    
    print(f"Configured CrewAI agent: {config.agent_id}")
    print(f"Strategy: {config.strategy.value}")
    print(f"Fallback chain: {config.fallback_models}")
    
    # Simulate Claude API being down
    print("\n--- Simulating Claude API outage ---")
    manager.registry.update_availability("claude-3-opus", False, "API timeout")
    
    # Try to chat - should auto-fallback
    messages = [{"role": "user", "content": "Research quantum computing advances"}]
    
    result = await manager.chat(
        agent_id="crewai-researcher-001",
        messages=messages
    )
    
    if result.get("status") == "success":
        routing = result.get("routing", {})
        print(f"\nRequest succeeded with fallback!")
        print(f"Model used: {routing.get('model_used')}")
        print(f"Provider: {routing.get('provider')}")
        print(f"Strategy: {routing.get('strategy')}")
    
    # Restore Claude
    manager.registry.update_availability("claude-3-opus", True)


async def example_3_cursor_multiple_agents():
    """Cursor IDE with multiple agents using different models"""
    
    print("\n" + "=" * 60)
    print("Example 3: Cursor IDE Multiple Agents")
    print("=" * 60)
    
    manager = AgentModelManager()
    
    # Agent 1: Fast code completion (cheap model)
    manager.configure_agent(
        agent_id="juanes-cursor-completion",
        user_id="juanes",
        primary_model="gpt-4o-mini",
        strategy=RoutingStrategy.CHEAPEST,
        cost_optimization=True
    )
    
    # Agent 2: Complex refactoring (premium model)
    manager.configure_agent(
        agent_id="juanes-cursor-refactor",
        user_id="juanes",
        primary_model="claude-3-5-sonnet",
        fallback_models=["gpt-4o"],
        strategy=RoutingStrategy.FIXED
    )
    
    # Agent 3: Architecture discussion (reasoning model)
    manager.configure_agent(
        agent_id="juanes-cursor-architecture",
        user_id="juanes",
        primary_model="o1-preview",
        strategy=RoutingStrategy.FIXED,
        required_capabilities=[ModelCapability.REASONING]
    )
    
    print("Configured 3 Cursor agents:")
    for agent_id in ["juanes-cursor-completion", "juanes-cursor-refactor", "juanes-cursor-architecture"]:
        config = manager.get_config(agent_id)
        print(f"  {agent_id}: {config.primary_model}")
    
    # Get IDE setup
    router = IDEModelRouter(manager)
    setup = router.get_user_ide_setup("juanes", IDEType.CURSOR)
    
    print(f"\nCursor setup for juanes:")
    print(f"  Available models: {len(setup['available_models'])}")
    print(f"  Configured agents: {len(setup['configured_agents'])}")


async def example_4_langgraph_workflow():
    """LangGraph workflow with smart model routing"""
    
    print("\n" + "=" * 60)
    print("Example 4: LangGraph Workflow with Smart Routing")
    print("=" * 60)
    
    manager = AgentModelManager()
    
    # Configure LangGraph workflow agent
    config = manager.configure_agent(
        agent_id="langgraph-data-pipeline",
        user_id="data-team",
        primary_model="gpt-4o",
        fallback_models=["claude-3-5-sonnet", "gemini-1.5-pro"],
        strategy=RoutingStrategy.SMART,
        auto_fallback=True,
        max_cost_per_request=0.50,
        required_capabilities=[
            ModelCapability.CODE,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.JSON_MODE
        ]
    )
    
    print(f"Configured LangGraph agent: {config.agent_id}")
    print(f"Strategy: {config.strategy.value}")
    
    # Simulate workflow steps
    steps = [
        {"name": "data_extraction", "tokens": 500},
        {"name": "data_transform", "tokens": 2000},
        {"name": "data_load", "tokens": 1000},
    ]
    
    for step in steps:
        print(f"\n  Step: {step['name']} (~{step['tokens']} tokens)")
        
        # Get cheapest model for this step
        cheapest = manager.registry.get_cheapest(
            capabilities=config.required_capabilities
        )
        print(f"  Cheapest model: {cheapest.id if cheapest else 'N/A'}")
        
        # Simulate cost check
        if cheapest:
            cost = cheapest.estimate_cost(step['tokens'], step['tokens'] // 2)
            print(f"  Estimated cost: ${cost:.4f}")


async def example_5_cost_optimization():
    """Automatic cost optimization across agents"""
    
    print("\n" + "=" * 60)
    print("Example 5: Cost Optimization")
    print("=" * 60)
    
    manager = AgentModelManager()
    
    # Configure multiple agents with cost optimization
    agents = [
        ("agent-001", "claude-3-5-sonnet"),
        ("agent-002", "gpt-4o"),
        ("agent-003", "claude-3-opus"),
    ]
    
    for agent_id, model in agents:
        manager.configure_agent(
            agent_id=agent_id,
            user_id="shared-team",
            primary_model=model,
            strategy=RoutingStrategy.CHEAPEST if "opus" not in model else RoutingStrategy.FIXED,
            cost_optimization=True
        )
    
    # Show cost comparison
    print("Cost comparison for 1K input / 500 output tokens:")
    
    for model_id in ["claude-3-5-sonnet", "gpt-4o", "claude-3-opus", "gpt-4o-mini"]:
        model = model_registry.get(model_id)
        if model:
            cost = model.estimate_cost(1000, 500)
            print(f"  {model.name}: ${cost:.4f}")
    
    # Show all agent costs today
    print("\nAgent usage today:")
    for agent_id, _ in agents:
        config = manager.get_config(agent_id)
        print(f"  {agent_id}: ${config.today_cost:.4f}")


async def main():
    """Run all examples"""
    
    print("\n" + "=" * 70)
    print("FLEETOPS LLM MODEL MANAGEMENT EXAMPLES")
    print("=" * 70)
    
    # Example 1: Cline user switches models
    await example_1_cline_user_switches_models()
    
    # Example 2: CrewAI with fallback
    await example_2_crewai_agent_with_fallback()
    
    # Example 3: Cursor multiple agents
    await example_3_cursor_multiple_agents()
    
    # Example 4: LangGraph workflow
    await example_4_langgraph_workflow()
    
    # Example 5: Cost optimization
    await example_5_cost_optimization()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
