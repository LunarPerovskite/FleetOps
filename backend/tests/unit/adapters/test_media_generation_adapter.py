"""Unit tests for Media Generation Adapter"""
import pytest
import sys

sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/backend')

from app.adapters.media_generation_adapter import (
    MediaGenerationAdapter,
    MediaGenerationRequest,
    MediaType,
    ImageProvider,
    VideoProvider,
    AudioProvider,
    MediaCost
)


class TestMediaGenerationAdapter:
    """Test media generation adapter"""
    
    @pytest.fixture
    def adapter(self):
        return MediaGenerationAdapter()
    
    def test_estimate_image_cost_dalle(self, adapter):
        """Test DALL-E cost estimation"""
        request = MediaGenerationRequest(
            media_type=MediaType.IMAGE,
            provider="dall-e",
            prompt="A beautiful sunset",
            width=1024,
            height=1024
        )
        
        cost = adapter.estimate_cost(request)
        
        assert cost.media_type == MediaType.IMAGE
        assert cost.provider == "dall-e"
        assert cost.estimated_cost > 0
        assert cost.currency == "USD"
    
    def test_estimate_video_cost_runway(self, adapter):
        """Test Runway video cost estimation"""
        request = MediaGenerationRequest(
            media_type=MediaType.VIDEO,
            provider="runway",
            prompt="A cat dancing",
            duration=4.0
        )
        
        cost = adapter.estimate_cost(request)
        
        assert cost.media_type == MediaType.VIDEO
        assert cost.estimated_cost == 4.0 * 0.05  # 4 seconds * $0.05/sec
    
    def test_estimate_audio_cost_elevenlabs(self, adapter):
        """Test ElevenLabs TTS cost estimation"""
        request = MediaGenerationRequest(
            media_type=MediaType.TTS,
            provider="elevenlabs",
            prompt="Hello, this is a test message"
        )
        
        cost = adapter.estimate_cost(request)
        
        assert cost.media_type == MediaType.TTS
        assert cost.units == len("Hello, this is a test message")
        assert cost.estimated_cost > 0
    
    def test_budget_exceeded(self, adapter):
        """Test budget enforcement"""
        request = MediaGenerationRequest(
            media_type=MediaType.IMAGE,
            provider="dall-e",
            prompt="A spaceship",
            budget_limit=0.01  # Very low budget
        )
        
        # Cost should exceed budget
        cost = adapter.estimate_cost(request)
        assert cost.estimated_cost > request.budget_limit
    
    def test_list_providers_by_type(self, adapter):
        """Test listing providers by media type"""
        
        image_providers = adapter.list_providers(MediaType.IMAGE)
        assert len(image_providers) > 0
        assert any(p["id"] == "dall-e" for p in image_providers)
        
        video_providers = adapter.list_providers(MediaType.VIDEO)
        assert len(video_providers) > 0
        assert any(p["id"] == "runway" for p in video_providers)
        
        audio_providers = adapter.list_providers(MediaType.TTS)
        assert len(audio_providers) > 0
        assert any(p["id"] == "elevenlabs" for p in audio_providers)
    
    def test_list_all_providers(self, adapter):
        """Test listing all providers"""
        
        all_providers = adapter.list_providers()
        assert len(all_providers) >= 7  # At least one per media type
        
        # Should have media_type field
        assert all("media_type" in p for p in all_providers)
    
    def test_get_provider_pricing(self, adapter):
        """Test getting provider pricing"""
        
        pricing = adapter.get_provider_pricing("dall-e")
        assert "dall-e-3" in pricing
        assert "dall-e-2" in pricing
    
    def test_get_unknown_provider_pricing(self, adapter):
        """Test getting pricing for unknown provider"""
        
        pricing = adapter.get_provider_pricing("unknown-provider")
        assert pricing == {}


class TestMediaGenerationRequest:
    """Test media generation request dataclass"""
    
    def test_create_image_request(self):
        """Test creating image generation request"""
        request = MediaGenerationRequest(
            media_type=MediaType.IMAGE,
            provider="dall-e",
            prompt="A red car",
            width=1024,
            height=1024,
            quality="hd"
        )
        
        assert request.media_type == MediaType.IMAGE
        assert request.provider == "dall-e"
        assert request.width == 1024
        assert request.height == 1024
        assert request.quality == "hd"
    
    def test_create_video_request(self):
        """Test creating video generation request"""
        request = MediaGenerationRequest(
            media_type=MediaType.VIDEO,
            provider="runway",
            prompt="A sunset timelapse",
            duration=10.0
        )
        
        assert request.media_type == MediaType.VIDEO
        assert request.duration == 10.0
    
    def test_create_tts_request(self):
        """Test creating TTS request"""
        request = MediaGenerationRequest(
            media_type=MediaType.TTS,
            provider="elevenlabs",
            prompt="Hello world",
            voice_id="bella"
        )
        
        assert request.media_type == MediaType.TTS
        assert request.voice_id == "bella"


class TestAsyncGeneration:
    """Test async generation methods"""
    
    @pytest.mark.asyncio
    async def test_generate_image(self):
        """Test async image generation"""
        adapter = MediaGenerationAdapter()
        
        request = MediaGenerationRequest(
            media_type=MediaType.IMAGE,
            provider="dall-e",
            prompt="A blue sky",
            budget_limit=1.0
        )
        
        result = await adapter.generate_image(request)
        
        assert result["status"] == "success"
        assert result["media_type"] == "image"
        assert "cost" in result
        assert result["cost"]["estimated"] > 0
    
    @pytest.mark.asyncio
    async def test_generate_image_budget_exceeded(self):
        """Test image generation with exceeded budget"""
        adapter = MediaGenerationAdapter()
        
        request = MediaGenerationRequest(
            media_type=MediaType.IMAGE,
            provider="dall-e",
            prompt="A spaceship",
            budget_limit=0.01  # Very low
        )
        
        result = await adapter.generate_image(request)
        
        assert result["status"] == "budget_exceeded"
        assert "estimated_cost" in result
        assert "budget_limit" in result
    
    @pytest.mark.asyncio
    async def test_generate_video(self):
        """Test async video generation"""
        adapter = MediaGenerationAdapter()
        
        request = MediaGenerationRequest(
            media_type=MediaType.VIDEO,
            provider="runway",
            prompt="A cat dancing",
            duration=4.0,
            budget_limit=1.0
        )
        
        result = await adapter.generate_video(request)
        
        assert result["status"] == "success"
        assert result["media_type"] == "video"
    
    @pytest.mark.asyncio
    async def test_generate_audio(self):
        """Test async audio generation"""
        adapter = MediaGenerationAdapter()
        
        request = MediaGenerationRequest(
            media_type=MediaType.TTS,
            provider="elevenlabs",
            prompt="Hello world",
            budget_limit=1.0
        )
        
        result = await adapter.generate_audio(request)
        
        assert result["status"] == "success"
        assert result["media_type"] == "audio"


class TestProviderPricing:
    """Test provider pricing accuracy"""
    
    @pytest.fixture
    def adapter(self):
        return MediaGenerationAdapter()
    
    def test_dalle_pricing_structure(self, adapter):
        """Test DALL-E pricing structure"""
        pricing = adapter.get_provider_pricing("dall-e")
        
        assert "dall-e-3" in pricing
        assert "1024x1024" in pricing["dall-e-3"]
        assert pricing["dall-e-3"]["1024x1024"] == 0.040
    
    def test_flux_pricing_structure(self, adapter):
        """Test FLUX pricing structure"""
        pricing = adapter.get_provider_pricing("flux")
        
        assert "flux-pro" in pricing
        assert pricing["flux-pro"] == 0.055
        assert pricing["flux-schnell"] == 0.003
    
    def test_elevenlabs_pricing(self, adapter):
        """Test ElevenLabs pricing"""
        pricing = adapter.get_provider_pricing("elevenlabs")
        
        assert "multilingual-v2" in pricing
        assert pricing["multilingual-v2"] == 0.0003
    
    def test_openai_tts_pricing(self, adapter):
        """Test OpenAI TTS pricing"""
        pricing = adapter.get_provider_pricing("openai_tts")
        
        assert "tts-1" in pricing
        assert pricing["tts-1"] == 0.015


class TestEdgeCases:
    """Test edge cases"""
    
    @pytest.fixture
    def adapter(self):
        return MediaGenerationAdapter()
    
    def test_empty_prompt(self, adapter):
        """Handle empty prompt"""
        request = MediaGenerationRequest(
            media_type=MediaType.IMAGE,
            provider="dall-e",
            prompt=""
        )
        
        cost = adapter.estimate_cost(request)
        assert cost.estimated_cost >= 0
    
    def test_very_long_prompt(self, adapter):
        """Handle very long prompt"""
        request = MediaGenerationRequest(
            media_type=MediaType.TTS,
            provider="elevenlabs",
            prompt="Hello " * 1000
        )
        
        cost = adapter.estimate_cost(request)
        assert cost.units == len("Hello " * 1000)
        assert cost.estimated_cost > 0
    
    def test_unknown_provider(self, adapter):
        """Handle unknown provider gracefully"""
        request = MediaGenerationRequest(
            media_type=MediaType.IMAGE,
            provider="unknown",
            prompt="Test"
        )
        
        cost = adapter.estimate_cost(request)
        # Unknown provider uses default pricing
        assert cost.estimated_cost >= 0
        assert cost.unit_price == 0.05  # default price
    
    def test_zero_budget(self, adapter):
        """Test zero budget"""
        request = MediaGenerationRequest(
            media_type=MediaType.IMAGE,
            provider="dall-e",
            prompt="Test",
            budget_limit=0.0
        )
        
        cost = adapter.estimate_cost(request)
        # Any cost > 0 should exceed zero budget
        assert cost.estimated_cost > request.budget_limit
