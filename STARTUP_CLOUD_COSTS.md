# Startup Cloud Cost Snapshot

A rough cost reference for an early-stage AI startup choosing between
Google Cloud Vertex AI, AWS Bedrock, and Azure for LLM workloads.

---

## Why Google Cloud Often Wins Early

| Platform | Max Startup Credits | Notes |
|---|---|---|
| **Google Cloud — AI Tier** | **$350,000** | AI-first startups, spread over 2 years ($250k yr1 + $100k yr2) |
| **Google Cloud — Standard** | $200,000 | Any early-stage startup |
| **AWS Activate — Portfolio** | $200,000 | Requires an Activate Provider (VC / accelerator) Org ID |
| **AWS Activate — Founders** | $5,000 | Self-funded / bootstrapped |
| **Microsoft for Startups** | $150,000 | Staged unlock, Series A+ for full amount |

Credits cover all platform usage (compute, storage, APIs) — not just LLM tokens.

---

## Claude Sonnet Pricing Baseline

Token pricing is identical across providers:

| Metric | Price |
|---|---|
| Input tokens | $3.00 / M tokens |
| Output tokens | $15.00 / M tokens |

> Pricing is the same on Vertex AI (Google Cloud), Bedrock (AWS), and the
> direct Anthropic API. The cost advantage comes entirely from credits and
> discount programs.

### Rough monthly spend (60% input / 40% output split)

| Usage tier | Tokens / month | Monthly cost |
|---|---|---|
| Early MVP | 50M | ~$390 |
| Growth | 500M | ~$3,900 |
| Scale | 2B | ~$15,600 |

---

## Cost Levers: Batch API + Prompt Caching

Both Vertex AI and Bedrock support these:

- **Batch API** — ~50% off output tokens for async workloads
- **Prompt caching** — ~90% off repeated input tokens (system prompts, document context)
- **Combined effect** — can reduce effective monthly spend by ~60%+ at Growth scale

These require zero model changes — just API call adjustments.

---

## EU Routing Consideration

- **Google Cloud Vertex AI** — `location='eu'` multi-region endpoint keeps
  all processing inside the EU. Claude + Gemini both available.
- **AWS Bedrock** — EU regions available (Frankfurt `eu-central-1`,
  Dublin `eu-west-1`, Stockholm `eu-north-1`). Claude models available
  after enabling model access per region.
- **Azure AI Foundry** — Claude on Azure today runs on Anthropic-hosted
  infrastructure regardless of Azure region. True EU-pinned Claude on
  Azure is roadmap (2026). Not recommended for strict EU data residency.

---

## Rough Recommendation

- **Google Cloud Vertex AI** — best choice if minimising burn is the priority.
  Highest startup credits ($350k), Gemini + Claude available, solid EU routing.
- **AWS Bedrock** — strong if team already operates on AWS and can fully
  use Activate credits. Good EU region coverage for Claude.
- **Azure** — consider only if Microsoft ecosystem alignment is a hard
  requirement. Lower credit ceiling, Claude EU routing still limited.

---

## References

- Google Cloud for Startups AI Program — https://cloud.google.com/startup/ai
- Google for Startups Cloud Program — https://cloud.google.com/startup
- Google Cloud Startup Benefits & Eligibility — https://cloud.google.com/startup/benefits
- AWS Activate Credits — https://aws.amazon.com/startups/credits/
- Microsoft for Startups — https://www.microsoft.com/en-us/startups
- Microsoft for Startups Benefits — https://learn.microsoft.com/en-us/microsoft-for-startups/benefits
- Claude Sonnet 4.6 pricing on Vertex AI — https://futureagi.com/llm-cost-calculator/vertex-ai/claude-sonnet-4-6/
- Claude Sonnet 4.6 pricing on Bedrock — https://futureagi.com/llm-cost-calculator/bedrock/us-anthropic-claude-sonnet-4-6/
- Anthropic Batch API & prompt caching — https://platform.claude.com/docs/en/about-claude/pricing
