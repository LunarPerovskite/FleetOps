"""Cost Management API Routes for FleetOps

Endpoints for tracking and managing AI service costs:
- View costs by task, agent, user, service
- Set budgets and alerts
- Export cost reports
- Configure pricing
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from app.core.auth import get_current_user
from app.models.models import User
from app.core.cost_tracking import cost_tracker, PricingModel

router = APIRouter(prefix="/costs", tags=["Cost Management"])


@router.get("/summary")
async def get_cost_summary(
    period: Optional[str] = Query(None, description="Filter by period: day, week, month"),
    current_user: User = Depends(get_current_user)
):
    """Get overall cost summary"""
    try:
        summary = cost_tracker.get_summary(period)
        return {
            "status": "success",
            **summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_task_costs(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed costs for a specific task"""
    try:
        entries = cost_tracker.get_detailed_report(task_id)
        total_cost = cost_tracker.get_task_cost(task_id)
        budget = cost_tracker.budgets.get(task_id)
        
        return {
            "status": "success",
            "task_id": task_id,
            "total_cost": str(total_cost),
            "budget": str(budget) if budget else None,
            "budget_status": {
                "has_budget": budget is not None,
                "limit": str(budget) if budget else None,
                "spent": str(total_cost),
                "remaining": str(budget - total_cost) if budget else None,
                "percent_used": float((total_cost / budget * 100)) if budget else None
            },
            "entries": entries,
            "entry_count": len(entries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/{agent_id}")
async def get_agent_costs(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get total costs for an agent"""
    try:
        total_cost = cost_tracker.get_agent_cost(agent_id)
        entries = [e for e in cost_tracker.entries if e.agent_id == agent_id]
        
        by_service = {}
        for e in entries:
            if e.service not in by_service:
                by_service[e.service] = {"cost": Decimal("0"), "tokens": 0}
            by_service[e.service]["cost"] += e.total_cost
            by_service[e.service]["tokens"] += e.input_tokens + e.output_tokens
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "total_cost": str(total_cost),
            "total_requests": len(entries),
            "total_tokens": sum(e.input_tokens + e.output_tokens for e in entries),
            "by_service": {
                k: {
                    "cost": str(v["cost"]),
                    "total_tokens": v["tokens"]
                }
                for k, v in by_service.items()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_costs(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get cost summary for a user"""
    try:
        return {
            "status": "success",
            **cost_tracker.get_user_cost(user_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def list_services(
    current_user: User = Depends(get_current_user)
):
    """List all tracked services and their pricing models"""
    try:
        from app.core.cost_tracking import PRICING_CONFIGS
        
        services = []
        for key, config in PRICING_CONFIGS.items():
            services.append({
                "id": key,
                "pricing_model": config.model.value,
                "input_rate": str(config.input_rate) if config.input_rate else None,
                "output_rate": str(config.output_rate) if config.output_rate else None,
                "monthly_cost": str(config.monthly_cost) if config.monthly_cost else None,
                "hourly_rate": str(config.hourly_rate) if config.hourly_rate else None,
                "included_tokens": config.included_tokens
            })
        
        return {
            "status": "success",
            "services": services,
            "count": len(services)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget/{task_id}")
async def set_task_budget(
    task_id: str,
    max_cost_usd: float,
    current_user: User = Depends(get_current_user)
):
    """Set budget limit for a task"""
    try:
        cost_tracker.set_budget(task_id, max_cost_usd)
        return {
            "status": "success",
            "message": f"Budget set for task {task_id}",
            "task_id": task_id,
            "budget_usd": max_cost_usd
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budget/{task_id}")
async def get_task_budget(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get budget status for a task"""
    try:
        budget = cost_tracker.budgets.get(task_id)
        spent = cost_tracker.get_task_cost(task_id)
        
        if not budget:
            return {
                "status": "success",
                "task_id": task_id,
                "has_budget": False,
                "spent": str(spent)
            }
        
        return {
            "status": "success",
            "task_id": task_id,
            "has_budget": True,
            "budget_usd": str(budget),
            "spent_usd": str(spent),
            "remaining_usd": str(budget - spent),
            "percent_used": float((spent / budget) * 100)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_cost_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = Query("service", description="Group by: service, agent, task, user, day"),
    current_user: User = Depends(get_current_user)
):
    """Generate a cost report with optional date range"""
    try:
        entries = cost_tracker.entries
        
        # Filter by date range
        if start_date:
            start = datetime.fromisoformat(start_date)
            entries = [e for e in entries if datetime.fromisoformat(e.timestamp) >= start]
        if end_date:
            end = datetime.fromisoformat(end_date)
            entries = [e for e in entries if datetime.fromisoformat(e.timestamp) <= end]
        
        # Group data
        grouped = {}
        if group_by == "service":
            for e in entries:
                key = e.service
                if key not in grouped:
                    grouped[key] = {"cost": Decimal("0"), "tokens": 0, "count": 0}
                grouped[key]["cost"] += e.total_cost
                grouped[key]["tokens"] += e.input_tokens + e.output_tokens
                grouped[key]["count"] += 1
        
        elif group_by == "agent":
            for e in entries:
                key = e.agent_id
                if key not in grouped:
                    grouped[key] = {"cost": Decimal("0"), "tokens": 0, "count": 0}
                grouped[key]["cost"] += e.total_cost
                grouped[key]["tokens"] += e.input_tokens + e.output_tokens
                grouped[key]["count"] += 1
        
        elif group_by == "day":
            for e in entries:
                key = datetime.fromisoformat(e.timestamp).strftime("%Y-%m-%d")
                if key not in grouped:
                    grouped[key] = {"cost": Decimal("0"), "tokens": 0, "count": 0}
                grouped[key]["cost"] += e.total_cost
                grouped[key]["tokens"] += e.input_tokens + e.output_tokens
                grouped[key]["count"] += 1
        
        return {
            "status": "success",
            "report": {
                "start_date": start_date,
                "end_date": end_date,
                "group_by": group_by,
                "total_cost": str(sum(e.total_cost for e in entries)),
                "total_requests": len(entries),
                "total_tokens": sum(e.input_tokens + e.output_tokens for e in entries),
                "groups": {
                    k: {
                        "cost": str(v["cost"]),
                        "tokens": v["tokens"],
                        "requests": v["count"]
                    }
                    for k, v in grouped.items()
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_costs(
    format: str = Query("json", description="Export format: json, csv"),
    current_user: User = Depends(get_current_user)
):
    """Export all cost data"""
    try:
        import json
        import csv
        import io
        from fastapi.responses import StreamingResponse
        
        if format == "json":
            data = {
                "exported_at": datetime.utcnow().isoformat(),
                "summary": cost_tracker.get_summary(),
                "entries": cost_tracker.get_detailed_report()
            }
            
            output = io.StringIO()
            json.dump(data, output, indent=2, default=str)
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=costs.json"}
            )
        
        elif format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "timestamp", "service", "model", "agent_id", "task_id",
                "input_tokens", "output_tokens", "api_cost", "compute_cost",
                "total_cost", "pricing_model"
            ])
            
            for e in cost_tracker.entries:
                writer.writerow([
                    e.timestamp, e.service, e.model, e.agent_id, e.task_id,
                    e.input_tokens, e.output_tokens, str(e.api_cost),
                    str(e.compute_cost), str(e.total_cost), e.pricing_model.value
                ])
            
            output.seek(0)
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=costs.csv"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
