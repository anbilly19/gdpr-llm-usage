"""
LLMHarness  —  Drop-in harness for integrating the LangGraph router into any codebase
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

ProviderName = Literal[
    "azure", "vertex_gemini", "vertex_claude", "bedrock_claude", "self_hosted", "all"
]


@dataclass
class HarnessResult:
    provider: str
    response_text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    raw: dict = field(default_factory=dict)

    @property
    def usage(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


class LLMHarness:
    def __init__(self, provider: ProviderName = "vertex_gemini", show_dashboard: bool = False):
        self.provider = provider
        self.show_dashboard = show_dashboard
        self._graph = None

    def _get_graph(self):
        if self._graph is None:
            from langgraph_router.router import build_graph
            self._graph = build_graph().compile()
        return self._graph

    def _invoke(self, prompt: str, provider: ProviderName) -> dict:
        graph = self._get_graph()
        return graph.invoke({
            "prompt": prompt,
            "provider": provider,
            "usage_records": [],
            "responses": [],
        })

    @staticmethod
    def _state_to_results(final_state: dict) -> list[HarnessResult]:
        results: list[HarnessResult] = []
        usage_map = {rec["provider"]: rec for rec in final_state.get("usage_records", [])}

        for resp in final_state.get("responses", []):
            provider_key = resp["provider"]
            usage = usage_map.get(
                next((k for k in usage_map if provider_key in k.lower().replace(" ", "_").replace("-", "_")), provider_key),
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

    def run(self, prompt: str) -> HarnessResult:
        final_state = self._invoke(prompt, self.provider)
        results = self._state_to_results(final_state)
        if self.show_dashboard:
            self.print_dashboard(results)
        return results[0] if results else HarnessResult(provider=self.provider, response_text="")

    def run_all(self, prompt: str) -> list[HarnessResult]:
        final_state = self._invoke(prompt, "all")
        results = self._state_to_results(final_state)
        if self.show_dashboard:
            self.print_dashboard(results)
        return results

    @staticmethod
    def print_dashboard(results: list[HarnessResult]) -> None:
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
