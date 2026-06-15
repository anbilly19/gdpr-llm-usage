# Provider Reference Card

Deep-dive reference for all five EU-compliant LLM providers covered in this project.
Use this alongside the standalone scripts in `providers/` and the `.env.example` file.

---

## 1. Azure OpenAI — HOME

> **Status:** GA, EU Data Boundary compliant

### When to use

- Your application is already Azure-native and you need GPT-4o or GPT-4 with a contractual guarantee that data never leaves EU Microsoft data centers.
- You require Microsoft's Data Processing Agreement (DPA) and EU Data Boundary commitment.

### EU regions

| Region code | Location |
|-------------|----------|
| `germanywestcentral` | Frankfurt, Germany ★ recommended |
| `westeurope` | Netherlands |
| `francecentral` | Paris, France |
| `swedencentral` | Gävle, Sweden |
| `norwayeast` | Oslo, Norway |

### Key env vars

```bash
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

### Available models (EU regions, June 2026)

| Model | Deployment type | Notes |
|-------|----------------|-------|
| `gpt-4o` | Standard / Global-Standard | Recommended |
| `gpt-4o-mini` | Standard | Cost-optimised |
| `gpt-4` | Standard | Legacy |
| `o3` | Standard | Reasoning model |
| `o4-mini` | Standard | Fast reasoning |
| `text-embedding-3-large` | Standard | Embeddings |

### Important notes

- **Azure AI Foundry + Claude:** As of June 2026, Anthropic Claude via Azure Foundry runs on Anthropic-managed infrastructure. It is **not** within the Azure EU Data Boundary. Microsoft lists EU Azure Foundry Claude support as "coming 2026" — check [this thread](https://learn.microsoft.com/en-us/answers/questions/5867930/timeline-for-claude-in-microsoft-foundry-to-run-on) for updates.
- For EU-compliant Claude today, use Vertex AI or AWS Bedrock (see below).

### Documentation

- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [EU Data Boundary](https://learn.microsoft.com/en-us/privacy/eudb/eu-data-boundary-learn)
- [Supported regions and models](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)
- [openai-python SDK](https://github.com/openai/openai-python)
- [Azure OpenAI API reference](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference)

---

## 2. Google Vertex AI — Gemini (AWAY)

> **Status:** GA, EU multi-region and single-region available

### When to use

- You need a frontier multimodal model (Gemini 2.5 Flash / Pro) with EU data residency.
- You want EU-hosted Gemini as a complement or fallback to Azure OpenAI.
- Cost-sensitive: Gemini Flash offers excellent price/performance.

### EU location options

| `GOOGLE_CLOUD_LOCATION` | Description | Use case |
|------------------------|-------------|----------|
| `eu` | EU multi-region (pools `europe-west1` + `europe-west4`) | Best availability, EU data boundary |
| `europe-west4` | Netherlands (single region) | Strictest single-country residency |
| `europe-west3` | Frankfurt, Germany | German data residency (partial model coverage) |
| `europe-west1` | Belgium | Single region |

### Key env vars

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=eu
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_GEMINI_MODEL=gemini-2.5-flash-001
```

### Available Gemini models on Vertex AI (June 2026)

| Model ID | Type | EU multi-region | Notes |
|----------|------|-----------------|-------|
| `gemini-2.5-flash-001` | Multimodal | ✅ GA | Best price/performance |
| `gemini-2.5-pro-001` | Multimodal | ✅ GA | Highest capability |
| `gemini-2.0-flash-001` | Multimodal | ✅ GA | Previous gen |
| `gemini-1.5-pro-002` | Multimodal | ✅ GA | Stable, widely used |
| `text-embedding-005` | Embedding | ✅ | Vertex embeddings |

### SDK note

This project uses the **new `google-genai` SDK** (`pip install google-genai`) rather than the older
`vertexai.generative_models` path from `google-cloud-aiplatform`. The old path is deprecated as of mid-2026.
See the [migration guide](https://googleapis.github.io/python-genai/) for details.

### Authentication

```bash
# Option 1: Service account (CI/production)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json

# Option 2: Workload Identity (GKE, Cloud Run)
# No credentials file needed — identity is attached to the workload

# Option 3: Local development
gcloud auth application-default login
```

### Documentation

- [Vertex AI overview](https://cloud.google.com/vertex-ai/docs/start/introduction-unified-platform)
- [Generative AI on Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/overview)
- [EU locations](https://cloud.google.com/vertex-ai/docs/general/locations#europe)
- [Gemini model versioning](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versioning)
- [google-genai SDK](https://googleapis.github.io/python-genai/)
- [Vertex AI pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)

---

## 3. Google Vertex AI — Claude (AWAY)

> **Status:** Public Preview, EU multi-region available

### When to use

- You specifically need Anthropic Claude with EU data residency **today** (Azure Foundry EU support is still roadmap).
- You want Anthropic's models (better instruction-following, longer context) without leaving EU infrastructure.
- You can reuse the same GCP project/credentials as Vertex Gemini — one cloud, two model families.

### EU location options

Same as Vertex Gemini. Prefer `eu` (multi-region) for availability, `europe-west4` for strictest single-region.

### Key env vars

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=eu
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_CLAUDE_MODEL=claude-sonnet-4-5@20251001
```

### Available Claude models on Vertex AI (June 2026)

| Model ID | Context window | EU multi-region | Notes |
|----------|---------------|-----------------|-------|
| `claude-opus-4@20250514` | 200K | ✅ | Most capable |
| `claude-sonnet-4-5@20251001` | 200K | ✅ | Recommended ★ |
| `claude-haiku-3-5@20241022` | 200K | ✅ | Fastest / cheapest |
| `claude-sonnet-3-7@20250219` | 200K | ✅ | Extended thinking |

### Important: model ID format

Vertex Claude model IDs use `@` + date suffix (not `-` like the direct Anthropic API):
- Direct API: `claude-sonnet-4-5-20251001`
- Vertex AI: `claude-sonnet-4-5@20251001`

### Documentation

- [Claude on Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude)
- [EU multi-region for Claude (announcement)](https://cloud.google.com/blog/products/ai-machine-learning/multi-region-endpoints-for-claude-available-on-vertex-ai)
- [Supported Claude model IDs on Vertex](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude#supported_models)
- [anthropic[vertex] Python SDK](https://github.com/anthropics/anthropic-sdk-python#vertex-ai)
- [Vertex AI partner models pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing#partner-models)

---

## 4. AWS Bedrock — Claude (AWAY)

> **Status:** GA, EU regions available

### When to use

- Your organisation has an existing AWS footprint and AWS-managed credentials/IAM.
- You want Anthropic Claude in EU AWS regions without adding GCP as a cloud dependency.
- You need strict Frankfurt (Germany) or Dublin (Ireland) data residency specifically within AWS.

### EU regions

| Region code | Location | Claude available |
|-------------|----------|------------------|
| `eu-central-1` | Frankfurt, Germany ★ | ✅ |
| `eu-west-1` | Dublin, Ireland | ✅ |
| `eu-north-1` | Stockholm, Sweden | ✅ |
| `eu-west-3` | Paris, France | ✅ |

### Key env vars

```bash
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=eu-central-1
BEDROCK_CLAUDE_MODEL=anthropic.claude-sonnet-4-5-20251001-v1:0
```

### Available Claude models on Bedrock (June 2026)

| Model ID | Notes |
|----------|-------|
| `anthropic.claude-opus-4-20250514-v1:0` | Most capable |
| `anthropic.claude-sonnet-4-5-20251001-v1:0` | Recommended ★ |
| `anthropic.claude-haiku-3-5-20241022-v2:0` | Fastest / cheapest |
| `anthropic.claude-sonnet-3-7-20250219-v1:0` | Extended thinking |

> **Note:** Model IDs use `-` separators and `v1:0` suffix (differs from Vertex's `@` format).

### Enable model access

You **must** manually enable Anthropic model access in the AWS Console for each region:

1. Go to [AWS Console → Amazon Bedrock → Model access](https://console.aws.amazon.com/bedrock/home#/modelaccess)
2. Switch to your target EU region (e.g., `eu-central-1`)
3. Click **Manage model access** and enable the Claude model(s) you need
4. Wait for access to be granted (usually instant for Anthropic models)

### Authentication options

```bash
# Option 1: Explicit keys (used in this project for simplicity)
AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...

# Option 2: IAM role / instance profile (production recommended)
# No keys needed — boto3 picks up the attached role automatically

# Option 3: AWS SSO / Identity Center
aws sso login --profile your-profile
export AWS_PROFILE=your-profile
```

### Documentation

- [AWS Bedrock overview](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
- [Claude on Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic.html)
- [Supported model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)
- [Enable model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
- [boto3 Bedrock runtime](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime.html)
- [anthropic[bedrock] SDK](https://github.com/anthropics/anthropic-sdk-python#aws-bedrock)
- [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)

---

## 5. Self-hosted (vLLM / Ollama / LocalAI) — HOME

> **Status:** Self-managed, zero data egress

### When to use

- **Strictest data control:** prompts never leave your own infrastructure. No external sub-processor, no data transfer under GDPR Article 46.
- **Bulk / batch workloads:** reserved GPU compute is significantly cheaper than per-token API pricing at scale.
- **Sensitive data tiers:** workloads where even a cloud-provider DPA is insufficient (e.g., medical records, legal discovery).
- **Dev / test:** a local Ollama instance costs nothing beyond hardware already in use.
- **Model diversity:** run any open-weight model (Qwen3, Llama-4, Mistral, Phi-4, Gemma-3) without waiting for hyperscaler availability.

### Compatible servers

| Server | Best for | Notes |
|--------|----------|-------|
| [vLLM](https://docs.vllm.ai/) | Production, high throughput | Continuous batching, tensor parallelism, OpenAI-compatible API |
| [Ollama](https://ollama.com/) | Local dev, easy setup | One-command model download and serve |
| [LocalAI](https://localai.io/) | Edge / CPU inference | Supports GGUF, runs without GPU |
| Any OpenAI-compatible proxy | Bring-your-own gateway | LiteLLM, ArchGW, etc. |

### Key env vars

```bash
SELF_HOSTED_BASE_URL=http://localhost:8000/v1   # vLLM default; Ollama uses :11434/v1
SELF_HOSTED_API_KEY=local-dev-key               # any value for local vLLM
SELF_HOSTED_MODEL=qwen3-32b                     # must match --served-model-name in vLLM
```

### Starting vLLM

```bash
# Basic (single GPU)
vllm serve Qwen/Qwen3-32B \
  --host 0.0.0.0 --port 8000 \
  --served-model-name qwen3-32b

# With 4-bit quantisation (fits 70B on A100 80GB)
vllm serve Qwen/Qwen3-72B \
  --quantization awq \
  --served-model-name qwen3-72b

# Multi-GPU tensor parallelism
vllm serve Qwen/Qwen3-32B \
  --tensor-parallel-size 2 \
  --served-model-name qwen3-32b
```

### Starting Ollama (local dev)

```bash
ollama serve                   # starts on http://localhost:11434
ollama pull qwen3:32b          # download model once
# Set SELF_HOSTED_BASE_URL=http://localhost:11434/v1
# Set SELF_HOSTED_MODEL=qwen3:32b
```

### Recommended open models (Apache 2.0 / MIT, June 2026)

| Model | HF repo | Size | VRAM (fp16) | Notes |
|-------|---------|------|-------------|-------|
| Qwen3-32B | `Qwen/Qwen3-32B` | 32B | ~64 GB | Best overall; fits 1× A100 80GB |
| Mistral-Small-3.2 | `mistralai/Mistral-Small-3.2-24B-Instruct` | 24B | ~48 GB | Fast instruction following |
| Llama-4-Scout | `meta-llama/Llama-4-Scout-17B-16E-Instruct` | 17B active (MoE) | ~34 GB active | Low VRAM/token |
| Phi-4 | `microsoft/Phi-4` | 14B | ~28 GB | Strong code + structured output |
| Gemma-3-27B | `google/gemma-3-27b-it` | 27B | ~54 GB | Multilingual, instruction tuned |

### Azure compute sizing (EU region: `germanywestcentral`)

| VM SKU | GPU | VRAM | On-demand | Reserved 1yr | Use case |
|--------|-----|------|-----------|--------------|----------|
| NC24ads A100 v4 | 1× A100 80 GB | 80 GB | ~€3.10/hr | ~€1.20/hr | 32B fp16, 70B 4-bit |
| NC48ads A100 v4 | 2× A100 80 GB | 160 GB | ~€6.20/hr | ~€2.40/hr | 70B fp16, 100B+ 4-bit |
| NC96ads A100 v4 | 4× A100 80 GB | 320 GB | ~€12.40/hr | ~€4.80/hr | Large models / high throughput |

> Spot instances typically 60–70% cheaper — use with a job queue for batch workloads.

### Documentation

- [vLLM docs](https://docs.vllm.ai/)
- [vLLM OpenAI-compatible server](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html)
- [Ollama docs](https://ollama.com/docs)
- [LocalAI docs](https://localai.io/)
- [Qwen3-32B on HuggingFace](https://huggingface.co/Qwen/Qwen3-32B)
- [OpenAI-compatible API spec](https://platform.openai.com/docs/api-reference/chat)
- [Azure NC A100 v4 pricing](https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/)

---

## Cross-Provider Comparison

| Dimension | Azure OpenAI | Vertex Gemini | Vertex Claude | Bedrock Claude | Self-hosted |
|-----------|-------------|---------------|---------------|----------------|-------------|
| Cloud | Azure | GCP | GCP | AWS | Your infra |
| Models | GPT-4o, o3, o4-mini | Gemini 2.5 Flash/Pro | Claude Sonnet/Opus | Claude Sonnet/Opus | Any open model |
| EU Data Residency | ✅ Full (EU Data Boundary) | ✅ Full (EU multi-region) | ✅ Full (EU multi-region, preview) | ✅ Full (eu-central-1 etc.) | ✅ Full (zero egress) |
| GDPR DPA available | ✅ Microsoft DPA | ✅ Google DPA | ✅ Google DPA | ✅ AWS DPA | N/A — no sub-processor |
| Auth mechanism | API key / Azure AD | Service account / ADC | Service account / ADC | IAM / Access keys | None / custom |
| Streaming | ✅ (`stream=True`) | ✅ (`stream=True`) | ✅ (`messages.stream()`) | ✅ (`messages.stream()`) | ✅ (`stream=True`) |
| Token usage in stream | ✅ (`stream_options`) | ✅ (`usage_metadata`) | ✅ (final message) | ✅ (final message) | ✅ (`stream_options`) |
| SDK | `openai` | `google-genai` | `anthropic[vertex]` | `anthropic[bedrock]` | `openai` (compat.) |
| Home/Away | HOME | AWAY | AWAY | AWAY | HOME |
| Extra cloud dependency | None | GCP project | GCP project | AWS account | None |
| Cost model | Per token | Per token | Per token | Per token | Compute time |
