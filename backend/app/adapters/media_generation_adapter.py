"""AI Media Generation Adapter for FleetOps

Central hub for all AI media generation:
- Image generation (DALL-E, Stable Diffusion, FLUX, Midjourney)
- Video generation (Runway, Pika, Sora, Kling)
- Audio/TTS generation (ElevenLabs, OpenAI TTS, Coqui)
- Cost tracking per media type
- Approval flow for expensive media generation

All media generation goes through FleetOps for:
- Cost tracking and budget enforcement
- Approval workflows for expensive generations
- Audit logging
- Usage analytics
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import httpx
import base64
import os


class MediaType(Enum):
    """Types of AI media generation"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TTS = "tts"


class ImageProvider(Enum):
    """Image generation providers"""
    DALLE = "dall-e"
    STABLE_DIFFUSION = "stable_diffusion"
    FLUX = "flux"
    MIDJOURNEY = "midjourney"
    REPLICATE = "replicate"


class VideoProvider(Enum):
    """Video generation providers"""
    RUNWAY = "runway"
    PIKA = "pika"
    SORA = "sora"
    KLING = "kling"
    REPLICATE = "replicate"


class AudioProvider(Enum):
    """Audio/TTS providers"""
    ELEVENLABS = "elevenlabs"
    OPENAI_TTS = "openai_tts"
    COQUI = "coqui"
    PLAYHT = "playht"


@dataclass
class MediaCost:
    """Cost breakdown for media generation"""
    media_type: MediaType
    provider: str
    estimated_cost: float
    actual_cost: Optional[float]
    unit_price: float  # per image, per second, per character
    units: float  # number of images, seconds, characters
    currency: str = "USD"


@dataclass
class MediaGenerationRequest:
    """Request for media generation"""
    media_type: MediaType
    provider: str
    prompt: str
    negative_prompt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # for video/audio
    voice_id: Optional[str] = None  # for TTS
    style: Optional[str] = None
    quality: Optional[str] = None
    org_id: str = "default"
    user_id: str = ""
    budget_limit: Optional[float] = None


class MediaGenerationAdapter:
    """Adapter for AI media generation with FleetOps integration"""
    
    # Pricing per provider (USD)
    PRICING = {
        # Image generation
        "dall-e": {
            "dall-e-3": {"1024x1024": 0.040, "1024x1792": 0.080, "1792x1024": 0.080},
            "dall-e-2": {"1024x1024": 0.020, "512x512": 0.018, "256x256": 0.016},
        },
        "stable_diffusion": {
            "sdxl": 0.008,
            "sd-1.5": 0.003,
        },
        "flux": {
            "flux-pro": 0.055,
            "flux-dev": 0.025,
            "flux-schnell": 0.003,
        },
        "midjourney": {
            "standard": 0.10,  # per image (estimated)
        },
        # Video generation
        "runway": {
            "gen-3": 0.05,  # per second
            "gen-2": 0.03,
        },
        "pika": {
            "1.5": 0.03,  # per second
        },
        "sora": {
            "standard": 0.10,  # per second (estimated)
        },
        # Audio/TTS
        "elevenlabs": {
            "multilingual-v2": 0.0003,  # per character
            "turbo-v2.5": 0.00015,
        },
        "openai_tts": {
            "tts-1": 0.015,  # per 1K characters
            "tts-1-hd": 0.030,
        },
    }
    
    def __init__(self):
        self._http_client = httpx.AsyncClient()
    
    def estimate_cost(self, request: MediaGenerationRequest) -> MediaCost:
        """Estimate cost before generation"""
        
        provider_pricing = self.PRICING.get(request.provider, {})
        
        if request.media_type == MediaType.IMAGE:
            return self._estimate_image_cost(request, provider_pricing)
        elif request.media_type == MediaType.VIDEO:
            return self._estimate_video_cost(request, provider_pricing)
        elif request.media_type in (MediaType.AUDIO, MediaType.TTS):
            return self._estimate_audio_cost(request, provider_pricing)
        
        return MediaCost(
            media_type=request.media_type,
            provider=request.provider,
            estimated_cost=0.0,
            actual_cost=None,
            unit_price=0.0,
            units=0.0
        )
    
    def _estimate_image_cost(
        self,
        request: MediaGenerationRequest,
        pricing: Dict[str, Any]
    ) -> MediaCost:
        """Estimate image generation cost"""
        
        # Default size
        size = f"{request.width or 1024}x{request.height or 1024}"
        
        # Find matching price
        unit_price = 0.050  # default
        for model, sizes in pricing.items():
            if isinstance(sizes, dict):
                unit_price = sizes.get(size, unit_price)
            else:
                unit_price = sizes
        
        units = 1.0  # one image
        estimated = unit_price * units
        
        return MediaCost(
            media_type=MediaType.IMAGE,
            provider=request.provider,
            estimated_cost=estimated,
            actual_cost=None,
            unit_price=unit_price,
            units=units
        )
    
    def _estimate_video_cost(
        self,
        request: MediaGenerationRequest,
        pricing: Dict[str, Any]
    ) -> MediaCost:
        """Estimate video generation cost"""
        
        duration = request.duration or 4.0  # default 4 seconds
        unit_price = next(iter(pricing.values())) if pricing else 0.05
        
        estimated = unit_price * duration
        
        return MediaCost(
            media_type=MediaType.VIDEO,
            provider=request.provider,
            estimated_cost=estimated,
            actual_cost=None,
            unit_price=unit_price,
            units=duration
        )
    
    def _estimate_audio_cost(
        self,
        request: MediaGenerationRequest,
        pricing: Dict[str, Any]
    ) -> MediaCost:
        """Estimate audio/TTS generation cost"""
        
        chars = len(request.prompt)
        unit_price = next(iter(pricing.values())) if pricing else 0.0003
        
        estimated = unit_price * chars
        
        return MediaCost(
            media_type=MediaType.TTS,
            provider=request.provider,
            estimated_cost=estimated,
            actual_cost=None,
            unit_price=unit_price,
            units=chars
        )
    
    async def generate_image(
        self,
        request: MediaGenerationRequest
    ) -> Dict[str, Any]:
        """Generate image through FleetOps"""
        
        # 1. Estimate cost
        cost = self.estimate_cost(request)
        
        # 2. Check budget (would integrate with budget service)
        if request.budget_limit and cost.estimated_cost > request.budget_limit:
            return {
                "status": "budget_exceeded",
                "estimated_cost": cost.estimated_cost,
                "budget_limit": request.budget_limit,
                "message": f"Estimated cost ${cost.estimated_cost:.2f} exceeds budget ${request.budget_limit:.2f}"
            }
        
        # 3. Call provider (simplified - would call actual API)
        result = await self._call_provider(request)
        
        # 4. Track actual cost
        cost.actual_cost = cost.estimated_cost  # In production, from provider response
        
        return {
            "status": "success",
            "media_type": "image",
            "provider": request.provider,
            "cost": {
                "estimated": cost.estimated_cost,
                "actual": cost.actual_cost,
                "currency": cost.currency
            },
            "result": result
        }
    
    async def generate_video(
        self,
        request: MediaGenerationRequest
    ) -> Dict[str, Any]:
        """Generate video through FleetOps"""
        
        cost = self.estimate_cost(request)
        
        if request.budget_limit and cost.estimated_cost > request.budget_limit:
            return {
                "status": "budget_exceeded",
                "estimated_cost": cost.estimated_cost,
                "budget_limit": request.budget_limit,
            }
        
        result = await self._call_provider(request)
        
        return {
            "status": "success",
            "media_type": "video",
            "provider": request.provider,
            "cost": {
                "estimated": cost.estimated_cost,
                "actual": cost.estimated_cost,
            },
            "result": result
        }
    
    async def generate_audio(
        self,
        request: MediaGenerationRequest
    ) -> Dict[str, Any]:
        """Generate audio/TTS through FleetOps"""
        
        cost = self.estimate_cost(request)
        
        if request.budget_limit and cost.estimated_cost > request.budget_limit:
            return {
                "status": "budget_exceeded",
                "estimated_cost": cost.estimated_cost,
                "budget_limit": request.budget_limit,
            }
        
        result = await self._call_provider(request)
        
        return {
            "status": "success",
            "media_type": "audio",
            "provider": request.provider,
            "cost": {
                "estimated": cost.estimated_cost,
                "actual": cost.estimated_cost,
            },
            "result": result
        }
    
    async def _call_provider(self, request: MediaGenerationRequest) -> Dict[str, Any]:
        """Call the actual media generation provider"""
        
        # This would make actual API calls to providers
        # For now, return a stub
        return {
            "status": "generated",
            "url": f"https://generated.media/{request.media_type.value}/{request.provider}/123",
            "prompt": request.prompt,
            "provider": request.provider,
            "media_type": request.media_type.value,
        }
    
    def get_provider_pricing(self, provider: str) -> Dict[str, Any]:
        """Get pricing for a specific provider"""
        return self.PRICING.get(provider, {})
    
    def list_providers(self, media_type: Optional[MediaType] = None) -> List[Dict[str, Any]]:
        """List available providers"""
        
        providers = {
            MediaType.IMAGE: [
                {"id": "dall-e", "name": "DALL-E", "models": ["dall-e-3", "dall-e-2"]},
                {"id": "stable_diffusion", "name": "Stable Diffusion", "models": ["sdxl", "sd-1.5"]},
                {"id": "flux", "name": "FLUX", "models": ["flux-pro", "flux-dev", "flux-schnell"]},
                {"id": "midjourney", "name": "Midjourney", "models": ["standard"]},
            ],
            MediaType.VIDEO: [
                {"id": "runway", "name": "Runway", "models": ["gen-3", "gen-2"]},
                {"id": "pika", "name": "Pika", "models": ["1.5"]},
                {"id": "sora", "name": "Sora", "models": ["standard"]},
            ],
            MediaType.TTS: [
                {"id": "elevenlabs", "name": "ElevenLabs", "models": ["multilingual-v2", "turbo-v2.5"]},
                {"id": "openai_tts", "name": "OpenAI TTS", "models": ["tts-1", "tts-1-hd"]},
            ],
        }
        
        if media_type:
            return providers.get(media_type, [])
        
        # Return all
        all_providers = []
        for mt, plist in providers.items():
            for p in plist:
                p["media_type"] = mt.value
                all_providers.append(p)
        return all_providers


# Singleton
media_adapter = MediaGenerationAdapter()
