# Cloud Cost Reference — Customer Operating Costs

This platform is deployed per customer. Cloud infrastructure and AI API costs
are **billed directly to each customer** as operating expenses — not absorbed
by the platform provider. This document helps customers and implementation
teams understand what to expect and how to keep costs lean.

---

## Billing Model

| Layer | Who pays | What it covers |
|---|---|---|
| Cloud infrastructure (compute, storage, networking) | Customer | GCP / AWS / Azure resources provisioned in their account |
| LLM API tokens | Customer | Per-token charges for Claude, Gemini, GPT-4o |
| Platform setup & integration | Engagement fee | One-time or retainer; scoped separately |

Each customer runs the platform in **their own cloud account** — no shared
tenancy, no pooled API keys.

---

## LLM Token Pricing Baseline

Token pricing is identical across providers for Claude Sonnet:

| Metric | Price |
|---|---|
| Input tokens | $3.00 / M tokens |
| Output tokens | $15.00 / M tokens |

> The same model costs the same on Vertex AI (Google Cloud), AWS Bedrock, and
> the direct Anthropic API. Provider choice affects EU data residency and
> infrastructure alignment — not per-token cost.

### Rough monthly token spend (60% input / 40% output split)

| Usage tier | Tokens / month | Monthly cost |
|---|---|---|
| Light usage | 50M | ~$390 |
| Active platform | 500M | ~$3,900 |
| Heavy / multi-tenant | 2B | ~$15,600 |

Actual spend scales with document volume, agent call frequency, and context
window usage per workflow.

---

## Cost Levers for Customers

These require no model changes — only API call adjustments in the platform:

- **Prompt caching** — ~90% off repeated input tokens (system prompts, shared
  document context reused across agent steps). Highest impact for RAG and
  agentic document workflows.
- **Batch API** — ~50% off output tokens for non-real-time workloads (bulk
  document processing, overnight ingestion jobs).
- **Combined effect** — can reduce effective monthly token spend by ~60%+ for
  typical document-heavy pipelines.

---

## Provider Recommendation by Customer Cloud Preference

| Customer's existing cloud | Recommended LLM provider | Notes |
|---|---|---|
| Google Cloud | **Vertex AI** (Gemini + Claude) | Native auth, `location='eu'` for EU residency, no cross-cloud egress |
| AWS | **AWS Bedrock** (Claude) | IAM-native, EU regions: `eu-central-1` Frankfurt, `eu-west-1` Dublin |
| Azure | **Vertex AI or Bedrock** (AWAY) | Azure Foundry Claude is not EU-resident today; cross-cloud call required |
| No preference | **Google Cloud Vertex AI** | Best EU routing flexibility, Gemini + Claude in one platform |

---

## EU Data Residency

All LLM calls must stay within the EU. Supported paths:

- **Google Cloud Vertex AI** — set `location='eu'` (multi-region) or
  `europe-west4` (Netherlands, strictest single-region).
- **AWS Bedrock** — use `eu-central-1` (Frankfurt) or `eu-west-1` (Dublin).
  Model access must be enabled per region in the AWS Console.
- **Azure AI Foundry + Claude** — not EU-resident today; Claude runs on
  Anthropic infrastructure regardless of Azure region. Azure OpenAI (GPT-4o)
  is EU-compliant and can be used as the Azure-native alternative.

---

## Startup Credits (for customers who qualify)

If a customer is an early-stage company, they may apply for cloud startup
credits to offset initial operating costs:

| Program | Max credits | Link |
|---|---|---|
| Google Cloud — AI Tier | $350,000 | https://cloud.google.com/startup/ai |
| AWS Activate — Portfolio | $200,000 | https://aws.amazon.com/startups/credits/ |
| Microsoft for Startups | $150,000 | https://www.microsoft.com/en-us/startups |

Credits cover all platform usage in the customer's account, not just LLM tokens.

---

## References

- Claude Sonnet pricing on Vertex AI — https://futureagi.com/llm-cost-calculator/vertex-ai/claude-sonnet-4-6/
- Claude Sonnet pricing on Bedrock — https://futureagi.com/llm-cost-calculator/bedrock/us-anthropic-claude-sonnet-4-6/
- Anthropic Batch API & prompt caching — https://platform.claude.com/docs/en/about-claude/pricing
- Vertex AI EU locations — https://cloud.google.com/vertex-ai/docs/general/locations#europe
- AWS Bedrock model access — https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html
- Azure EU Data Boundary — https://learn.microsoft.com/en-us/privacy/eudb/eu-data-boundary-learn
