"""
Self-hosted OpenAI-compatible Provider  (HOME option — fully self-managed)
===============================================================================
Use this provider to call a self-hosted OpenAI-compatible endpoint such as:
- vLLM
- Ollama exposed via an OpenAI bridge
- LocalAI
- any internal gateway exposing /v1/chat/completions

This is the strongest option for data control because prompts never leave your
own infrastructure. It fits well for bulk/batch processing, sensitive workloads,
and development environments where API dependencies are undesirable.

Env vars:
    SELF_HOSTED_BASE_URL=http://localhost:8000/v1
    SELF_HOSTED_API_KEY=local-dev-key
    SELF_HOSTED_MODEL=qwen3-32b

Usage:
    uv run python providers/self_hosted_vllm_provider.py
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console()


def build_client() -> OpenAI:
    """Return an OpenAI-compatible client for a self-hosted endpoint."""
    return OpenAI(
        api_key=os.environ.get("SELF_HOSTED_API_KEY", "local-dev-key"),
        base_url=os.environ.get("SELF_HOSTED_BASE_URL", "http://localhost:8000/v1"),
    )


def chat_stream(client: OpenAI, prompt: str, model_id: str) -> dict:
    """
    Stream a chat completion and return token usage.
    Returns: {"response_text": str, "prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    """
    base_url = os.environ.get("SELF_HOSTED_BASE_URL", "http://localhost:8000/v1")
    console.print(Panel(f"[bold blue]Self-hosted[/] → {model_id}  (base_url: {base_url})", expand=False))
    console.print(f"[dim]Prompt:[/] {prompt}\n")

    full_text = ""
    usage = {}

    with client.chat.completions.create(
        model=model_id,
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
    _print_usage_table(usage, "Self-hosted", model_id)
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
    model_id = os.environ.get("SELF_HOSTED_MODEL", "qwen3-32b")
    prompt = "Explain the GDPR Article 46 transfer mechanisms in two sentences."
    chat_stream(client, prompt, model_id)
