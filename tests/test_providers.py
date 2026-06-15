"""
Unit tests for standalone provider modules.

All LLM clients are mocked — no real API calls or credentials required.
Run with:  uv run pytest tests/test_providers.py -v
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch


# Helpers

def _make_env(monkeypatch, extra: dict | None = None) -> None:
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
        "SELF_HOSTED_BASE_URL": "http://localhost:8000/v1",
        "SELF_HOSTED_API_KEY": "local-dev-key",
        "SELF_HOSTED_MODEL": "qwen3-32b",
    }
    if extra:
        base.update(extra)
    for k, v in base.items():
        monkeypatch.setenv(k, v)


def _reload(module_path: str) -> ModuleType:
    if module_path in sys.modules:
        del sys.modules[module_path]
    return importlib.import_module(module_path)


class TestSelfHostedProvider:
    def test_chat_stream_returns_usage(self, monkeypatch):
        _make_env(monkeypatch)

        chunk_text = MagicMock()
        chunk_text.choices = [MagicMock(delta=MagicMock(content="Hello "))]
        chunk_text.usage = None

        chunk_usage = MagicMock()
        chunk_usage.choices = []
        chunk_usage.usage = MagicMock(
            prompt_tokens=9, completion_tokens=6, total_tokens=15
        )

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=iter([chunk_text, chunk_usage]))
        mock_stream.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_stream

        with patch("openai.OpenAI", return_value=mock_client):
            mod = _reload("providers.self_hosted_vllm_provider")
            client = mod.build_client()
            result = mod.chat_stream(client, "Test prompt", "qwen3-32b")

        assert result["response_text"] == "Hello "
        assert result["prompt_tokens"] == 9
        assert result["completion_tokens"] == 6
        assert result["total_tokens"] == 15
