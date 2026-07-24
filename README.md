# HR Intel Toolkit — 7-Prompt GTM Intelligence System

A production-grade lead intelligence suite for HR Cloud. Built around the **HR Cloud GTM Intelligence Playbook** — 7 agent prompts, 4 evidence tiers, canonical domain verification, and a scored output schema that separates signal from noise.

> These are not generic search prompts. Each one is an operating specification for an autonomous scraping and research agent. They define what to look for, where to look, how to score, and what to do with the results.

---

## The 7 Prompts

| # | Prompt | Target | Scraper |
|---|--------|--------|---------|
| 1 | Manual/Paper Onboarding | Companies still using paper new-hire packets | `scrapers/p01_manual_onboarding/` |
| 2 | Lookalike / Seed DNA | Companies structurally similar to known customers | `scrapers/p02_lookalike/` |
| 3 | ADP Confirmed Users | Companies confirmed using ADP products | `scrapers/p03_adp_confirmed/` |
| 4 | High-Intent Signals | 18 signal families competitors miss | `scrapers/p04_high_intent/` |
| 5 | Workmates Frontline | Multi-location orgs with frontline comm pain | `scrapers/p05_workmates/` |
| 6 | Healthcare / Senior Care | Home health, hospice, senior living, behavioral health | `scrapers/p06_healthcare/` |
| 7 | Education | K-12 districts, charter networks, community colleges | `scrapers/p07_education/` |

Prompt text: `prompts/`  
Module guides: `instructions/`

---

## Operating Model

Run one prompt at a time. Each is a focused intelligence operation.

**Recommended order:**
1. Start with **Prompt 1** (manual onboarding) to build baseline
2. Use **Prompt 4** for broad discovery across 18 signal families
3. Go vertical with **Prompts 6 or 7** for healthcare/education territories
4. Feed high-scoring leads as seeds into **Prompt 2** for lookalike expansion

**Full workflow:**
```
Discover → Resolve → Verify → Score → Reject Aggressively → Enrich → Write Outreach
```

See `instructions/00_operating_model.md` for the complete model.

---

## Evidence Tiers

| Tier | Source | Reliability |
|------|--------|-------------|
| A | Company-hosted PDF or careers page | Very High — direct evidence |
| B | Job posting on company domain mentioning paper process | High |
| C | DDG snippet / news article | Medium — confirm with page fetch |
| D | Inference from industry or size | Low — never sufficient alone |

**Every lead must have at least one Tier A or Tier B signal.**

---

## Scoring Overview

All 7 prompts produce leads scored on 100-point scales:

| Score | Action |
|-------|--------|
| 85–100 | Immediate outreach |
| 75–84 | Outreach with qualification |
| 65–74 | Verification queue |
| < 65 | Reject |

Output uses 25 canonical fields (see `scrapers/shared/schema.py`).

---

## HR Cloud Product Mapping

| Signal | Product | Rationale |
|--------|---------|-----------|
| Paper new hire packets | Onboard | Replace manual onboarding |
| ADP user + paper onboarding | Onboard | Complement ADP payroll |
| Multi-location + frontline comm gap | Workmates | Bridge last-mile communication |
| ADP user + multi-location frontline | Onboard + Workmates | Maximum cross-sell |
| No HRIS at all | Onboard | Greenfield opportunity |

---

## How to Run Each Module

### Prompt 1: Manual Onboarding
```bash
python3 -u scrapers/p01_manual_onboarding/batch3.py 2>&1 | tee /tmp/p01.log
# Output: data/nano_batch3_leads.csv
```

### Prompt 2: Lookalike
```bash
python3 -u scrapers/p02_lookalike/lookalike.py --seeds acme.com,bestcare.org 2>&1 | tee /tmp/p02.log
# Output: data/lookalike_leads.csv
```

### Prompt 3: ADP Confirmed
```bash
python3 -u scrapers/p03_adp_confirmed/adp_finder.py 2>&1 | tee /tmp/p03.log
# Output: data/adp_confirmed_leads.csv
```

### Prompt 4: High-Intent Signals
```bash
python3 -u scrapers/p04_high_intent/intent_signals.py 2>&1 | tee /tmp/p04.log
# Output: data/high_intent_leads.csv
```

### Prompt 5: Workmates Frontline
```bash
python3 -u scrapers/p05_workmates/workmates_finder.py 2>&1 | tee /tmp/p05.log
# Output: data/workmates_leads.csv
```

### Prompt 6: Healthcare / Senior Care
```bash
python3 -u scrapers/p06_healthcare/healthcare_finder.py 2>&1 | tee /tmp/p06.log
# Output: data/healthcare_leads.csv
```

### Prompt 7: Education
```bash
python3 -u scrapers/p07_education/education_finder.py 2>&1 | tee /tmp/p07.log
# Output: data/education_leads.csv
```

### Run via ScrapeGraph Agent
```bash
python3 -u scrapegraph/agent.py --module p06_healthcare
python3 -u scrapegraph/agent.py --module all
python3 -u scrapegraph/agent.py --module p01_manual_onboarding --scrapegraph  # requires OPENAI_API_KEY
```

---

## Pipeline: Build Master CSV

```bash
python3 pipeline/build_master.py
# Output: data/nano_onboarding_MASTER.csv
```

---

## Directory Structure

```
hr-intel-toolkit/
├── prompts/                      # 7 prompt specifications (markdown)
│   ├── 01_manual_onboarding.md
│   ├── 02_lookalike.md
│   ├── 03_adp_confirmed.md
│   ├── 04_high_intent_signals.md
│   ├── 05_workmates_frontline.md
│   ├── 06_healthcare_senior_care.md
│   └── 07_education_intent.md
│
├── scrapers/
│   ├── shared/                   # Shared utilities
│   │   ├── ddg.py               # DDG search with retry/backoff
│   │   ├── fetcher.py           # Page and PDF fetcher
│   │   ├── schema.py            # Canonical 25-column output schema
│   │   └── verifier.py          # Domain verification
│   │
│   ├── p01_manual_onboarding/   # Prompt 1 scrapers (batch1, batch2, batch3)
│   ├── p02_lookalike/           # Prompt 2 lookalike finder
│   ├── p03_adp_confirmed/       # Prompt 3 ADP user finder
│   ├── p04_high_intent/         # Prompt 4 intent signal finder
│   ├── p05_workmates/           # Prompt 5 Workmates prospect finder
│   ├── p06_healthcare/          # Prompt 6 healthcare finder
│   └── p07_education/           # Prompt 7 education finder
│
├── instructions/                 # How-to guides per module
│   ├── 00_operating_model.md    # Core playbook operating model
│   ├── 01_manual_onboarding.md
│   ├── 02_adp_confirmed.md
│   ├── 03_rfp_rfq.md
│   ├── 04_high_intent.md
│   ├── 05_workmates.md
│   ├── 06_healthcare.md
│   ├── 07_education.md
│   └── 08_scrapegraph.md
│
├── scrapegraph/
│   ├── agent.py                 # ScrapeGraph agent entrypoint (all 7 modules)
│   └── prompts/                 # Prompt text files for ScrapeGraph
│
├── pipeline/
│   └── build_master.py          # Merge all CSVs into master
│
└── data/
    ├── nano_onboarding_MASTER.csv
    ├── workmates_leads.csv       (generated)
    ├── healthcare_leads.csv      (generated)
    ├── education_leads.csv       (generated)
    └── lookalike_leads.csv       (generated)
```

---

## ScrapeGraph Integration

The `scrapegraph/agent.py` wraps all 7 modules for ScrapeGraph Cloud deployment.

With `OPENAI_API_KEY` set, it uses ScrapeGraph's LLM-powered extraction for higher accuracy on complex pages. Without the key, it falls back to the plain DDG + BeautifulSoup scrapers.

See `instructions/08_scrapegraph.md` for setup details.

---

## Key Lessons Learned

1. **K-12 school districts have the highest hit rate** for paper new hire packets — `site:.k12.[state].us filetype:pdf` is extremely reliable.

2. **Home health agencies almost universally still use paper packets** — caregiver new hire packet PDFs are findable on company domains.

3. **ADP users are the easiest cross-sell** — confirmed ADP users who also show paper onboarding signals need no education about the problem.

4. **DDG rate limits are real** — the shared `ddg.py` module handles this with 4-retry exponential backoff.

5. **Domain deduplication matters** — use `scrapers/shared/verifier.py` to collapse subdomains and detect CDN/generic hosts before counting a domain as a unique company.

6. **Reject aggressively** — a list of 50 highly qualified leads outperforms 500 guesses every time.

---

## Requirements

```bash
pip install -r requirements.txt
```

Key packages: `duckduckgo-search`, `requests`, `beautifulsoup4`, `lxml`, `pdfminer.six`

Optional for ScrapeGraph: `scrapegraphai`, `openai`
