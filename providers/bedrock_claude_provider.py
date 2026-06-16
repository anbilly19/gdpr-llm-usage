"""
AWS Bedrock — Anthropic Claude Provider  (AWAY option, EU AWS regions)
===============================================================================
Uses Claude Sonnet (or any Bedrock-hosted Claude) in an EU AWS region.

EU regions with Anthropic Claude support:
  eu-west-1    Dublin (Ireland)
  eu-central-1 Frankfurt (Germany)  ← recommended for German data residency
  eu-north-1   Stockholm (Sweden)

Credential resolution order (standard boto3 chain):
  1. Explicit env vars  AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
  2. ~/.aws/credentials profile
  3. IAM instance profile / ECS task role / EKS IRSA  (recommended for production)
  4. AWS SSO / Identity Center  (aws sso login --profile <name>)

Docs:
  AWS Bedrock overview            → https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html
  Anthropic Claude on Bedrock     → https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic.html
  Supported model IDs             → https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html
  Enable model access             → https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html
  boto3 sessions                  → https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html
  anthropic[bedrock] SDK          → https://github.com/anthropics/anthropic-sdk-python#aws-bedrock

Prerequisite:
    Enable model access in the AWS Console for the target EU region.
    https://console.aws.amazon.com/bedrock/home#/modelaccess

Usage:
    uv run python providers/bedrock_claude_provider.py
"""

import os
from dotenv import load_dotenv
import boto3
from anthropic import AnthropicBedrock
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console()


def build_client() -> AnthropicBedrock:
    """
    Return an AnthropicBedrock client backed by a boto3 session.

    A boto3 Session resolves credentials through the full AWS credential chain
    (env vars → ~/.aws/credentials → IAM role → ECS task role → IRSA → SSO),
    so this works identically in local dev, CI, and production without code changes.
    Resolved credentials are forwarded to AnthropicBedrock via botocore.
    """
    region = os.environ.get("AWS_REGION", "eu-central-1")

    session = boto3.Session(region_name=region)
    credentials = session.get_credentials().get_frozen_credentials()

    return AnthropicBedrock(
        aws_access_key=credentials.access_key,
        aws_secret_key=credentials.secret_key,
        aws_session_token=credentials.token,   # populated for temporary creds (roles, SSO)
        aws_region=region,
    )


def chat_stream(client: AnthropicBedrock, prompt: str, model_id: str) -> dict:
    """
    Stream a Claude chat completion via Bedrock and return token usage.
    Returns: {"response_text": str, "prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    """
    region = os.environ.get("AWS_REGION", "eu-central-1")
    console.print(Panel(f"[bold yellow]AWS Bedrock Claude[/] → {model_id}  (region: {region})", expand=False))
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
    _print_usage_table(usage, "AWS Bedrock Claude", model_id)
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
    model_id = os.environ.get("BEDROCK_CLAUDE_MODEL", "anthropic.claude-sonnet-4-5-20251001-v1:0")
    prompt = "Explain the GDPR Article 46 transfer mechanisms in two sentences."
    chat_stream(client, prompt, model_id)
