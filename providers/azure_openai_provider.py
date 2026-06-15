"""
Azure OpenAI Provider  (HOME option — fully Azure-native, EU Data Boundary compliant)
===============================================================================
Deploys GPT-4o (or any Azure OpenAI deployment) in an EU Azure region.

EU-compliant regions: westeurope, francecentral, swedencentral, germanywestcentral
Data stays within Microsoft’s EU Data Boundary.

Docs:
  Azure OpenAI Service      → https://learn.microsoft.com/en-us/azure/ai-services/openai/
  EU Data Boundary          → https://learn.microsoft.com/en-us/privacy/eudb/eu-data-boundary-learn
  Supported regions         → https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models
  openai Python SDK         → https://github.com/openai/openai-python

Usage:
    uv run python providers/azure_openai_provider.py
"""

import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console()


def build_client() -> AzureOpenAI:
    """Return an authenticated AzureOpenAI client from environment variables."""
    return AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    )


def chat_stream(client: AzureOpenAI, prompt: str, deployment: str) -> dict:
    """
    Stream a chat completion and return token usage.
    Returns: {"response_text": str, "prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    """
    console.print(Panel(f"[bold cyan]Azure OpenAI[/] → {deployment}", expand=False))
    console.print(f"[dim]Prompt:[/] {prompt}\n")

    full_text = ""
    usage = {}

    with client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        stream_options={"include_usage": True},
    ) as stream:
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_text += token
                console.print(token, end="", markup=False)
            if chunk.usage:
                usage = {
                    "prompt_tokens": chunk.usage.prompt_tokens,
                    "completion_tokens": chunk.usage.completion_tokens,
                    "total_tokens": chunk.usage.total_tokens,
                }

    console.print("\n")
    _print_usage_table(usage, "Azure OpenAI", deployment)
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
    client = build_client()
    deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
    prompt = "Explain the GDPR Article 46 transfer mechanisms in two sentences."
    chat_stream(client, prompt, deployment)
