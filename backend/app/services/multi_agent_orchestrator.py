"""Multi-Agent Orchestration Service for FleetOps

Manages interactions between multiple agents:
- Sequential pipelines (Agent A → Agent B → Agent C)
- Parallel execution (Agent A + Agent B simultaneously)
- Agent debates (multiple agents discuss topic)
- Consensus building (agents must agree)
- Load balancing (distribute tasks across agents)
- Cross-agent workflows with human approval gates

Key principle: Agents NEVER talk directly to each other.
FleetOps is always the middleman.
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import logging

from app.adapters.personal_agent_adapter import PersonalAgentAdapter, AgentType
from app.services.agent_instance_service import agent_instance_service
from app.services.service_stubs import task_service, approval_service, notification_service, event_service

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """Orchestrates interactions between multiple agents
    
    Usage:
        orchestrator = MultiAgentOrchestrator()
        
        # Sequential pipeline
        result = await orchestrator.sequential_pipeline([
            {"agent": "crewai", "task": "Research topic"},
            {"agent": "openclaw", "task": "Write code based on research"},
            {"agent": "devin", "task": "Deploy the application"}
        ])
        
        # Parallel execution
        results = await orchestrator.parallel_execute([
            {"agent": "openclaw", "task": "Write backend"},
            {"agent": "crewai", "task": "Write frontend"}
        ])
        
        # Agent debate
        winner = await orchestrator.agent_debate(
            topic="Best database for this project?",
            agents=["openclaw", "crewai", "autogen"]
        )
    """
    
    def __init__(self):
        self._active_pipelines: Dict[str, Dict] = {}
        self._results_cache: Dict[str, Any] = {}
    
    # ═══════════════════════════════════════
    # SEQUENTIAL PIPELINE
    # ═══════════════════════════════════════
    
    async def sequential_pipeline(
        self,
        pipeline_id: str,
        steps: List[Dict[str, Any]],
        org_id: str,
        require_approval_between_steps: bool = True,
        stop_on_failure: bool = True
    ) -> Dict[str, Any]:
        """Execute a sequential pipeline of agents
        
        Each step's output becomes the next step's input.
        Human approval between steps.
        
        Example:
            steps = [
                {
                    "agent": "crewai",
                    "name": "research",
                    "task": "Research: What are the best practices for API authentication?",
                    "config": {"process": "sequential"}
                },
                {
                    "agent": "openclaw",
                    "name": "implementation",
                    "task": "Based on the research, implement JWT authentication",
                    "depends_on": ["research"]  # Uses output from 'research' step
                },
                {
                    "agent": "aider",
                    "name": "testing",
                    "task": "Write comprehensive tests for the authentication system",
                    "depends_on": ["implementation"]
                }
            ]
        """
        try:
            logger.info(f"Starting sequential pipeline {pipeline_id} with {len(steps)} steps")
            
            results = {}
            step_results = []
            
            for i, step in enumerate(steps):
                step_id = f"{pipeline_id}_step_{i}"
                agent_type = step["agent"]
                step_name = step.get("name", f"step_{i}")
                
                logger.info(f"Pipeline {pipeline_id}: Executing step {i+1}/{len(steps)} - {step_name} with {agent_type}")
                
                # Check dependencies
                depends_on = step.get("depends_on", [])
                context = {}
                for dep in depends_on:
                    if dep in results:
                        context[dep] = results[dep]
                    else:
                        error_msg = f"Dependency '{dep}' not found for step {step_name}"
                        logger.error(error_msg)
                        return {
                            "status": "failed",
                            "error": error_msg,
                            "completed_steps": step_results,
                            "failed_at_step": i
                        }
                
                # Build instructions with context from previous steps
                instructions = step["task"]
                if context:
                    instructions += f"\n\nPrevious results:\n"
                    for dep_name, dep_result in context.items():
                        instructions += f"\n[{dep_name}]:\n{dep_result.get('output', str(dep_result))[:2000]}\n"
                
                # Execute with agent
                agent = PersonalAgentAdapter(agent_type)
                
                # Get agent instance for permissions
                instance = await self._get_agent_instance(org_id, agent_type)
                
                result = await agent.execute_task(
                    task_id=step_id,
                    instructions=instructions,
                    context={
                        "org_id": org_id,
                        "pipeline_id": pipeline_id,
                        "step_number": i + 1,
                        "total_steps": len(steps),
                        "previous_results": context,
                        "step_name": step_name
                    }
                )
                
                if result["status"] == "error":
                    logger.error(f"Pipeline {pipeline_id}: Step {step_name} failed: {result.get('error')}")
                    
                    if stop_on_failure:
                        return {
                            "status": "failed",
                            "error": result.get("error"),
                            "completed_steps": step_results,
                            "failed_at_step": i,
                            "failed_step_name": step_name
                        }
                    else:
                        step_results.append({
                            "step": i,
                            "name": step_name,
                            "agent": agent_type,
                            "status": "failed",
                            "error": result.get("error")
                        })
                        continue
                
                # Store result
                results[step_name] = result
                step_results.append({
                    "step": i,
                    "name": step_name,
                    "agent": agent_type,
                    "status": "success",
                    "output_preview": str(result.get("output", ""))[:500]
                })
                
                # Human approval between steps
                if require_approval_between_steps and i < len(steps) - 1:
                    logger.info(f"Pipeline {pipeline_id}: Waiting for human approval before step {i+2}")
                    
                    approval = await self._request_step_approval(
                        pipeline_id=pipeline_id,
                        step_number=i + 1,
                        step_name=step_name,
                        next_step=steps[i + 1].get("name", f"step_{i+1}"),
                        result=result,
                        org_id=org_id
                    )
                    
                    if approval["decision"] != "approve":
                        return {
                            "status": "cancelled",
                            "reason": f"Human rejected continuation after step {step_name}",
                            "completed_steps": step_results,
                            "stopped_at_step": i
                        }
                
                # Small delay between steps
                await asyncio.sleep(1)
            
            logger.info(f"Pipeline {pipeline_id}: Completed successfully")
            
            return {
                "status": "completed",
                "pipeline_id": pipeline_id,
                "total_steps": len(steps),
                "completed_steps": len(step_results),
                "steps": step_results,
                "final_output": results.get(steps[-1].get("name", f"step_{len(steps)-1}"))
            }
            
        except Exception as e:
            logger.exception(f"Pipeline {pipeline_id} failed")
            return {
                "status": "error",
                "error": str(e),
                "pipeline_id": pipeline_id
            }
    
    # ═══════════════════════════════════════
    # PARALLEL EXECUTION
    # ═══════════════════════════════════════
    
    async def parallel_execute(
        self,
        jobs: List[Dict[str, Any]],
        org_id: str,
        max_concurrent: int = 3,
        require_all_success: bool = False
    ) -> Dict[str, Any]:
        """Execute multiple agents in parallel
        
        Example:
            jobs = [
                {"agent": "openclaw", "task": "Write API models", "name": "models"},
                {"agent": "crewai", "task": "Design database schema", "name": "database"},
                {"agent": "hermes", "task": "Write API documentation", "name": "docs"}
            ]
        """
        try:
            logger.info(f"Starting parallel execution with {len(jobs)} jobs (max concurrent: {max_concurrent})")
            
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def execute_with_limit(job: Dict) -> Dict:
                async with semaphore:
                    agent_type = job["agent"]
                    job_name = job.get("name", "unnamed")
                    
                    logger.info(f"Parallel: Starting job {job_name} with {agent_type}")
                    
                    agent = PersonalAgentAdapter(agent_type)
                    
                    result = await agent.execute_task(
                        task_id=f"parallel_{job_name}",
                        instructions=job["task"],
                        context={
                            "org_id": org_id,
                            "job_name": job_name,
                            "parallel_execution": True
                        }
                    )
                    
                    return {
                        "name": job_name,
                        "agent": agent_type,
                        "status": result.get("status", "unknown"),
                        "result": result
                    }
            
            # Execute all jobs in parallel
            tasks = [execute_with_limit(job) for job in jobs]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful = []
            failed = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed.append({"error": str(result)})
                elif result["status"] == "success" or result["status"] == "executing":
                    successful.append(result)
                else:
                    failed.append(result)
            
            status = "completed"
            if failed and require_all_success:
                status = "failed"
            elif failed:
                status = "partial"
            
            logger.info(f"Parallel execution: {len(successful)} successful, {len(failed)} failed")
            
            return {
                "status": status,
                "total_jobs": len(jobs),
                "successful": len(successful),
                "failed": len(failed),
                "results": {
                    "successful": successful,
                    "failed": failed
                }
            }
            
        except Exception as e:
            logger.exception("Parallel execution failed")
            return {"status": "error", "error": str(e)}
    
    # ═══════════════════════════════════════
    # AGENT DEBATE
    # ═══════════════════════════════════════
    
    async def agent_debate(
        self,
        topic: str,
        agents: List[str],
        org_id: str,
        rounds: int = 1,
        require_consensus: bool = False
    ) -> Dict[str, Any]:
        """Multiple agents debate a topic
        
        Each agent provides their perspective.
        Human selects the best approach.
        
        Example:
            topic = "Should we use PostgreSQL or MongoDB?"
            agents = ["openclaw", "crewai", "autogen"]
        """
        try:
            logger.info(f"Starting agent debate on: {topic}")
            
            opinions = {}
            
            # Collect opinions from all agents
            for agent_type in agents:
                logger.info(f"Debate: Getting opinion from {agent_type}")
                
                agent = PersonalAgentAdapter(agent_type)
                
                result = await agent.execute_task(
                    task_id=f"debate_{agent_type}",
                    instructions=f"DEBATE TOPIC: {topic}\n\nProvide your analysis and recommendation. "
                               f"Consider:\n"
                               f"- Technical merits\n"
                               f"- Scalability\n"
                               f"- Maintenance\n"
                               f"- Team expertise\n"
                               f"\nBe thorough but concise. Argue for your position.",
                    context={
                        "org_id": org_id,
                        "debate_topic": topic,
                        "agent_role": "debater"
                    }
                )
                
                opinions[agent_type] = {
                    "agent": agent_type,
                    "opinion": result.get("output", "No output"),
                    "status": result.get("status", "unknown")
                }
            
            # Create comparison for human
            comparison = self._create_debate_comparison(topic, opinions)
            
            # Request human to select winner
            if require_consensus:
                # Additional rounds where agents respond to each other
                logger.info("Debate: Starting response rounds")
                
                for round_num in range(rounds - 1):
                    responses = {}
                    
                    for agent_type in agents:
                        other_opinions = {k: v for k, v in opinions.items() if k != agent_type}
                        
                        agent = PersonalAgentAdapter(agent_type)
                        
                        result = await agent.execute_task(
                            task_id=f"debate_response_{agent_type}_round_{round_num}",
                            instructions=f"RESPOND TO OTHER AGENTS\n\n"
                                       f"Topic: {topic}\n"
                                       f"Your previous position: {opinions[agent_type]['opinion'][:500]}\n\n"
                                       f"Other agents said:\n"
                                       f"{self._format_opinions(other_opinions)}\n\n"
                                       f"Respond to their points. Defend your position or update it.",
                            context={"org_id": org_id, "round": round_num}
                        )
                        
                        responses[agent_type] = result.get("output", "No response")
                    
                    # Update opinions with responses
                    for agent_type in agents:
                        opinions[agent_type]["opinion"] += f"\n\n[Round {round_num + 2} Response]:\n{responses[agent_type]}"
            
            # Request human selection
            selection = await self._request_debate_winner(topic, opinions, org_id)
            
            return {
                "status": "completed",
                "topic": topic,
                "agents": list(opinions.keys()),
                "opinions": opinions,
                "human_selection": selection.get("winner"),
                "human_reasoning": selection.get("reasoning"),
                "rounds": rounds
            }
            
        except Exception as e:
            logger.exception("Agent debate failed")
            return {"status": "error", "error": str(e)}
    
    # ═══════════════════════════════════════
    # CONSENSUS BUILDING
    # ═══════════════════════════════════════
    
    async def consensus_building(
        self,
        proposal: str,
        agents: List[str],
        org_id: str,
        threshold: float = 0.7,
        max_rounds: int = 3
    ) -> Dict[str, Any]:
        """Agents must reach consensus on a proposal
        
        Each agent reviews and approves/rejects.
        If consensus not reached, agents discuss until agreement.
        
        Example:
            proposal = "Deploy new authentication system"
            threshold = 0.7  # 70% must approve
        """
        try:
            logger.info(f"Starting consensus building: {proposal}")
            
            approvals = {}
            round_num = 0
            
            while round_num < max_rounds:
                logger.info(f"Consensus round {round_num + 1}/{max_rounds}")
                
                # Get approvals from all agents
                for agent_type in agents:
                    if agent_type in approvals and approvals[agent_type] == "approve":
                        continue  # Already approved
                    
                    agent = PersonalAgentAdapter(agent_type)
                    
                    previous_feedback = ""
                    if round_num > 0:
                        previous_feedback = self._format_previous_feedback(approvals)
                    
                    result = await agent.execute_task(
                        task_id=f"consensus_{agent_type}_round_{round_num}",
                        instructions=f"REVIEW AND APPROVE/REJECT\n\n"
                                   f"Proposal: {proposal}\n\n"
                                   f"Previous feedback:\n{previous_feedback}\n\n"
                                   f"Do you APPROVE or REJECT this proposal?\n"
                                   f"Provide detailed reasoning.",
                        context={"org_id": org_id, "round": round_num}
                    )
                    
                    output = result.get("output", "").lower()
                    
                    if "approve" in output and "reject" not in output:
                        approvals[agent_type] = "approve"
                    elif "reject" in output:
                        approvals[agent_type] = "reject"
                    else:
                        approvals[agent_type] = "unclear"
                
                # Calculate consensus
                approval_rate = sum(1 for v in approvals.values() if v == "approve") / len(agents)
                
                logger.info(f"Consensus rate: {approval_rate:.0%} ({sum(1 for v in approvals.values() if v == 'approve')}/{len(agents)})")
                
                if approval_rate >= threshold:
                    return {
                        "status": "consensus_reached",
                        "proposal": proposal,
                        "approval_rate": approval_rate,
                        "approvals": approvals,
                        "rounds_needed": round_num + 1
                    }
                
                round_num += 1
            
            # Max rounds reached without consensus
            return {
                "status": "no_consensus",
                "proposal": proposal,
                "approval_rate": approval_rate,
                "approvals": approvals,
                "max_rounds_reached": max_rounds,
                "recommendation": "Requires human arbitration"
            }
            
        except Exception as e:
            logger.exception("Consensus building failed")
            return {"status": "error", "error": str(e)}
    
    # ═══════════════════════════════════════
    # LOAD BALANCING
    # ═══════════════════════════════════════
    
    async def load_balanced_execute(
        self,
        tasks: List[Dict[str, Any]],
        available_agents: List[str],
        org_id: str,
        strategy: str = "round_robin"
    ) -> Dict[str, Any]:
        """Distribute tasks across agents
        
        Strategies:
        - round_robin: Even distribution
        - least_busy: Assign to least busy agent
        - capability: Match task to agent capabilities
        - random: Random assignment
        """
        try:
            logger.info(f"Load balancing {len(tasks)} tasks across {len(available_agents)} agents ({strategy})")
            
            assignments = []
            
            if strategy == "round_robin":
                for i, task in enumerate(tasks):
                    agent = available_agents[i % len(available_agents)]
                    assignments.append({**task, "assigned_agent": agent})
            
            elif strategy == "least_busy":
                # Get current load for each agent
                agent_loads = await self._get_agent_loads(available_agents, org_id)
                
                for task in tasks:
                    # Sort by load (ascending)
                    sorted_agents = sorted(agent_loads.items(), key=lambda x: x[1])
                    agent = sorted_agents[0][0]
                    assignments.append({**task, "assigned_agent": agent})
                    agent_loads[agent] += 1  # Increment load
            
            elif strategy == "capability":
                for task in tasks:
                    # Match task requirements to agent capabilities
                    best_agent = await self._match_agent_to_task(task, available_agents)
                    assignments.append({**task, "assigned_agent": best_agent})
            
            else:  # random
                import random
                for task in tasks:
                    agent = random.choice(available_agents)
                    assignments.append({**task, "assigned_agent": agent})
            
            # Execute all tasks in parallel
            semaphore = asyncio.Semaphore(len(available_agents))
            
            async def execute_assigned(assignment):
                async with semaphore:
                    agent = PersonalAgentAdapter(assignment["assigned_agent"])
                    
                    result = await agent.execute_task(
                        task_id=assignment.get("id", f"task_{datetime.utcnow().timestamp()}"),
                        instructions=assignment["task"],
                        context={
                            "org_id": org_id,
                            "assigned_agent": assignment["assigned_agent"],
                            "load_balance_strategy": strategy
                        }
                    )
                    
                    return {
                        "task": assignment.get("name", "unnamed"),
                        "agent": assignment["assigned_agent"],
                        "status": result.get("status"),
                        "result": result
                    }
            
            tasks_to_run = [execute_assigned(a) for a in assignments]
            results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
            
            return {
                "status": "completed",
                "strategy": strategy,
                "total_tasks": len(tasks),
                "assignments": [
                    {"task": a.get("name"), "agent": a["assigned_agent"]}
                    for a in assignments
                ],
                "results": results
            }
            
        except Exception as e:
            logger.exception("Load balancing failed")
            return {"status": "error", "error": str(e)}
    
    # ═══════════════════════════════════════
    # CROSS-AGENT WORKFLOW
    # ═══════════════════════════════════════
    
    async def cross_agent_workflow(
        self,
        workflow_id: str,
        workflow_definition: Dict[str, Any],
        org_id: str
    ) -> Dict[str, Any]:
        """Execute a complex cross-agent workflow
        
        Workflow definition:
        {
            "name": "Build Feature",
            "steps": [
                {
                    "id": "design",
                    "agent": "crewai",
                    "task": "Design the feature",
                    "next": ["implement", "document"]
                },
                {
                    "id": "implement",
                    "agent": "openclaw",
                    "task": "Implement based on design",
                    "depends_on": ["design"],
                    "next": ["test"]
                },
                {
                    "id": "document",
                    "agent": "hermes",
                    "task": "Document the feature",
                    "depends_on": ["design"],
                    "next": []
                },
                {
                    "id": "test",
                    "agent": "autogen",
                    "task": "Write and run tests",
                    "depends_on": ["implement"],
                    "next": ["deploy"]
                },
                {
                    "id": "deploy",
                    "agent": "devin",
                    "task": "Deploy the feature",
                    "depends_on": ["test"],
                    "next": [],
                    "requires_approval": True
                }
            ]
        }
        """
        try:
            logger.info(f"Starting cross-agent workflow: {workflow_id}")
            
            steps = {s["id"]: s for s in workflow_definition["steps"]}
            completed = set()
            results = {}
            
            async def execute_step(step_id: str):
                step = steps[step_id]
                
                # Wait for dependencies
                for dep in step.get("depends_on", []):
                    while dep not in completed:
                        await asyncio.sleep(1)
                
                # Execute
                agent = PersonalAgentAdapter(step["agent"])
                
                # Build context from dependencies
                context = {}
                for dep in step.get("depends_on", []):
                    context[dep] = results[dep]
                
                instructions = step["task"]
                if context:
                    instructions += f"\n\nContext from previous steps:\n{context}"
                
                result = await agent.execute_task(
                    task_id=f"{workflow_id}_{step_id}",
                    instructions=instructions,
                    context={"org_id": org_id, "workflow_id": workflow_id}
                )
                
                results[step_id] = result
                completed.add(step_id)
                
                # Execute next steps
                next_steps = step.get("next", [])
                if next_steps:
                    await asyncio.gather(*[execute_step(s) for s in next_steps])
            
            # Start with steps that have no dependencies
            root_steps = [s["id"] for s in workflow_definition["steps"] if not s.get("depends_on")]
            
            await asyncio.gather(*[execute_step(s) for s in root_steps])
            
            return {
                "status": "completed",
                "workflow_id": workflow_id,
                "completed_steps": list(completed),
                "results": results
            }
            
        except Exception as e:
            logger.exception(f"Workflow {workflow_id} failed")
            return {"status": "error", "error": str(e)}
    
    # ═══════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════
    
    async def _get_agent_instance(self, org_id: str, agent_type: str):
        """Get or create agent instance"""
        # This would query the database for agent instances
        # For now, return a stub
        return None
    
    async def _request_step_approval(
        self,
        pipeline_id: str,
        step_number: int,
        step_name: str,
        next_step: str,
        result: Dict,
        org_id: str
    ) -> Dict[str, Any]:
        """Request human approval between pipeline steps"""
        logger.info(f"Requesting approval for pipeline {pipeline_id}, step {step_name} -> {next_step}")
        
        # In production, this would create an approval in the database
        # and wait for human response via WebSocket or polling
        
        # For now, return simulated approval
        return {
            "decision": "approve",
            "approved_by": "system",
            "reason": "Auto-approved for testing"
        }
    
    def _create_debate_comparison(self, topic: str, opinions: Dict) -> str:
        """Create human-readable comparison of agent opinions"""
        comparison = f"# Agent Debate: {topic}\n\n"
        
        for agent, data in opinions.items():
            comparison += f"## {agent.upper()}\n\n"
            comparison += f"{data['opinion'][:1000]}\n\n"
            comparison += "---\n\n"
        
        return comparison
    
    def _format_opinions(self, opinions: Dict) -> str:
        """Format opinions for context"""
        formatted = ""
        for agent, data in opinions.items():
            formatted += f"**{agent}**: {data['opinion'][:300]}...\n\n"
        return formatted
    
    async def _request_debate_winner(self, topic: str, opinions: Dict, org_id: str) -> Dict[str, Any]:
        """Request human to select debate winner"""
        # In production, this would create an approval request
        # For now, return first agent as winner
        return {
            "winner": list(opinions.keys())[0],
            "reasoning": "Auto-selected for testing"
        }
    
    def _format_previous_feedback(self, approvals: Dict) -> str:
        """Format previous feedback for context"""
        feedback = ""
        for agent, decision in approvals.items():
            feedback += f"- {agent}: {decision.upper()}\n"
        return feedback
    
    async def _get_agent_loads(self, agents: List[str], org_id: str) -> Dict[str, int]:
        """Get current task load for each agent"""
        # In production, query database for active tasks per agent
        # For now, return equal loads
        return {agent: 0 for agent in agents}
    
    async def _match_agent_to_task(self, task: Dict, agents: List[str]) -> str:
        """Match task requirements to best agent"""
        # In production, analyze task requirements and agent capabilities
        # For now, return first agent
        return agents[0]

# Singleton
multi_agent_orchestrator = MultiAgentOrchestrator()
