# gdpr-llm-usage

> Research project: EU/GDPR-compliant LLM provider patterns for Azure-native applications.
> Every script is **standalone and self-contained** — drop any provider module straight into your codebase.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [EU Compliance Matrix](#eu-compliance-matrix)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Provider Setup](#provider-setup)
  - [Azure OpenAI (HOME)](#1-azure-openai-home)
  - [Vertex AI — Gemini (AWAY)](#2-google-vertex-ai--gemini-away)
  - [Vertex AI — Claude (AWAY)](#3-google-vertex-ai--claude-away)
  - [AWS Bedrock — Claude (AWAY)](#4-aws-bedrock--claude-away)
- [LangGraph Router](#langgraph-router)
- [Reusable Harness](#reusable-harness)
- [Unified Token Dashboard](#unified-token-dashboard)
- [Running Tests](#running-tests)
- [Related Projects](#related-projects)
- [Free & Trial API Access](./FREE_TRIALS.md)
- [Key Documentation Links](#key-documentation-links)

---

## Overview

When your primary stack lives in **Azure** (EU region), you have two routing situations:

| Situation | Description |
|-----------|-------------|
| **HOME** | Azure-native models (Azure OpenAI GPT-4o). Full EU Data Boundary compliance. |
| **AWAY** | Cross-cloud to Google Vertex AI or AWS Bedrock for models not yet EU-native on Azure (e.g. Anthropic Claude via Azure Foundry is roadmap, not yet available in EU as of 2026). |

This project shows exactly how to wire up all four options with a unified interface so you can switch or combine providers without touching business logic.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Azure Application                    │
│                  (stays in Azure EU region)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                 ┌──────────▼──────────┐
                 │   LangGraph Router   │
                 │  (langgraph_router/) │
                 └──────────┬──────────┘
          ┌─────────────────┼──────────────────┐
          │                 │                  │
  ┌───────▼──────┐  ┌───────▼──────┐  ┌───────▼──────────────┐
  │  HOME        │  │  AWAY        │  │  AWAY                 │
  │  Azure       │  │  Google      │  │  AWS Bedrock          │
  │  OpenAI      │  │  Vertex AI   │  │  Claude               │
  │  (EU region) │  │  Gemini/     │  │  (eu-central-1 etc.)  │
  │              │  │  Claude      │  │                       │
  │  EU Data     │  │  (EU multi-  │  │  Frankfurt / Dublin   │
  │  Boundary ✓  │  │  region) ✓   │  │  / Stockholm ✓        │
  └──────────────┘  └──────────────┘  └───────────────────────┘
          │                 │                  │
          └─────────────────▼──────────────────┘
                 ┌──────────────────────┐
                 │  Unified Token       │
                 │  Dashboard (Rich)    │
                 └──────────────────────┘
```

---

## EU Compliance Matrix

| Provider | Model | EU Data Residency | Status | Notes |
|----------|-------|-------------------|--------|-------|
| Azure OpenAI | GPT-4o, GPT-4 | ✅ Full | GA | Set region to `westeurope`, `germanywestcentral`, `francecentral` |
| Azure AI Foundry | Claude (Anthropic) | ❌ Not yet | Roadmap 2026 | Runs on Anthropic infra, outside EU Data Boundary |
| Google Vertex AI | Gemini 2.5 Flash | ✅ Full | GA | Use `GOOGLE_CLOUD_LOCATION=eu` or `europe-west4` |
| Google Vertex AI | Claude Sonnet | ✅ Full | Preview | EU multi-region endpoint; data stays within EU |
| AWS Bedrock | Claude Sonnet | ✅ Full | GA | Use `eu-central-1` (Frankfurt) or `eu-west-1` (Dublin) |

---

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) installed (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Install

```bash
git clone https://github.com/anbilly19/gdpr-llm-usage.git
cd gdpr-llm-usage
uv sync
```

### Configure

```bash
cp .env.example .env
# Edit .env with your credentials for the provider(s) you want to use
```

### Run a single provider

```bash
# Azure OpenAI (HOME)
uv run python providers/azure_openai_provider.py

# Vertex Gemini (AWAY — EU)
uv run python providers/vertex_gemini_provider.py

# Vertex Claude (AWAY — EU)
uv run python providers/vertex_claude_provider.py

# AWS Bedrock Claude (AWAY — EU)
uv run python providers/bedrock_claude_provider.py
```

### Run all providers via LangGraph router

```bash
# All providers, default GDPR prompt
uv run python run_all.py

# Single provider
uv run python run_all.py --provider vertex_gemini

# Custom prompt
uv run python run_all.py --prompt "Summarise GDPR Article 28 processor obligations."

# Via environment variable (useful in CI)
PROVIDER=bedrock_claude uv run python langgraph_router/router.py
```

### Embed in your own codebase via the harness

```python
from langgraph_router.harness import LLMHarness

harness = LLMHarness(provider="vertex_gemini")  # or 'azure', 'vertex_claude', 'bedrock_claude', 'all'
result = harness.run("Your prompt here")
print(result.response_text)
print(result.usage)  # {prompt_tokens, completion_tokens, total_tokens}
```

---

## Project Structure

```
gdpr-llm-usage/
├── providers/                        # Standalone provider scripts (one per LLM backend)
│   ├── azure_openai_provider.py      # HOME: Azure OpenAI GPT-4o, EU Data Boundary
│   ├── vertex_gemini_provider.py     # AWAY: Vertex AI Gemini, EU multi-region (google-genai SDK)
│   ├── vertex_claude_provider.py     # AWAY: Vertex AI Claude, EU multi-region
│   └── bedrock_claude_provider.py    # AWAY: AWS Bedrock Claude, EU regions
├── langgraph_router/
│   ├── router.py                     # LangGraph graph: fan-out routing across providers
│   └── harness.py                    # Drop-in harness class for integrating into any codebase
├── token_dashboard/
│   └── dashboard.py                  # Unified Rich token usage table (all providers)
├── tests/
│   ├── test_providers.py             # Unit tests for provider modules (mocked)
│   └── test_router.py                # Unit tests for LangGraph router (mocked)
├── run_all.py                        # CLI: run one or all providers and show dashboard
├── pyproject.toml                    # uv-managed dependencies
├── .env.example                      # Credential template
└── PROVIDERS.md                      # Deep-dive reference: regions, model IDs, pricing links
```

---

## Provider Setup

### 1. Azure OpenAI (HOME)

**EU Data Boundary compliant** — data never leaves Microsoft's EU data centers.

```bash
# In .env:
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

**EU regions to use:** `germanywestcentral`, `westeurope`, `francecentral`, `swedencentral`

Docs: [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/) · [EU Data Boundary](https://learn.microsoft.com/en-us/privacy/eudb/eu-data-boundary-learn) · [openai-python SDK](https://github.com/openai/openai-python)

---

### 2. Google Vertex AI — Gemini (AWAY)

Uses the **new `google-genai` SDK** (`pip install google-genai`). The old `vertexai.generative_models` path is deprecated as of mid-2026.

```bash
# In .env:
GOOGLE_CLOUD_PROJECT=your-gcp-project
GOOGLE_CLOUD_LOCATION=eu              # EU multi-region (recommended)
# GOOGLE_CLOUD_LOCATION=europe-west4  # Netherlands single-region (strictest)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_GEMINI_MODEL=gemini-2.5-flash-001
```

**Auth alternatives:**
```bash
# Keyless (local dev)
gcloud auth application-default login

# Service account (CI/production)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
```

Docs: [Vertex AI overview](https://cloud.google.com/vertex-ai/docs/start/introduction-unified-platform) · [Gemini on Vertex](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/overview) · [EU locations](https://cloud.google.com/vertex-ai/docs/general/locations#europe) · [google-genai SDK](https://googleapis.github.io/python-genai/)

---

### 3. Google Vertex AI — Claude (AWAY)

This is the **recommended path for Anthropic Claude with EU data residency** today, since Azure Foundry EU Claude support is still roadmap.

```bash
# In .env (same GCP credentials as Gemini):
GOOGLE_CLOUD_PROJECT=your-gcp-project
GOOGLE_CLOUD_LOCATION=eu
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_CLAUDE_MODEL=claude-sonnet-4-5@20251001
```

Docs: [Claude on Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude) · [EU multi-region for Claude](https://cloud.google.com/blog/products/ai-machine-learning/multi-region-endpoints-for-claude-available-on-vertex-ai) · [anthropic[vertex] SDK](https://github.com/anthropics/anthropic-sdk-python#vertex-ai)

---

### 4. AWS Bedrock — Claude (AWAY)

Alternative Anthropic EU path if your organisation already uses AWS.

```bash
# In .env:
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=eu-central-1              # Frankfurt — recommended for German data residency
# AWS_REGION=eu-west-1               # Dublin
# AWS_REGION=eu-north-1              # Stockholm
BEDROCK_CLAUDE_MODEL=anthropic.claude-sonnet-4-5-20251001-v1:0
```

> **Important:** You must manually enable Anthropic model access in the [AWS Console](https://console.aws.amazon.com/bedrock/home#/modelaccess) for each EU region you intend to use.

Docs: [AWS Bedrock overview](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html) · [Claude on Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic.html) · [Supported model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html) · [anthropic[bedrock] SDK](https://github.com/anthropics/anthropic-sdk-python#aws-bedrock)

---

## LangGraph Router

`langgraph_router/router.py` implements a **fan-out LangGraph graph** that can route a single prompt to one or all providers and collect unified token usage.

```
[START]
   │
[route]   ← conditional edge based on GraphState.provider
   ├── azure          → node_azure
   ├── vertex_gemini  → node_vertex_gemini
   ├── vertex_claude  → node_vertex_claude
   └── bedrock_claude → node_bedrock_claude
        │ (all converge via Annotated reducer)
     [END]
```

Key design choices:
- Each **provider node** is a thin wrapper — all LLM logic lives in the standalone provider modules
- `usage_records` and `responses` use **LangGraph Annotated reducers** to safely accumulate across parallel branches
- `PROVIDER=all` fans out to all four providers (LangGraph handles concurrency)

Docs: [LangGraph concepts](https://langchain-ai.github.io/langgraph/concepts/) · [Conditional edges](https://langchain-ai.github.io/langgraph/how-tos/branching/) · [Parallel nodes](https://langchain-ai.github.io/langgraph/how-tos/map-reduce/)

---

## Reusable Harness

`langgraph_router/harness.py` provides a **drop-in class** for embedding the router into any existing codebase:

```python
from langgraph_router.harness import LLMHarness, HarnessResult

# Single provider
harness = LLMHarness(provider="vertex_gemini")
result: HarnessResult = harness.run("Your prompt")
print(result.response_text)
print(result.usage)   # dict: prompt_tokens, completion_tokens, total_tokens

# All providers — returns list of HarnessResult
harness = LLMHarness(provider="all")
results = harness.run_all("Your prompt")
for r in results:
    print(r.provider, r.total_tokens)

# Print unified dashboard for a run
harness.print_dashboard(results)
```

---

## Unified Token Dashboard

After every run (standalone or via router), a Rich terminal table shows token usage across all invoked providers:

```
╭──────────────────────────────────────────────────────────────────────╮
│              Token Usage Across Providers                            │
├─────────────────┬───────────────────────────┬───────┬──────────┬─────┤
│ Provider        │ Model                     │ Prmpt │ Compltn  │ Tot │
├─────────────────┼───────────────────────────┼───────┼──────────┼─────┤
│ Azure OpenAI    │ gpt-4o                    │   42  │    89    │ 131 │
│ Vertex Gemini   │ gemini-2.5-flash-001      │   38  │    74    │ 112 │
│ Vertex Claude   │ claude-sonnet-4-5@2025... │   41  │    96    │ 137 │
│ Bedrock Claude  │ anthropic.claude-sonnet.. │   41  │    91    │ 132 │
├─────────────────┼───────────────────────────┼───────┼──────────┼─────┤
│ TOTAL           │                           │  162  │   350    │ 512 │
╰──────────────────────────────────────────────────────────────────────╯
  Most token-efficient: Vertex Gemini (112 total tokens)
```

---

## Running Tests

Tests use `unittest.mock` to patch all LLM clients — no real API calls or credentials needed.

```bash
# Run all tests
uv run pytest

# Verbose output
uv run pytest -v

# Single test file
uv run pytest tests/test_providers.py -v
```

---

## Related Projects

This section maps the broader ecosystem to help you understand where `gdpr-llm-usage` fits and what to reach for when you need something different.

### LLM abstraction & unified gateways

| Project | Description | How it differs from this repo |
|---------|-------------|-------------------------------|
| [**LiteLLM**](https://github.com/BerriAI/litellm) ⭐ 20k+ | Open-source Python SDK + proxy server. Single OpenAI-compatible API over 100+ providers (Azure, Vertex, Bedrock, Anthropic, etc.). Includes cost tracking, rate limiting, caching. | Broader (100+ providers, full proxy infra). Not opinionated on EU routing or Azure-as-home. Best if you need production gateway scale. |
| [**EdgeQuake LLM**](https://github.com/raphaelmansuy/edgequake-llm) | Rust crate providing strongly-typed trait-based abstraction over 17 providers (cloud APIs, local inference, gateways). Includes token counting, rate limiting, response caching. | Rust-native, performance-focused, no EU/GDPR angle. Good reference for a typed provider abstraction in systems work. |
| [**ArchGW**](https://github.com/katanemo/archgw) | Lightweight AI API gateway / proxy. Plans for Azure OpenAI, Bedrock, Anthropic, Cohere support. | Infrastructure-heavy (proxy layer), not a Python library. |

### Multi-provider routing samples

| Project | Description | How it differs |
|---------|-------------|----------------|
| [**AWS Guidance for Multi-Provider GenAI Gateway**](https://github.com/aws-solutions-library-samples/guidance-for-multi-provider-generative-ai-gateway-on-aws) ⭐ 226 | Official AWS Solutions Library sample. Unified OpenAI-compatible endpoint routing to Bedrock, OpenAI, Azure OpenAI via API Gateway + Lambda. Infra-as-code (HCL/Terraform). | AWS-centric infra view (not Azure-as-home). No EU/GDPR data-residency angle. Terraform/HCL rather than Python. |
| [**aws-samples/sample-agent-interoperability**](https://github.com/aws-samples/sample-agent-interoperability) | Multi-cloud agent interoperability: Google ADK + Bedrock AgentCore exposed via A2A protocol. | Agent-level interop focus, not LLM-routing or token tracking. |

### Real-world GDPR-compliant multi-cloud LLM architecture

| Project / Resource | Description |
|--------------------|-------------|
| [**CompanyGPT (innFactory)**](https://innfactory.de/en/references/companygpt/) | Enterprise GDPR-compliant AI assistant built on Azure + Vertex AI + Bedrock. Routes: Claude → Bedrock EU Frankfurt, GPT → Azure OpenAI EU Sweden/Germany, Gemini → Vertex EU europe-west3. Closest real-world architecture to this repo. Described as a product/reference, not open-source code. |
| [**Anthropic Claude EU data residency issue (claude-code #40530)**](https://github.com/anthropics/claude-code/issues/40530) | Active Anthropic GitHub issue tracking the request for EU data residency support via hyperscaler backends (exactly the problem this repo solves). Useful to watch for upstream progress. |
| [**Azure AI Foundry Claude EU timeline (MS Q&A)**](https://learn.microsoft.com/en-us/answers/questions/5867930/timeline-for-claude-in-microsoft-foundry-to-run-on) | Microsoft community thread tracking when Azure-native Claude EU hosting will arrive. Once resolved, the `azure` provider in this repo can be extended to use Claude directly via Foundry. |

### When to use what

```
Need production-grade proxy with 100+ providers?  → LiteLLM
Need Rust-native strongly-typed provider traits?   → EdgeQuake LLM
Need AWS-anchored multi-provider routing (IaC)?   → AWS Multi-Provider Gateway guidance
Need EU/GDPR-pinned routing with Azure as home,
  LangGraph orchestration, and Python harness?    → this repo ✓
```

---

## Key Documentation Links

| Service | Link |
|---------|------|
| Azure OpenAI Service | https://learn.microsoft.com/en-us/azure/ai-services/openai/ |
| Azure EU Data Boundary | https://learn.microsoft.com/en-us/privacy/eudb/eu-data-boundary-learn |
| Azure AI Foundry (Claude roadmap) | https://learn.microsoft.com/en-us/answers/questions/5867930/timeline-for-claude-in-microsoft-foundry-to-run-on |
| Google Vertex AI overview | https://cloud.google.com/vertex-ai/docs/start/introduction-unified-platform |
| Vertex AI EU locations | https://cloud.google.com/vertex-ai/docs/general/locations#europe |
| Claude EU multi-region on Vertex | https://cloud.google.com/blog/products/ai-machine-learning/multi-region-endpoints-for-claude-available-on-vertex-ai |
| Gemini model IDs | https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versioning |
| Claude on Vertex AI | https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude |
| AWS Bedrock overview | https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html |
| Claude on Bedrock | https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic.html |
| Bedrock EU model access | https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html |
| LangGraph concepts | https://langchain-ai.github.io/langgraph/concepts/ |
| LangGraph how-to guides | https://langchain-ai.github.io/langgraph/how-tos/ |
| uv documentation | https://docs.astral.sh/uv/ |
| openai-python SDK | https://github.com/openai/openai-python |
| anthropic-sdk-python | https://github.com/anthropics/anthropic-sdk-python |
| google-genai SDK | https://googleapis.github.io/python-genai/ |
| boto3 Bedrock runtime | https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime.html |
