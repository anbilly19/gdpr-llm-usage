"""
Unit tests for standalone provider modules.

All LLM clients are mocked — no real API calls or credentials required.
Run with:  uv run pytest tests/test_providers.py -v
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_env(monkeypatch, extra: dict | None = None) -> None:
    """Set minimum env vars so providers can be imported without real credentials."""
    base = {
        "AZURE_OPENAI_API_KEY": "fake-azure-key",
        "AZURE_OPENAI_ENDPOINT": "https://fake.openai.azure.com/",
        "AZURE_OPENAI_DEPLOYMENT": "gpt-4o",
        "AZURE_OPENAI_API_VERSION": "2025-01-01-preview",
        "GOOGLE_CLOUD_PROJECT": "fake-project",
        "GOOGLE_CLOUD_LOCATION": "eu",
        "VERTEX_GEMINI_MODEL": "gemini-2.5-flash-001",
        "VERTEX_CLAUDE_MODEL": "claude-sonnet-4-5@20251001",
        "AWS_ACCESS_KEY_ID": "fake-aws-key",
        "AWS_SECRET_ACCESS_KEY": "fake-aws-secret",
        "AWS_REGION": "eu-central-1",
        "BEDROCK_CLAUDE_MODEL": "anthropic.claude-sonnet-4-5-20251001-v1:0",
    }
    if extra:
        base.update(extra)
    for k, v in base.items():
        monkeypatch.setenv(k, v)


def _reload(module_path: str) -> ModuleType:
    """Force-reload a module so monkeypatched env vars are picked up."""
    if module_path in sys.modules:
        del sys.modules[module_path]
    return importlib.import_module(module_path)


# ─────────────────────────────────────────────────────────────────────────────
# Azure OpenAI
# ─────────────────────────────────────────────────────────────────────────────

class TestAzureOpenAIProvider:
    def test_chat_stream_returns_usage(self, monkeypatch):
        _make_env(monkeypatch)

        # Build mock streaming chunks
        chunk_text = MagicMock()
        chunk_text.choices = [MagicMock(delta=MagicMock(content="Hello "))]
        chunk_text.usage = None

        chunk_usage = MagicMock()
        chunk_usage.choices = []
        chunk_usage.usage = MagicMock(
            prompt_tokens=10, completion_tokens=5, total_tokens=15
        )

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=iter([chunk_text, chunk_usage]))
        mock_stream.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_stream

        with patch("openai.AzureOpenAI", return_value=mock_client):
            mod = _reload("providers.azure_openai_provider")
            client = mod.build_client()
            result = mod.chat_stream(client, "Test prompt", "gpt-4o")

        assert "response_text" in result
        assert result["total_tokens"] == 15
        assert result["prompt_tokens"] == 10
        assert result["completion_tokens"] == 5

    def test_build_client_uses_env_vars(self, monkeypatch):
        _make_env(monkeypatch)
        with patch("openai.AzureOpenAI") as mock_cls:
            mock_cls.return_value = MagicMock()
            mod = _reload("providers.azure_openai_provider")
            mod.build_client()
            call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["api_key"] == "fake-azure-key"
        assert "fake.openai.azure.com" in call_kwargs["azure_endpoint"]


# ─────────────────────────────────────────────────────────────────────────────
# Vertex Gemini
# ─────────────────────────────────────────────────────────────────────────────

class TestVertexGeminiProvider:
    def test_chat_stream_returns_usage(self, monkeypatch):
        _make_env(monkeypatch)

        # Mock usage_metadata on final chunk
        chunk_final = MagicMock()
        chunk_final.text = "World"
        chunk_final.usage_metadata = MagicMock(
            prompt_token_count=12, candidates_token_count=8
        )

        mock_model = MagicMock()
        mock_model.generate_content.return_value = iter([chunk_final])

        with (
            patch("google.cloud.aiplatform.init"),
            patch("vertexai.generative_models.GenerativeModel", return_value=mock_model),
        ):
            mod = _reload("providers.vertex_gemini_provider")
            result = mod.chat_stream("Test prompt", "gemini-2.5-flash-001")

        assert result["response_text"] == "World"
        assert result["prompt_tokens"] == 12
        assert result["completion_tokens"] == 8
        assert result["total_tokens"] == 20


# ─────────────────────────────────────────────────────────────────────────────
# Vertex Claude
# ─────────────────────────────────────────────────────────────────────────────

class TestVertexClaudeProvider:
    def test_chat_stream_returns_usage(self, monkeypatch):
        _make_env(monkeypatch)

        mock_final_msg = MagicMock()
        mock_final_msg.usage = MagicMock(input_tokens=15, output_tokens=10)

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["Hello", " world"])
        mock_stream_ctx.get_final_message.return_value = mock_final_msg

        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_stream_ctx

        with patch("anthropic.AnthropicVertex", return_value=mock_client):
            mod = _reload("providers.vertex_claude_provider")
            client = mod.build_client()
            result = mod.chat_stream(client, "Test prompt", "claude-sonnet-4-5@20251001")

        assert result["response_text"] == "Hello world"
        assert result["prompt_tokens"] == 15
        assert result["completion_tokens"] == 10
        assert result["total_tokens"] == 25

    def test_build_client_uses_eu_location(self, monkeypatch):
        _make_env(monkeypatch)
        with patch("anthropic.AnthropicVertex") as mock_cls:
            mock_cls.return_value = MagicMock()
            mod = _reload("providers.vertex_claude_provider")
            mod.build_client()
            call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["region"] == "eu"
        assert call_kwargs["project_id"] == "fake-project"


# ─────────────────────────────────────────────────────────────────────────────
# AWS Bedrock Claude
# ─────────────────────────────────────────────────────────────────────────────

class TestBedrockClaudeProvider:
    def test_chat_stream_returns_usage(self, monkeypatch):
        _make_env(monkeypatch)

        mock_final_msg = MagicMock()
        mock_final_msg.usage = MagicMock(input_tokens=20, output_tokens=12)

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["Test", " response"])
        mock_stream_ctx.get_final_message.return_value = mock_final_msg

        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_stream_ctx

        with patch("anthropic.AnthropicBedrock", return_value=mock_client):
            mod = _reload("providers.bedrock_claude_provider")
            client = mod.build_client()
            result = mod.chat_stream(client, "Test prompt", "anthropic.claude-sonnet-4-5-20251001-v1:0")

        assert result["response_text"] == "Test response"
        assert result["prompt_tokens"] == 20
        assert result["completion_tokens"] == 12
        assert result["total_tokens"] == 32

    def test_build_client_uses_eu_region(self, monkeypatch):
        _make_env(monkeypatch)
        with patch("anthropic.AnthropicBedrock") as mock_cls:
            mock_cls.return_value = MagicMock()
            mod = _reload("providers.bedrock_claude_provider")
            mod.build_client()
            call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["aws_region"] == "eu-central-1"


# ─────────────────────────────────────────────────────────────────────────────
# Token Dashboard
# ─────────────────────────────────────────────────────────────────────────────

class TestTokenDashboard:
    def test_print_dashboard_with_records(self, capsys):
        from token_dashboard.dashboard import print_dashboard

        records = [
            {"provider": "Azure OpenAI", "model": "gpt-4o",
             "prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            {"provider": "Vertex Gemini", "model": "gemini-2.5-flash-001",
             "prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
        ]
        # Should not raise
        print_dashboard(records)

    def test_print_dashboard_empty(self, capsys):
        from token_dashboard.dashboard import print_dashboard
        print_dashboard([])  # Should not raise

    def test_totals_are_correct(self):
        from token_dashboard.dashboard import print_dashboard
        records = [
            {"provider": "A", "model": "m1", "prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            {"provider": "B", "model": "m2", "prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        ]
        total = sum(r["total_tokens"] for r in records)
        assert total == 45
