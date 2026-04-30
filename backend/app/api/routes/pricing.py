"""Pricing Management API Routes for FleetOps

User-configurable pricing for any service/model.
Fetch pricing from provider APIs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from decimal import Decimal

from app.api.routes.auth import get_current_user
from app.models.models import User
from app.core.cost_tracking import cost_tracker

router = APIRouter(prefix="/pricing", tags=["Pricing Management"])


@router.get("/models")
async def list_models(
    service: Optional[str] = Query(None, description="Filter by service"),
    current_user: User = Depends(get_current_user)
):
    """List all models with pricing (auto-fetched + user-configured)"""
    try:
        models = await cost_tracker.list_available_models(service)
        return {
            "status": "success",
            "models": models,
            "count": len(models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configure")
async def configure_pricing(
    service: str,
    model: str,
    input_rate_per_1m: float,
    output_rate_per_1m: float,
    model_name: Optional[str] = None,
    pricing_type: str = "pay_per_token",
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Configure custom pricing for any service/model
    
    Use this to:
    - Add pricing for new models not in our database
    - Override API-fetched pricing with your negotiated rates
    - Configure local models with estimated costs
    - Set up subscription services
    """
    try:
        result = await cost_tracker.add_user_pricing(
            service=service,
            model=model,
            input_rate_per_1m=input_rate_per_1m,
            output_rate_per_1m=output_rate_per_1m,
            model_name=model_name,
            notes=notes
        )
        return {
            "status": "success",
            "message": f"Pricing configured for {service}/{model}",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fetch/{service}")
async def fetch_provider_pricing(
    service: str,
    current_user: User = Depends(get_current_user)
):
    """Force fetch latest pricing from a provider API"""
    try:
        from app.core.cost_tracking import ProviderPricingFetcher
        
        if service == "openrouter":
            models = await ProviderPricingFetcher.fetch_openrouter_pricing()
        elif service == "groq":
            models = await ProviderPricingFetcher.fetch_groq_pricing()
        elif service == "together":
            models = await ProviderPricingFetcher.fetch_together_pricing()
        else:
            raise HTTPException(status_code=400, detail=f"Provider {service} not supported")
        
        # Refresh cache
        await cost_tracker._refresh_pricing_cache()
        
        return {
            "status": "success",
            "service": service,
            "models_fetched": len(models),
            "models": models[:10]  # First 10
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate")
async def calculate_cost(
    service: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Calculate estimated cost for a request (before making it)"""
    try:
        pricing = await cost_tracker.get_pricing(service, model)
        cost = cost_tracker.calculate_cost(
            service, model,
            input_tokens, output_tokens, cached_tokens,
            pricing
        )
        
        return {
            "status": "success",
            "service": service,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_tokens": cached_tokens,
            "estimated_cost_usd": str(cost),
            "pricing_source": "user_configured" if pricing and pricing.get("is_user_configured") else "api_fetched",
            "rates": {
                "input_per_1m": pricing.get("input_rate_per_1m") if pricing else None,
                "output_per_1m": pricing.get("output_rate_per_1m") if pricing else None,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
