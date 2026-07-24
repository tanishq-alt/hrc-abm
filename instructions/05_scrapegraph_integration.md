# ScrapeGraph Integration Guide

## What is ScrapeGraph?

ScrapeGraph is an AI-powered web scraping framework that combines traditional scraping with LLM-based extraction. Instead of writing brittle regex, you describe what you want in plain English and the LLM extracts structured data from any page.

---

## Setup

```bash
pip install scrapegraphai openai
export OPENAI_API_KEY=sk-...
```

---

## Running Modules via ScrapeGraph Agent

```bash
# Run single module
python scrapegraph/scrapegraph_agent.py --module manual_onboarding --scrapegraph

# Run ADP finder with LLM extraction
python scrapegraph/scrapegraph_agent.py --module adp_confirmed --scrapegraph

# Run RFP scanner
python scrapegraph/scrapegraph_agent.py --module rfp_rfq --scrapegraph

# Run all modules
python scrapegraph/scrapegraph_agent.py --module all

# Output JSON only
python scrapegraph/scrapegraph_agent.py --module manual_onboarding --output json
```

---

## ScrapeGraph Cloud Deployment

### Step 1: Upload to ScrapeGraph Cloud
1. Go to app.scrapegraph.ai
2. Create new agent
3. Upload `scrapegraph/scrapegraph_agent.py` as your entrypoint
4. Set environment variables:
   - `OPENAI_API_KEY` = your key
   - `MODULE` = `manual_onboarding` (or whichever module)

### Step 2: Configure Prompt
Each module has a prompt in `scrapegraph/prompts/`:
- `manual_onboarding.txt` — finds paper-based onboarding companies
- `adp_confirmed.txt` — finds confirmed ADP users
- `rfp_rfq.txt` — finds active HR software RFPs

The prompts are loaded automatically by the agent.

### Step 3: Schedule Runs
In ScrapeGraph Cloud, schedule the agent to run:
- **Manual onboarding**: Weekly (new PDFs get indexed constantly)
- **ADP confirmed**: Daily (job postings refresh daily)
- **RFP/RFQ**: Daily (deadlines are time-sensitive)
- **High intent**: 2x/week

---

## Using SmartScraperGraph Directly

```python
from scrapegraphai.graphs import SmartScraperGraph

config = {
    "llm": {
        "api_key": "sk-...",
        "model": "openai/gpt-4o-mini",
    },
}

# Find manual onboarding companies from a DDG results page
graph = SmartScraperGraph(
    prompt="""
    Extract companies that host new hire packet PDFs on their websites.
    Return: company_name, domain, evidence_quote, signal_type, industry, state.
    Only include companies with clear evidence of paper-based onboarding.
    """,
    source="https://duckduckgo.com/?q=%22new+hire+packet%22+filetype%3Apdf&ia=web",
    config=config,
)
result = graph.run()
print(result)
```

---

## Combining DDG Scraper + ScrapeGraph

The most powerful approach:
1. **DDG scraper** finds candidate URLs (fast, no LLM cost)
2. **ScrapeGraph** extracts structured data from the best candidates (accurate, handles messy HTML)

```python
from duckduckgo_search import DDGS
from scrapegraphai.graphs import SmartScraperGraph

# Step 1: DDG finds URLs
with DDGS() as ddgs:
    results = list(ddgs.text('"new hire packet" filetype:pdf', max_results=20))
    urls = [r["href"] for r in results]

# Step 2: ScrapeGraph extracts from each URL
prompt = open("scrapegraph/prompts/manual_onboarding.txt").read()
config = {"llm": {"api_key": "sk-...", "model": "openai/gpt-4o-mini"}}

all_leads = []
for url in urls[:5]:
    graph = SmartScraperGraph(prompt=prompt, source=url, config=config)
    result = graph.run()
    if isinstance(result, list):
        all_leads.extend(result)
```

---

## Cost Estimate

| Module | Queries | Pages fetched | Est. GPT-4o-mini cost |
|--------|---------|---------------|----------------------|
| manual_onboarding (batch3) | 147 | ~200 pages | ~$0.80 |
| adp_confirmed | 35 | ~80 pages | ~$0.30 |
| rfp_rfq | 40 | ~60 pages | ~$0.25 |
| high_intent | 35 | ~70 pages | ~$0.28 |
| **Total** | **257** | **~410 pages** | **~$1.60/run** |

Running weekly = ~$6.40/month for unlimited lead discovery.

---

## Integration with Claude Code (This Environment)

You're already running this toolkit from Claude Code. To re-run any module:

```bash
# From /Users/tanishqmac/lead-intel/scripts/
python3 -u nano_batch3.py 2>&1 | tee /tmp/nano_batch3.log &
tail -f /tmp/nano_batch3.log

# Or from the toolkit repo:
cd /Users/tanishqmac/hr-intel-toolkit
python scrapegraph/scrapegraph_agent.py --module manual_onboarding
```

Results always land in `data/MASTER.csv` after running `python pipeline/build_master.py`.
