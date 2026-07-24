# HR Intel Toolkit

A battle-tested scraper suite for finding high-intent HR software leads. Built around real signals — not guesses. Four independent modules, a shared merge pipeline, and full ScrapeGraph integration.

---

## What's Inside

| Module | What it finds | Signal strength |
|--------|--------------|-----------------|
| `scrapers/manual_onboarding/` | Companies still using paper new-hire packets, fax forms, in-person HR paperwork | ⭐⭐⭐ Highest — explicit evidence |
| `scrapers/adp_confirmed/` | Confirmed ADP users (via job postings, LinkedIn, G2 reviews) | ⭐⭐⭐ High — named incumbent |
| `scrapers/rfp_rfq/` | Active government/enterprise RFPs for HR/onboarding/HRIS software | ⭐⭐⭐ High — buying intent confirmed |
| `scrapers/high_intent/` | Companies with recent HR system job posts, G2 comparisons, or review activity | ⭐⭐ Medium — behavioral intent |

---

## Quick Start

```bash
git clone https://github.com/tanishq-alt/hr-intel-toolkit.git
cd hr-intel-toolkit
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY if using ScrapeGraph
```

### Run manual onboarding discovery (most productive)
```bash
python scrapers/manual_onboarding/nano_batch3.py
python pipeline/build_master.py
```

### Run ADP confirmed user finder
```bash
python scrapers/adp_confirmed/adp_finder.py
```

### Run RFP/RFQ scanner
```bash
python scrapers/rfp_rfq/rfp_finder.py
```

### Run via ScrapeGraph (AI-powered)
```bash
python scrapegraph/scrapegraph_agent.py --module manual_onboarding
python scrapegraph/scrapegraph_agent.py --module adp_confirmed
python scrapegraph/scrapegraph_agent.py --module rfp_rfq
```

---

## Output Format

All modules output CSV with these fields:
```
Company Name, Verified Company Domain, Official Website, Country,
State or Province, Industry, Estimated Employee Count,
Exact Manual-Onboarding Signal, Exact Evidence Quote,
Reason This Indicates Manual Onboarding, Signal Type,
Evidence Source Title, Verified Evidence Link, Evidence Date,
Confidence Level, Recommended Outreach Angle
```

`pipeline/build_master.py` merges all batch CSVs, deduplicates by canonical domain, and outputs `data/MASTER.csv`.

---

## Module Guides

- [Manual Onboarding Discovery](instructions/01_manual_onboarding.md)
- [ADP Confirmed Users](instructions/02_adp_confirmed.md)
- [RFP/RFQ Scanner](instructions/03_rfp_rfq.md)
- [High Intent Signals](instructions/04_high_intent.md)
- [ScrapeGraph Integration](instructions/05_scrapegraph_integration.md)

---

## Key Lessons Learned

1. **`filetype:pdf "new hire packet"` is the gold standard query** — surfaces actual company-hosted PDFs that are undeniable paper-onboarding evidence.
2. **DDG rate-limits hard** — use 4-second inter-query delay, exponential backoff (20s × attempt), and `python -u` for unbuffered output.
3. **Filter patient paperwork** — many medical sites match "bring paperwork" but it's for patients, not employees. Check for `employee|HR|new hire` context.
4. **CDN domains are noise** — s3.amazonaws.com, hubspotusercontent, squarespace host PDFs for unknown companies. Skip them.
5. **Large enterprises hide HR behind auth portals** — BAYADA, Amedisys, etc. won't expose PDFs. Target school districts, community colleges, government agencies, small nonprofits.
6. **Best verticals**: K12 school districts (.k12.XX.us), community colleges (.edu), county/city government (.gov), home care agencies, faith-based orgs, small healthcare systems.

---

## Repo Structure

```
hr-intel-toolkit/
├── scrapers/
│   ├── manual_onboarding/   # DDG filetype:pdf signal scrapers (3 batches)
│   ├── adp_confirmed/       # ADP user discovery via job posts + signals
│   ├── rfp_rfq/             # Government/enterprise RFP scanners
│   └── high_intent/         # Behavioral intent signals (G2, job posts, reviews)
├── pipeline/
│   ├── build_master.py      # Merge + dedup all batch CSVs → MASTER.csv
│   └── filters.py           # Shared exclusion/cleaning logic
├── scrapegraph/
│   ├── scrapegraph_agent.py # ScrapeGraph-compatible CLI agent
│   └── prompts/             # Per-module LLM prompts
├── instructions/            # Step-by-step guides per module
├── data/                    # Output CSVs (gitignored except .gitkeep)
└── requirements.txt
```
