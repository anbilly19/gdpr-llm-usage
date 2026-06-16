# gdpr-llm-usage

> EU/GDPR-compliant LLM provider patterns for Azure-native applications.
> Every provider script is standalone — drop it straight into your codebase.

---

## Table of Contents

- [Overview](#overview)
- [EU Compliance Matrix](#eu-compliance-matrix)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Provider Setup](#provider-setup)
- [LangGraph Router](#langgraph-router)
- [Running Tests](#running-tests)
- [Related Projects](#related-projects)
- [Startup Cost Reference](./STARTUP_CLOUD_COSTS.md)
- [Free & Trial API Access](./FREE_TRIALS.md)
- [Provider Deep-dive](./PROVIDERS.md)

---

## Overview

When your primary stack lives in **Azure** (EU region), you have two routing situations:

| Situation | Description |
|-----------|-------------|
| **HOME** | Azure OpenAI (GPT-4o) or self-hosted open-source models. Full EU Data Boundary or zero egress. |
| **AWAY** | Cross-cloud to Google Vertex AI or AWS Bedrock — required for Anthropic Claude with EU residency today, since Azure Foundry Claude EU support is still roadmap. |

---

## EU Compliance Matrix

| Provider | Model | EU Residency | Status |
|----------|-------|-------------|--------|
| Azure OpenAI | GPT-4o | ✅ Full | GA — use `germanywestcentral`, `westeurope` |
| Azure AI Foundry | Claude | ❌ Not yet | Roadmap 2026 — runs on Anthropic infra |
| Google Vertex AI | Gemini 2.5 Flash | ✅ Full | GA — `GOOGLE_CLOUD_LOCATION=eu` |
| Google Vertex AI | Claude Sonnet | ✅ Full | Preview — EU multi-region endpoint |
| AWS Bedrock | Claude Sonnet | ✅ Full | GA — `eu-central-1` / `eu-west-1` |
| Self-hosted (vLLM/Ollama) | Any open model | ✅ Full | Self-managed — zero egress |

---

## Quick Start

```bash
git clone https://github.com/anbilly19/gdpr-llm-usage.git
cd gdpr-llm-usage
uv sync
cp .env.example .env  # fill in credentials
```

**Run a single provider:**
```bash
uv run python providers/azure_openai_provider.py
uv run python providers/vertex_gemini_provider.py
uv run python providers/vertex_claude_provider.py
uv run python providers/bedrock_claude_provider.py
uv run python providers/self_hosted_vllm_provider.py
```

**Run all providers via router:**
```bash
uv run python run_all.py
uv run python run_all.py --provider vertex_claude
uv run python run_all.py --prompt "Summarise GDPR Article 28."
```

**Use the harness in your own code:**
```python
from langgraph_router.harness import LLMHarness

harness = LLMHarness(provider="vertex_claude")
result = harness.run("Your prompt")
print(result.response_text, result.usage)
```

---

## Project Structure

```
gdpr-llm-usage/
├── providers/
│   ├── azure_openai_provider.py       # HOME: Azure OpenAI GPT-4o
│   ├── vertex_gemini_provider.py      # AWAY: Vertex AI Gemini, EU multi-region
│   ├── vertex_claude_provider.py      # AWAY: Vertex AI Claude, EU multi-region
│   ├── bedrock_claude_provider.py     # AWAY: AWS Bedrock Claude, EU regions
│   └── self_hosted_vllm_provider.py   # HOME: vLLM / Ollama, zero egress
├── langgraph_router/
│   ├── router.py                      # LangGraph fan-out across all 5 providers
│   └── harness.py                     # Drop-in harness class
├── token_dashboard/
│   └── dashboard.py                   # Unified Rich token usage table
├── tests/
│   ├── test_providers.py
│   └── test_router.py
├── run_all.py
├── PROVIDERS.md                       # Region/model/pricing deep-dive
├── STARTUP_CLOUD_COSTS.md             # Cloud credit programs & cost breakdown
└── FREE_TRIALS.md                     # Free-tier & trial access per provider
```

---

## Provider Setup

### 1. Azure OpenAI (HOME)

```bash
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

Docs: [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/) · [EU Data Boundary](https://learn.microsoft.com/en-us/privacy/eudb/eu-data-boundary-learn)

---

### 2. Google Vertex AI — Gemini (AWAY)

```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project
GOOGLE_CLOUD_LOCATION=eu              # EU multi-region
GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
VERTEX_GEMINI_MODEL=gemini-2.5-flash-001
```

Docs: [Gemini on Vertex](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/overview) · [EU locations](https://cloud.google.com/vertex-ai/docs/general/locations#europe) · [google-genai SDK](https://googleapis.github.io/python-genai/)

---

### 3. Google Vertex AI — Claude (AWAY)

> Recommended path for Anthropic Claude with EU residency today.

```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project
GOOGLE_CLOUD_LOCATION=eu
GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
VERTEX_CLAUDE_MODEL=claude-sonnet-4-5@20251001
```

Docs: [Claude on Vertex](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude) · [EU multi-region for Claude](https://cloud.google.com/blog/products/ai-machine-learning/multi-region-endpoints-for-claude-available-on-vertex-ai)

---

### 4. AWS Bedrock — Claude (AWAY)

```bash
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=eu-central-1              # Frankfurt
BEDROCK_CLAUDE_MODEL=anthropic.claude-sonnet-4-5-20251001-v1:0
```

> Enable Anthropic model access in the [AWS Console](https://console.aws.amazon.com/bedrock/home#/modelaccess) per EU region before use.

Docs: [Claude on Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic.html) · [anthropic[bedrock] SDK](https://github.com/anthropics/anthropic-sdk-python#aws-bedrock)

---

### 5. Self-hosted vLLM / Ollama (HOME)

```bash
SELF_HOSTED_BASE_URL=http://localhost:8000/v1
SELF_HOSTED_API_KEY=local-dev-key
SELF_HOSTED_MODEL=qwen3-32b
```

```bash
# vLLM
vllm serve Qwen/Qwen3-32B --host 0.0.0.0 --port 8000 --served-model-name qwen3-32b

# Ollama
ollama serve  # default port 11434
```

Docs: [vLLM](https://docs.vllm.ai/) · [Ollama](https://ollama.com/docs)

---

## LangGraph Router

`langgraph_router/router.py` fans out a prompt to one or all five providers via a conditional LangGraph graph. Provider nodes are thin wrappers — all logic lives in the standalone provider modules.

Docs: [LangGraph concepts](https://langchain-ai.github.io/langgraph/concepts/) · [Parallel nodes](https://langchain-ai.github.io/langgraph/how-tos/map-reduce/)

---

## Running Tests

All tests use `unittest.mock` — no real API calls or credentials needed.

```bash
uv run pytest
uv run pytest -v
```

---

## Related Projects

| Project | What it is |
|---------|------------|
| [LiteLLM](https://github.com/BerriAI/litellm) | Unified SDK + proxy over 100+ providers. Best for production gateway scale. |
| [AWS Multi-Provider GenAI Gateway](https://github.com/aws-solutions-library-samples/guidance-for-multi-provider-generative-ai-gateway-on-aws) | AWS-anchored multi-provider routing via API Gateway + Lambda (Terraform). |
| [EdgeQuake LLM](https://github.com/raphaelmansuy/edgequake-llm) | Rust-native typed provider abstraction, 17 providers. |
| [Anthropic Claude EU residency issue](https://github.com/anthropics/claude-code/issues/40530) | Active tracking issue for upstream EU data residency on Azure Foundry. |
