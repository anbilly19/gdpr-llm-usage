"""
LangGraph Provider Router
===============================================================================
A provider-agnostic LangGraph graph that routes a chat request to one or more
EU-compliant LLM backends and collects token usage across all invocations.

Graph topology:

    [START]
       │
    [route]          ← decides which provider(s) to call based on GraphState.provider
       ├──────────────── azure
       ├──────────────── vertex_gemini
       ├──────────────── vertex_claude
       └──────────────── bedrock_claude
            │ (all converge)
         [collect_usage]
              │
           [END]

Each provider node calls the corresponding standalone provider module,
so this file is purely orchestration — no LLM logic lives here.

Docs:
  LangGraph concepts              → https://langchain-ai.github.io/langgraph/concepts/
  LangGraph how-to guides         → https://langchain-ai.github.io/langgraph/how-tos/
  Conditional edges               → https://langchain-ai.github.io/langgraph/how-tos/branching/

Usage:
    uv run python langgraph_router/router.py
    # or specify a provider:
    PROVIDER=vertex_gemini uv run python langgraph_router/router.py
    # run all providers in sequence for comparison:
    PROVIDER=all uv run python langgraph_router/router.py
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

# ────────────────────────────────────────────────────────────────────────────
# State
# ────────────────────────────────────────────────────────────────────────────

ProviderName = Literal["azure", "vertex_gemini", "vertex_claude", "bedrock_claude", "all"]


def _merge_usage(existing: list, new: list) -> list:
    """LangGraph reducer: accumulate usage records across all provider nodes."""
    return (existing or []) + (new or [])


class GraphState(TypedDict):
    """Shared state flowing through the LangGraph graph."""
    prompt: str                                              # user input
    provider: ProviderName                                   # which provider to invoke
    usage_records: Annotated[list[dict], _merge_usage]       # accumulated token usage
    responses: Annotated[list[dict], _merge_usage]           # accumulated responses


# ────────────────────────────────────────────────────────────────────────────
# Provider nodes (thin wrappers calling standalone provider modules)
# ────────────────────────────────────────────────────────────────────────────

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


# ────────────────────────────────────────────────────────────────────────────
# Routing logic
# ────────────────────────────────────────────────────────────────────────────

_ALL_PROVIDERS = ["azure", "vertex_gemini", "vertex_claude", "bedrock_claude"]


def route(state: GraphState) -> list[str]:
    """
    Conditional edge function: returns the list of node names to invoke next.
    'all' fans out to every provider in parallel (LangGraph handles concurrency).
    """
    p = state.get("provider", "vertex_gemini")
    if p == "all":
        return _ALL_PROVIDERS
    return [p]


# ────────────────────────────────────────────────────────────────────────────
# Graph assembly
# ────────────────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(GraphState)

    # Add provider nodes
    g.add_node("azure", node_azure)
    g.add_node("vertex_gemini", node_vertex_gemini)
    g.add_node("vertex_claude", node_vertex_claude)
    g.add_node("bedrock_claude", node_bedrock_claude)

    # Fan-out: START → conditional edge → one or all provider nodes
    g.add_conditional_edges(
        START,
        route,
        {
            "azure": "azure",
            "vertex_gemini": "vertex_gemini",
            "vertex_claude": "vertex_claude",
            "bedrock_claude": "bedrock_claude",
        },
    )

    # All provider nodes converge at END
    # (usage_records and responses are merged via the Annotated reducer)
    for node in _ALL_PROVIDERS:
        g.add_edge(node, END)

    return g


# ────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ────────────────────────────────────────────────────────────────────────────

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
