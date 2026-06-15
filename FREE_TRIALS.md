# Free & Trial API Access Guide

How to get API keys for each provider in this repo without paying upfront.

---

## TL;DR — Recommended order

| Priority | Provider | Free path | Effort |
|----------|----------|-----------|--------|
| 1st | **Vertex AI (Gemini + Claude)** | $300 GCP credit, 90 days | Low — one account unlocks two providers |
| 2nd | **AWS Bedrock (Claude)** | $100 AWS credit | Low — but must enable model access manually |
| 3rd | **Anthropic direct API** | ~$5 credit (or $300 with student email) | Minimal — instant, no card needed |
| 4th | **Azure OpenAI** | Paid only (free credits don’t apply) | High — needs company/uni email + approval |

> **Best single move:** Create a new GCP account → get $300 Vertex credit → immediately unlocks
> both `vertex_gemini_provider.py` and `vertex_claude_provider.py` with one service account JSON.

---

## 1. Google Vertex AI — Best free option ⭐

### What you get
- **$300 free trial credit** on all new Google Cloud accounts, valid for **90 days**, usable across
  all GCP services including Vertex AI (Gemini + Claude).
- **Vertex AI free tier** on top: up to 1,000 requests/day for some Gemini models, free Workbench
  notebook hours, no billing required for Express Mode (limited quotas, 90 days).

### Sign-up steps

1. Go to [https://cloud.google.com/free](https://cloud.google.com/free) and click **Get started for free**.
2. Sign in with a Google account (personal Gmail works).
3. Enter a credit card (required for identity verification — you won’t be charged until you upgrade).
4. Your account starts with $300 credit and a 90-day trial.
5. In the GCP Console, enable the **Vertex AI API**:
   ```
   APIs & Services → Enable APIs → search "Vertex AI API" → Enable
   ```
6. Create a service account and download the JSON key:
   ```
   IAM & Admin → Service Accounts → Create → Role: Vertex AI User → Keys → Add Key → JSON
   ```
7. Set in your `.env`:
   ```bash
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=eu
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/downloaded-key.json
   ```

### Important notes
- As of early 2026, the $300 credits **do not work via Google AI Studio** — you must access
  Gemini via the **Vertex AI API** specifically. Your repo already does this correctly.
- Vertex Claude (Anthropic on Vertex) is billed separately as a partner model but uses the same
  GCP billing account, so the $300 credit covers it too.

### Docs
- [Google Cloud Free Trial](https://cloud.google.com/free)
- [Vertex AI pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [Vertex AI quickstart](https://cloud.google.com/vertex-ai/docs/start/introduction-unified-platform)

---

## 2. AWS Bedrock — $100 free credit

### What you get
- **$100 in credits immediately** when you create a new AWS Free Tier account.
- Potential to earn up to **$100 more** as you explore key services.
- Bedrock has **no dedicated free tier** — all model inference is billed per token, but the
  general account credit covers it.

### Sign-up steps

1. Go to [https://aws.amazon.com/free](https://aws.amazon.com/free) and create an account.
2. Enter a credit card (required; you won’t be charged while credit remains).
3. In the AWS Console, switch to your target EU region (e.g. `eu-central-1` for Frankfurt).
4. **Manually enable Anthropic model access** — this is required even on trial accounts:
   ```
   AWS Console → Amazon Bedrock → Model access → Manage model access
   → Enable: Anthropic Claude Sonnet (or whichever model you need)
   ```
5. Create an IAM user with `AmazonBedrockFullAccess` policy and generate access keys.
6. Set in your `.env`:
   ```bash
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   AWS_REGION=eu-central-1
   ```

### EU regions with Claude support

| Region code | Location |
|-------------|----------|
| `eu-central-1` | Frankfurt, Germany ★ recommended |
| `eu-west-1` | Dublin, Ireland |
| `eu-north-1` | Stockholm, Sweden |
| `eu-west-3` | Paris, France |

### Docs
- [AWS Free Tier](https://aws.amazon.com/free/)
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
- [Enable Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)

---

## 3. Anthropic API (direct)

### What you get
- **~$5 in free API credits** for new accounts — no payment details required to claim.
- **Student bonus:** University email holders can apply for up to **$300 in credits** via
  Anthropic’s education program.
- No ongoing free tier beyond initial credits.

### Sign-up steps

1. Go to [https://console.anthropic.com](https://console.anthropic.com) and sign up.
2. Verify your email. Free credits are added automatically.
3. Navigate to **API Keys** → **Create Key**.
4. If you have a university email (e.g. TU Kaiserslautern), apply for the student credit:
   [https://www.anthropic.com/education](https://www.anthropic.com/education)

### Important note for this repo

The direct Anthropic API key is **not used** by the four provider scripts in this repo.
The repo uses:
- `anthropic[vertex]` → authenticated via GCP service account (no Anthropic API key needed)
- `anthropic[bedrock]` → authenticated via AWS IAM credentials (no Anthropic API key needed)

A direct Anthropic API key would only be useful if you add a fifth provider script
(`providers/anthropic_direct_provider.py`) for the direct `api.anthropic.com` endpoint.
Note: the direct API has no EU data residency guarantee (traffic goes to Anthropic’s US infra).

### Docs
- [Anthropic Console](https://console.anthropic.com)
- [Anthropic API getting started](https://docs.anthropic.com/en/api/getting-started)
- [Anthropic education credits](https://www.anthropic.com/education)

---

## 4. Azure OpenAI — Hardest to get free

### What you get
- Azure gives **$200 in free credits** to new accounts, but these credits **do not apply to
  Azure OpenAI Service** — Azure OpenAI requires a paid subscription.
- A **company or university email is required** — personal Gmail/Outlook addresses are rejected.

### Sign-up steps

1. Go to [https://azure.microsoft.com/free](https://azure.microsoft.com/free) and create an
   account using your **TUK or work email**.
2. Once in the Azure Portal, search for **Azure OpenAI** and click **Create**.
3. You will be prompted to request access. Fill in the form — approvals typically take 1–2 business days.
4. After approval, create a deployment:
   ```
   Azure OpenAI Studio → Deployments → Create new deployment
   → Model: gpt-4o  → Region: germanywestcentral (or westeurope)
   ```
5. Get your endpoint and key:
   ```
   Azure OpenAI resource → Keys and Endpoint
   ```
6. Set in your `.env`:
   ```bash
   AZURE_OPENAI_API_KEY=your-key
   AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4o
   AZURE_OPENAI_API_VERSION=2025-01-01-preview
   ```

### EU regions to pick during deployment

| Region code | Location |
|-------------|----------|
| `germanywestcentral` | Frankfurt, Germany ★ recommended |
| `westeurope` | Netherlands |
| `francecentral` | Paris, France |
| `swedencentral` | Sweden |

### Docs
- [Azure free account](https://azure.microsoft.com/free)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Request Azure OpenAI access](https://aka.ms/oai/access)
- [Azure OpenAI pricing](https://azure.microsoft.com/en-us/pricing/details/azure-openai/)

---

## Quick setup checklist

```
[ ] GCP account created + Vertex AI API enabled
[ ] GCP service account JSON downloaded + path set in .env
[ ] GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION=eu set in .env

[ ] AWS account created
[ ] Anthropic model access enabled in AWS Console (eu-central-1)
[ ] AWS IAM access key created + set in .env
[ ] AWS_REGION=eu-central-1 set in .env

[ ] (Optional) Anthropic console account created for direct API testing
[ ] (Optional) Azure OpenAI access requested via TUK/work email

[ ] cp .env.example .env
[ ] uv sync
[ ] uv run pytest  # verify everything wires up (no API calls made)
```
