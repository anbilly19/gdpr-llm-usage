"""
Google Vertex AI — Anthropic Claude Provider  (AWAY option, EU multi-region)
===============================================================================
Uses Claude Sonnet (or any Claude model) via Vertex AI’s EU multi-region endpoint.
This is the recommended path for Anthropic models with EU data residency today,
as Azure Foundry’s EU support for Claude is still roadmap (planned 2026).

Set GOOGLE_CLOUD_LOCATION=eu           for EU multi-region (pooled EU capacity).
Set GOOGLE_CLOUD_LOCATION=europe-west4 for strict single-region Netherlands.

Docs:
  Claude on Vertex AI             → https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude
  EU multi-region for Claude      → https://cloud.google.com/blog/products/ai-machine-learning/multi-region-endpoints-for-claude-available-on-vertex-ai
  Supported Claude model IDs      → https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude#supported_models
  anthropic[vertex] Python SDK    → https://github.com/anthropics/anthropic-sdk-python#vertex-ai

Auth prerequisite:
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
    # OR: gcloud auth application-default login

Usage:
    uv run python providers/vertex_claude_provider.py
"""

import os
from dotenv import load_dotenv
from anthropic import AnthropicVertex
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console()


def build_client() -> AnthropicVertex:
    """Return an AnthropicVertex client pointed at the EU region."""
    return AnthropicVertex(
        project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
        region=os.environ.get("GOOGLE_CLOUD_LOCATION", "eu"),
    )


def chat_stream(client: AnthropicVertex, prompt: str, model_id: str) -> dict:
    """
    Stream a Claude chat completion via Vertex and return token usage.
    Returns: {"response_text": str, "prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    """
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "eu")
    console.print(Panel(f"[bold magenta]Vertex Claude[/] → {model_id}  (region: {location})", expand=False))
    console.print(f"[dim]Prompt:[/] {prompt}\n")

    full_text = ""
    prompt_tokens = completion_tokens = 0

    with client.messages.stream(
        model=model_id,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            full_text += text
            console.print(text, end="", markup=False)
        # Final message carries usage
        final = stream.get_final_message()
        prompt_tokens = final.usage.input_tokens
        completion_tokens = final.usage.output_tokens

    total_tokens = prompt_tokens + completion_tokens
    console.print("\n")

    usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }
    _print_usage_table(usage, "Vertex Claude", model_id)
    return {"response_text": full_text, **usage}


def _print_usage_table(usage: dict, provider: str, model: str) -> None:
    table = Table(title=f"Token Usage — {provider}", show_header=True)
    table.add_column("Field", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Model", model)
    table.add_row("Input tokens", str(usage.get("prompt_tokens", "N/A")))
    table.add_row("Output tokens", str(usage.get("completion_tokens", "N/A")))
    table.add_row("Total tokens", str(usage.get("total_tokens", "N/A")))
    console.print(table)


if __name__ == "__main__":
    client = build_client()
    model_id = os.environ.get("VERTEX_CLAUDE_MODEL", "claude-sonnet-4-5@20251001")
    prompt = "Explain the GDPR Article 46 transfer mechanisms in two sentences."
    chat_stream(client, prompt, model_id)
