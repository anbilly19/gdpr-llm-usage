"""
LLMHarness  —  Drop-in harness for integrating the LangGraph router into any codebase
===============================================================================
This module provides a clean, typed interface over the LangGraph router so that
you can embed EU-compliant LLM calls into any existing project with minimal
adaptation.

Design goals:
  - Zero coupling to internal graph structure  —  callers only see HarnessResult
  - Works identically for a single provider or all providers at once
  - Token usage is always surfaced, never silently dropped
  - Prints the unified dashboard optionally (off by default for library use)

Usage example:

    from langgraph_router.harness import LLMHarness

    # Single provider
    harness = LLMHarness(provider="vertex_gemini")
    result = harness.run("Summarise GDPR Article 28 in two sentences.")
    print(result.response_text)
    print(result.usage)

    # All providers — returns list of HarnessResult, one per provider
    harness = LLMHarness(provider="all")
    results = harness.run_all("Summarise GDPR Article 28 in two sentences.")
    for r in results:
        print(r.provider, r.total_tokens)

    # Print unified dashboard
    harness.print_dashboard(results)

Docs:
  LangGraph how-tos   → https://langchain-ai.github.io/langgraph/how-tos/
  LangGraph concepts  → https://langchain-ai.github.io/langgraph/concepts/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

ProviderName = Literal["azure", "vertex_gemini", "vertex_claude", "bedrock_claude", "all"]


@dataclass
class HarnessResult:
    """
    Typed result returned by LLMHarness.run() and LLMHarness.run_all().

    Attributes:
        provider:           Which provider generated this result.
        response_text:      Full streamed text response.
        prompt_tokens:      Tokens consumed by the input prompt.
        completion_tokens:  Tokens consumed by the model output.
        total_tokens:       Sum of prompt + completion tokens.
        usage:              Dict representation for easy serialisation.
    """
    provider: str
    response_text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    raw: dict = field(default_factory=dict)  # full usage_record from router

    @property
    def usage(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


class LLMHarness:
    """
    Provider-agnostic harness for EU-compliant LLM inference.

    This class wraps the LangGraph router and exposes a clean interface
    suitable for embedding in any service, script, or agent pipeline.

    Parameters
    ----------
    provider : ProviderName
        Which provider(s) to call.
        One of: 'azure', 'vertex_gemini', 'vertex_claude', 'bedrock_claude', 'all'
    show_dashboard : bool
        If True, print the Rich token-usage dashboard after each run.
        Default False (library-friendly).
    """

    def __init__(self, provider: ProviderName = "vertex_gemini", show_dashboard: bool = False):
        self.provider = provider
        self.show_dashboard = show_dashboard
        self._graph = None  # lazy-compiled

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _get_graph(self):
        """Lazy-compile the LangGraph graph (once per harness instance)."""
        if self._graph is None:
            from langgraph_router.router import build_graph
            self._graph = build_graph().compile()
        return self._graph

    def _invoke(self, prompt: str, provider: ProviderName) -> dict:
        """Invoke the compiled graph and return raw final state."""
        graph = self._get_graph()
        return graph.invoke({
            "prompt": prompt,
            "provider": provider,
            "usage_records": [],
            "responses": [],
        })

    @staticmethod
    def _state_to_results(final_state: dict) -> list[HarnessResult]:
        """Convert raw graph state into a list of HarnessResult objects."""
        results: list[HarnessResult] = []
        usage_map = {rec["provider"]: rec for rec in final_state.get("usage_records", [])}

        for resp in final_state.get("responses", []):
            provider_key = resp["provider"]
            usage = usage_map.get(
                # router stores provider display name in usage_records, key in responses
                # normalise by matching on partial key
                next((k for k in usage_map if provider_key in k.lower().replace(" ", "_")), provider_key),
                {},
            )
            results.append(HarnessResult(
                provider=provider_key,
                response_text=resp.get("text", ""),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                raw=usage,
            ))
        return results

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def run(self, prompt: str) -> HarnessResult:
        """
        Run a single prompt against the configured provider.

        If provider='all', this returns only the first result.
        Use run_all() when you want results from every provider.

        Parameters
        ----------
        prompt : str  The prompt to send.

        Returns
        -------
        HarnessResult
        """
        final_state = self._invoke(prompt, self.provider)
        results = self._state_to_results(final_state)
        if self.show_dashboard:
            self.print_dashboard(results)
        return results[0] if results else HarnessResult(provider=self.provider, response_text="")

    def run_all(self, prompt: str) -> list[HarnessResult]:
        """
        Fan out the prompt to every provider and collect all results.

        Temporarily overrides self.provider to 'all' for this call.

        Parameters
        ----------
        prompt : str  The prompt to send.

        Returns
        -------
        list[HarnessResult]  One entry per provider.
        """
        final_state = self._invoke(prompt, "all")
        results = self._state_to_results(final_state)
        if self.show_dashboard:
            self.print_dashboard(results)
        return results

    @staticmethod
    def print_dashboard(results: list[HarnessResult]) -> None:
        """
        Print the unified Rich token-usage dashboard for a list of results.

        Parameters
        ----------
        results : list[HarnessResult]
        """
        from token_dashboard.dashboard import print_dashboard
        records = [
            {
                "provider": r.provider,
                "model": r.raw.get("model", "unknown"),
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
            }
            for r in results
        ]
        print_dashboard(records)


# ------------------------------------------------------------------ #
# Quick demo when run directly
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    import os

    provider: ProviderName = os.environ.get("PROVIDER", "vertex_gemini")  # type: ignore
    harness = LLMHarness(provider=provider, show_dashboard=True)

    prompt = "Explain the GDPR Article 46 transfer mechanisms in two sentences."

    if provider == "all":
        results = harness.run_all(prompt)
        print(f"\nGot {len(results)} results.")
    else:
        result = harness.run(prompt)
        print(f"\nProvider : {result.provider}")
        print(f"Tokens   : {result.total_tokens}")
        print(f"Response : {result.response_text[:200]}...")
