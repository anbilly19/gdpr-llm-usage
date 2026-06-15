"""
Unit tests for the LangGraph router and LLMHarness.

All provider nodes are mocked so no real LLM calls are made.
Run with:  uv run pytest tests/test_router.py -v
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fake_provider_result(provider_key: str) -> dict:
    """Return a realistic provider node output for mocking."""
    return {
        "responses": [{"provider": provider_key, "text": f"Response from {provider_key}"}],
        "usage_records": [{
            "provider": provider_key,
            "model": f"mock-model-{provider_key}",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        }],
    }


def _make_env(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "fake-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "eu")
    monkeypatch.setenv("VERTEX_GEMINI_MODEL", "gemini-2.5-flash-001")
    monkeypatch.setenv("VERTEX_CLAUDE_MODEL", "claude-sonnet-4-5@20251001")
    monkeypatch.setenv("BEDROCK_CLAUDE_MODEL", "anthropic.claude-sonnet-4-5-20251001-v1:0")
    monkeypatch.setenv("AWS_REGION", "eu-central-1")


# ─────────────────────────────────────────────────────────────────────────────
# Router graph tests
# ─────────────────────────────────────────────────────────────────────────────

class TestLangGraphRouter:

    def test_route_single_provider(self, monkeypatch):
        """route() should return a list with one node name for a single provider."""
        _make_env(monkeypatch)
        # Clear cached module
        for mod in list(sys.modules.keys()):
            if "langgraph_router" in mod:
                del sys.modules[mod]

        from langgraph_router.router import route

        state = {"prompt": "test", "provider": "vertex_gemini", "usage_records": [], "responses": []}
        assert route(state) == ["vertex_gemini"]

    def test_route_all_providers(self, monkeypatch):
        """route() should return all four provider node names when provider='all'."""
        _make_env(monkeypatch)
        for mod in list(sys.modules.keys()):
            if "langgraph_router" in mod:
                del sys.modules[mod]

        from langgraph_router.router import route, _ALL_PROVIDERS

        state = {"prompt": "test", "provider": "all", "usage_records": [], "responses": []}
        result = route(state)
        assert set(result) == set(_ALL_PROVIDERS)

    def test_graph_invocation_single_provider(self, monkeypatch):
        """Invoking the graph with a single provider should produce one usage record."""
        _make_env(monkeypatch)
        for mod in list(sys.modules.keys()):
            if "langgraph_router" in mod:
                del sys.modules[mod]

        from langgraph_router.router import build_graph

        with patch("langgraph_router.router.node_vertex_gemini",
                   return_value=_fake_provider_result("vertex_gemini")):
            graph = build_graph().compile()
            final_state = graph.invoke({
                "prompt": "Test",
                "provider": "vertex_gemini",
                "usage_records": [],
                "responses": [],
            })

        assert len(final_state["usage_records"]) == 1
        assert final_state["usage_records"][0]["provider"] == "vertex_gemini"

    def test_graph_invocation_all_providers(self, monkeypatch):
        """Invoking with provider='all' should produce one usage record per provider."""
        _make_env(monkeypatch)
        for mod in list(sys.modules.keys()):
            if "langgraph_router" in mod:
                del sys.modules[mod]

        from langgraph_router.router import build_graph, _ALL_PROVIDERS

        patches = {
            f"langgraph_router.router.node_{p}": MagicMock(return_value=_fake_provider_result(p))
            for p in _ALL_PROVIDERS
        }

        with patch.multiple("langgraph_router.router", **{
            f"node_{p}": MagicMock(return_value=_fake_provider_result(p))
            for p in _ALL_PROVIDERS
        }):
            graph = build_graph().compile()
            final_state = graph.invoke({
                "prompt": "Test",
                "provider": "all",
                "usage_records": [],
                "responses": [],
            })

        assert len(final_state["usage_records"]) == len(_ALL_PROVIDERS)

    def test_usage_reducer_accumulates(self, monkeypatch):
        """The _merge_usage reducer should concatenate lists."""
        _make_env(monkeypatch)
        for mod in list(sys.modules.keys()):
            if "langgraph_router" in mod:
                del sys.modules[mod]

        from langgraph_router.router import _merge_usage

        a = [{"provider": "A", "total_tokens": 10}]
        b = [{"provider": "B", "total_tokens": 20}]
        result = _merge_usage(a, b)
        assert len(result) == 2
        assert result[0]["provider"] == "A"
        assert result[1]["provider"] == "B"


# ─────────────────────────────────────────────────────────────────────────────
# LLMHarness tests
# ─────────────────────────────────────────────────────────────────────────────

class TestLLMHarness:

    def _mock_graph(self, provider: str) -> MagicMock:
        """Return a mock compiled graph that returns one fake result."""
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "responses": [{"provider": provider, "text": "Mocked response"}],
            "usage_records": [{
                "provider": provider,
                "model": "mock-model",
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            }],
        }
        return mock_graph

    def test_run_returns_harness_result(self, monkeypatch):
        _make_env(monkeypatch)
        for mod in list(sys.modules.keys()):
            if "langgraph_router" in mod:
                del sys.modules[mod]

        from langgraph_router.harness import LLMHarness

        harness = LLMHarness(provider="vertex_gemini")
        harness._graph = self._mock_graph("vertex_gemini")

        result = harness.run("Test prompt")
        assert result.provider == "vertex_gemini"
        assert result.response_text == "Mocked response"
        assert result.total_tokens == 15
        assert result.usage["prompt_tokens"] == 10

    def test_run_all_returns_list(self, monkeypatch):
        _make_env(monkeypatch)
        for mod in list(sys.modules.keys()):
            if "langgraph_router" in mod:
                del sys.modules[mod]

        from langgraph_router.harness import LLMHarness
        from langgraph_router.router import _ALL_PROVIDERS

        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "responses": [{"provider": p, "text": f"Response {p}"} for p in _ALL_PROVIDERS],
            "usage_records": [{
                "provider": p,
                "model": "mock-model",
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            } for p in _ALL_PROVIDERS],
        }

        harness = LLMHarness(provider="all")
        harness._graph = mock_graph

        results = harness.run_all("Test prompt")
        assert len(results) == len(_ALL_PROVIDERS)
        for r in results:
            assert r.total_tokens == 15

    def test_harness_result_usage_property(self):
        from langgraph_router.harness import HarnessResult

        r = HarnessResult(
            provider="test",
            response_text="hello",
            prompt_tokens=5,
            completion_tokens=3,
            total_tokens=8,
        )
        assert r.usage == {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
