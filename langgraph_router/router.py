"""
LangGraph Provider Router
===============================================================================
A provider-agnostic LangGraph graph that routes a chat request to one or more
EU-compliant LLM backends and collects token usage across all invocations.
"""

from __future__ import annotations

import os
from typing import Annotated, Literal
from typing_extensions import TypedDict

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from rich.console import Console

load_dotenv()
console = Console()

ProviderName = Literal[
    "azure", "vertex_gemini", "vertex_claude", "bedrock_claude", "self_hosted", "all"
]


def _merge_usage(existing: list, new: list) -> list:
    return (existing or []) + (new or [])


class GraphState(TypedDict):
    prompt: str
    provider: ProviderName
    usage_records: Annotated[list[dict], _merge_usage]
    responses: Annotated[list[dict], _merge_usage]


def node_azure(state: GraphState) -> dict:
    from providers.azure_openai_provider import build_client, chat_stream
    client = build_client()
    deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
    result = chat_stream(client, state["prompt"], deployment)
    return {
        "responses": [{"provider": "azure", "text": result["response_text"]}],
        "usage_records": [{
            "provider": "Azure OpenAI",
            "model": deployment,
            **{k: result[k] for k in ("prompt_tokens", "completion_tokens", "total_tokens")},
        }],
    }


def node_vertex_gemini(state: GraphState) -> dict:
    from providers.vertex_gemini_provider import chat_stream
    model_id = os.environ.get("VERTEX_GEMINI_MODEL", "gemini-2.5-flash-001")
    result = chat_stream(state["prompt"], model_id)
    return {
        "responses": [{"provider": "vertex_gemini", "text": result["response_text"]}],
        "usage_records": [{
            "provider": "Vertex Gemini",
            "model": model_id,
            **{k: result[k] for k in ("prompt_tokens", "completion_tokens", "total_tokens")},
        }],
    }


def node_vertex_claude(state: GraphState) -> dict:
    from providers.vertex_claude_provider import build_client, chat_stream
    client = build_client()
    model_id = os.environ.get("VERTEX_CLAUDE_MODEL", "claude-sonnet-4-5@20251001")
    result = chat_stream(client, state["prompt"], model_id)
    return {
        "responses": [{"provider": "vertex_claude", "text": result["response_text"]}],
        "usage_records": [{
            "provider": "Vertex Claude",
            "model": model_id,
            **{k: result[k] for k in ("prompt_tokens", "completion_tokens", "total_tokens")},
        }],
    }


def node_bedrock_claude(state: GraphState) -> dict:
    from providers.bedrock_claude_provider import build_client, chat_stream
    client = build_client()
    model_id = os.environ.get("BEDROCK_CLAUDE_MODEL", "anthropic.claude-sonnet-4-5-20251001-v1:0")
    result = chat_stream(client, state["prompt"], model_id)
    return {
        "responses": [{"provider": "bedrock_claude", "text": result["response_text"]}],
        "usage_records": [{
            "provider": "AWS Bedrock Claude",
            "model": model_id,
            **{k: result[k] for k in ("prompt_tokens", "completion_tokens", "total_tokens")},
        }],
    }


def node_self_hosted(state: GraphState) -> dict:
    from providers.self_hosted_vllm_provider import build_client, chat_stream
    client = build_client()
    model_id = os.environ.get("SELF_HOSTED_MODEL", "qwen3-32b")
    result = chat_stream(client, state["prompt"], model_id)
    return {
        "responses": [{"provider": "self_hosted", "text": result["response_text"]}],
        "usage_records": [{
            "provider": "Self-hosted",
            "model": model_id,
            **{k: result[k] for k in ("prompt_tokens", "completion_tokens", "total_tokens")},
        }],
    }


_ALL_PROVIDERS = ["azure", "vertex_gemini", "vertex_claude", "bedrock_claude", "self_hosted"]


def route(state: GraphState) -> list[str]:
    p = state.get("provider", "vertex_gemini")
    if p == "all":
        return _ALL_PROVIDERS
    return [p]


def build_graph() -> StateGraph:
    g = StateGraph(GraphState)
    g.add_node("azure", node_azure)
    g.add_node("vertex_gemini", node_vertex_gemini)
    g.add_node("vertex_claude", node_vertex_claude)
    g.add_node("bedrock_claude", node_bedrock_claude)
    g.add_node("self_hosted", node_self_hosted)
    g.add_conditional_edges(
        START,
        route,
        {
            "azure": "azure",
            "vertex_gemini": "vertex_gemini",
            "vertex_claude": "vertex_claude",
            "bedrock_claude": "bedrock_claude",
            "self_hosted": "self_hosted",
        },
    )
    for node in _ALL_PROVIDERS:
        g.add_edge(node, END)
    return g


if __name__ == "__main__":
    from token_dashboard.dashboard import print_dashboard

    graph = build_graph().compile()
    provider: ProviderName = os.environ.get("PROVIDER", "vertex_gemini")  # type: ignore

    console.rule(f"[bold]LangGraph Router  —  provider={provider}[/]")

    final_state = graph.invoke({
        "prompt": "Explain the GDPR Article 46 transfer mechanisms in two sentences.",
        "provider": provider,
        "usage_records": [],
        "responses": [],
    })

    print_dashboard(final_state["usage_records"])
