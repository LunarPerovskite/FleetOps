"""Unit tests for usage extraction module."""
import pytest
from unittest.mock import Mock, AsyncMock

import sys
sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/backend')

from app.core.usage_extraction import RealUsageExtractor


class TestOpenAIUsageExtraction:
    """Test extracting usage from OpenAI responses."""

    def test_extract_with_usage_field(self):
        """Test extraction when usage field is present."""
        response = {
            "choices": [{"message": {"content": "Hello"}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            },
            "model": "gpt-4"
        }

        result = RealUsageExtractor.extract_openai_usage(response)

        assert result["input_tokens"] == 10
        assert result["output_tokens"] == 5
        assert result["total_tokens"] == 15
        assert result["has_real_usage"] is True
        assert result["model"] == "gpt-4"

    def test_extract_without_usage_field(self):
        """Test fallback when no usage field."""
        response = {
            "choices": [{"message": {"content": "Hello world this is a test"}}]
        }

        result = RealUsageExtractor.extract_openai_usage(response)

        assert result["has_real_usage"] is False
        assert result["input_tokens"] == 0
        assert result["output_tokens"] > 0  # Estimated from content
        assert result["total_tokens"] > 0

    def test_extract_with_cached_tokens(self):
        """Test extraction with cached tokens (GPT-4o)."""
        response = {
            "choices": [{"message": {"content": "Hello"}}],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "prompt_tokens_details": {
                    "cached_tokens": 80
                }
            }
        }

        result = RealUsageExtractor.extract_openai_usage(response)

        assert result["cached_tokens"] == 80
        assert result["has_real_usage"] is True


class TestAnthropicUsageExtraction:
    """Test extracting usage from Anthropic responses."""

    def test_extract_with_usage(self):
        """Test extraction with Anthropic usage format."""
        response = {
            "content": [{"text": "Hello", "type": "text"}],
            "usage": {
                "input_tokens": 20,
                "output_tokens": 10
            },
            "model": "claude-3-opus-20240229"
        }

        result = RealUsageExtractor.extract_anthropic_usage(response)

        assert result["input_tokens"] == 20
        assert result["output_tokens"] == 10
        assert result["total_tokens"] == 30
        assert result["has_real_usage"] is True

    def test_extract_without_usage(self):
        """Test fallback when no usage."""
        response = {
            "content": [{"text": "Hello world"}]
        }

        result = RealUsageExtractor.extract_anthropic_usage(response)

        assert result["has_real_usage"] is False


class TestGroqUsageExtraction:
    """Test extracting usage from Groq responses."""

    def test_extract_with_x_groq(self):
        """Test with x-groq headers."""
        response = {
            "choices": [{"message": {"content": "Hello"}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5
            },
            "x_groq": {
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5
                }
            }
        }

        result = RealUsageExtractor.extract_groq_usage(response)

        assert result["input_tokens"] == 10
        assert result["output_tokens"] == 5
        assert result["has_real_usage"] is True


class TestPerplexityUsageExtraction:
    """Test extracting usage from Perplexity responses."""

    def test_extract_with_usage(self):
        response = {
            "choices": [{"message": {"content": "Answer"}}],
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 25,
                "total_tokens": 40
            },
            "citations": ["http://example.com"]
        }

        result = RealUsageExtractor.extract_perplexity_usage(response)

        assert result["input_tokens"] == 15
        assert result["output_tokens"] == 25
        assert result["has_real_usage"] is True


class TestOpenRouterUsageExtraction:
    """Test extracting usage from OpenRouter responses."""

    def test_extract_with_usage(self):
        response = {
            "choices": [{"message": {"content": "Hello"}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5
            },
            "model": "openai/gpt-4"
        }

        result = RealUsageExtractor.extract_openrouter_usage(response)

        assert result["input_tokens"] == 10
        assert result["output_tokens"] == 5
        assert result["has_real_usage"] is True


class TestOllamaUsageExtraction:
    """Test extracting usage from Ollama responses."""

    def test_extract_with_prompt_eval(self):
        """Test with prompt_eval_count and eval_count."""
        response = {
            "message": {"content": "Hello"},
            "prompt_eval_count": 100,
            "eval_count": 50,
            "model": "llama3.1:8b"
        }

        result = RealUsageExtractor.extract_ollama_usage(response)

        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["total_tokens"] == 150
        assert result["has_real_usage"] is True
        assert result["model"] == "llama3.1:8b"

    def test_extract_without_counts(self):
        """Test fallback when no counts."""
        response = {
            "message": {"content": "Hello world this is a test response"}
        }

        result = RealUsageExtractor.extract_ollama_usage(response)

        assert result["has_real_usage"] is False
        assert result["input_tokens"] == 0


class TestGeminiUsageExtraction:
    """Test extracting usage from Gemini responses."""

    def test_extract_with_usage_metadata(self):
        response = {
            "candidates": [{"content": {"parts": [{"text": "Hello"}]}}],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 5,
                "totalTokenCount": 15
            }
        }

        result = RealUsageExtractor.extract_gemini_usage(response)

        assert result["input_tokens"] == 10
        assert result["output_tokens"] == 5
        assert result["total_tokens"] == 15
        assert result["has_real_usage"] is True


class TestGenericExtraction:
    """Test the generic extract method."""

    def test_detects_openai(self):
        response = {
            "object": "chat.completion",
            "usage": {"prompt_tokens": 10}
        }

        result = RealUsageExtractor.extract("openai", response)

        assert result["has_real_usage"] is True

    def test_detects_anthropic(self):
        response = {
            "type": "message",
            "usage": {"input_tokens": 10}
        }

        result = RealUsageExtractor.extract("anthropic", response)

        assert result["has_real_usage"] is True

    def test_unknown_provider(self):
        response = {"text": "Hello"}

        result = RealUsageExtractor.extract("unknown", response)

        assert result["has_real_usage"] is False
        assert result["input_tokens"] == 0


class TestTokenEstimation:
    """Test fallback token estimation."""

    def test_estimate_from_text(self):
        """Test estimating tokens from text content."""
        text = "Hello world, this is a test message with approximately twelve tokens."

        result = RealUsageExtractor._estimate_tokens(text)

        assert result > 0
        # Rough estimate: ~4 chars per token for English
        assert result < len(text)

    def test_estimate_empty(self):
        """Test empty text returns 0."""
        result = RealUsageExtractor._estimate_tokens("")
        assert result == 0

    def test_estimate_none(self):
        """Test None returns 0."""
        result = RealUsageExtractor._estimate_tokens(None)
        assert result == 0
