"""
run_all.py  —  Compare all four providers side-by-side
===============================================================================
Invokes the LangGraph router with provider='all', which fans out to every
configured provider in sequence and then renders the unified token dashboard.

Make sure all credentials are set in .env before running.

Usage:
    uv run python run_all.py
    uv run python run_all.py --prompt "Your custom question here"
"""

import argparse
from dotenv import load_dotenv
from langgraph_router.router import build_graph
from token_dashboard.dashboard import print_dashboard
from rich.console import Console

load_dotenv()
console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all EU LLM providers and compare token usage.")
    parser.add_argument(
        "--prompt",
        default="Explain the GDPR Article 46 transfer mechanisms in two sentences.",
        help="The prompt to send to all providers.",
    )
    parser.add_argument(
        "--provider",
        default="all",
        choices=["all", "azure", "vertex_gemini", "vertex_claude", "bedrock_claude"],
        help="Which provider(s) to invoke (default: all).",
    )
    args = parser.parse_args()

    graph = build_graph().compile()
    console.rule(f"[bold]Sending prompt to: [cyan]{args.provider}[/][/]")
    console.print(f"[dim]Prompt: {args.prompt}[/]\n")

    final_state = graph.invoke({
        "prompt": args.prompt,
        "provider": args.provider,
        "usage_records": [],
        "responses": [],
    })

    print_dashboard(final_state["usage_records"])


if __name__ == "__main__":
    main()
