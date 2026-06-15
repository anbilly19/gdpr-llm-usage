"""
Google Vertex AI — Gemini Provider  (AWAY option, EU multi-region / single-region)
===============================================================================
Uses Gemini 2.5 Flash (or any Gemini model) via Vertex AI with the new google-genai SDK.
Set GOOGLE_CLOUD_LOCATION=eu           for EU multi-region (processes data within EU).
Set GOOGLE_CLOUD_LOCATION=europe-west4 for strict Netherlands single-region.

Docs:
  Vertex AI overview            → https://cloud.google.com/vertex-ai/docs/start/introduction-unified-platform
  Generative AI on Vertex AI    → https://cloud.google.com/vertex-ai/generative-ai/docs/learn/overview
  EU multi-region endpoints     → https://cloud.google.com/vertex-ai/docs/general/locations#europe
  Gemini model IDs              → https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versioning
  google-genai SDK              → https://googleapis.github.io/python-genai/

Auth prerequisite:
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
    # OR: gcloud auth application-default login

Usage:
    uv run python providers/vertex_gemini_provider.py
"""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console()


def build_client() -> genai.Client:
    """Return a google-genai Client pointed at Vertex AI in the configured EU location."""
    return genai.Client(
        vertexai=True,
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "eu"),
    )


def chat_stream(prompt: str, model_id: str) -> dict:
    """
    Stream a Gemini chat completion and return token usage.
    Returns: {"response_text": str, "prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    """
    client = build_client()
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "eu")
    console.print(Panel(f"[bold green]Vertex Gemini[/] → {model_id}  (location: {location})", expand=False))
    console.print(f"[dim]Prompt:[/] {prompt}\n")

    config = types.GenerateContentConfig(max_output_tokens=512, temperature=0.7)

    full_text = ""
    prompt_tokens = completion_tokens = 0

    for chunk in client.models.generate_content_stream(
        model=model_id,
        contents=prompt,
        config=config,
    ):
        if chunk.text:
            full_text += chunk.text
            console.print(chunk.text, end="", markup=False)
        if chunk.usage_metadata:
            prompt_tokens = chunk.usage_metadata.prompt_token_count or 0
            completion_tokens = chunk.usage_metadata.candidates_token_count or 0

    total_tokens = prompt_tokens + completion_tokens
    console.print("\n")

    usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }
    _print_usage_table(usage, "Vertex Gemini", model_id)
    return {"response_text": full_text, **usage}


def _print_usage_table(usage: dict, provider: str, model: str) -> None:
    table = Table(title=f"Token Usage — {provider}", show_header=True)
    table.add_column("Field", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Model", model)
    table.add_row("Prompt tokens", str(usage.get("prompt_tokens", "N/A")))
    table.add_row("Completion tokens", str(usage.get("completion_tokens", "N/A")))
    table.add_row("Total tokens", str(usage.get("total_tokens", "N/A")))
    console.print(table)


if __name__ == "__main__":
    model_id = os.environ.get("VERTEX_GEMINI_MODEL", "gemini-2.5-flash-001")
    prompt = "Explain the GDPR Article 46 transfer mechanisms in two sentences."
    chat_stream(prompt, model_id)
