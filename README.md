# HR Intel Toolkit — 7-Prompt GTM Intelligence System

A production-grade lead intelligence suite for HR Cloud. Built around the **HR Cloud GTM Intelligence Playbook** — 7 agent prompts, 4 evidence tiers, canonical domain verification, and a scored output schema that separates signal from noise.

> **The weak version of this project produces thousands of companies with guessed domains, stale job posts, and vague 'intent.' That data wastes sales capacity. This toolkit only surfaces verified, scored, outreach-ready leads.**

---

## The 7 Prompts

| # | Prompt | Scraper | What it finds | Top signals |
|---|--------|---------|---------------|-------------|
| 1 | Manual Onboarding | `p01_manual_onboarding/` | Companies with paper new-hire packets, manual I-9/W-4, fax/mail onboarding | Company-hosted PDF packets, job posts describing manual tasks |
| 2 | Lookalike Finder | `p02_lookalike/` | Organizations matching the DNA of known HR Cloud customers | 7-dimension DNA model: operating model, workforce type, compliance complexity |
| 3 | ADP Confirmed | `p03_adp_confirmed/` | Confirmed ADP Workforce Now / ADP Run users — displacement candidates | ADP tenant URLs, job posts requiring ADP proficiency |
| 4 | High-Intent Signals | `p04_high_intent/` | Companies exhibiting behavioral buying signals across 18 signal families | Acquisition pressure, OSHA citations, HR transformation hires, grant awards |
| 5 | Workmates Frontline | `p05_workmates/` | Large frontline/hourly workforces without a digital communication platform | Frontline comm gaps, high turnover, no-email workforce signals |
| 6 | Healthcare / Senior Care | `p06_healthcare/` | Home health, SNF, assisted living, behavioral health employers | CMS deficiency reports, caregiver hiring surges, credential tracking gaps |
| 7 | Education Intent | `p07_education/` | K-12 districts, charter networks, Head Start, community colleges | Seasonal onboarding surges, PDF new-hire packets on .k12 domains |

---

## Quick Start

```bash
git clone https://github.com/tanishq-alt/hr-intel-toolkit.git
cd hr-intel-toolkit
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY if using ScrapeGraph
```

### Run any scraper

```bash
# Prompt 1: Manual onboarding (most productive, start here)
python3 -u scrapers/p01_manual_onboarding/batch3.py 2>&1 | tee /tmp/batch3.log &
tail -f /tmp/batch3.log

# Prompt 3: ADP confirmed users
python3 -u scrapers/p03_adp_confirmed/adp_finder.py 2>&1 | tee /tmp/adp.log

# Prompt 4: High-intent behavioral signals
python3 -u scrapers/p04_high_intent/intent_signals.py 2>&1 | tee /tmp/intent.log

# Prompt 5: Workmates frontline communication
python3 -u scrapers/p05_workmates/workmates_finder.py 2>&1 | tee /tmp/workmates.log

# Prompt 6: Healthcare & senior care
python3 -u scrapers/p06_healthcare/healthcare_finder.py 2>&1 | tee /tmp/healthcare.log

# Prompt 7: Education intent
python3 -u scrapers/p07_education/education_finder.py 2>&1 | tee /tmp/education.log

# Prompt 2: Lookalike (provide seed domains)
python3 -u scrapers/p02_lookalike/lookalike.py --seeds acme.com,bestcare.org 2>&1 | tee /tmp/lookalike.log
```

### Merge all outputs into master
```bash
python3 pipeline/build_master.py
```

### Run via ScrapeGraph (AI-powered extraction)
```bash
python scrapegraph/scrapegraph_agent.py --module manual_onboarding
python scrapegraph/scrapegraph_agent.py --module adp_confirmed
python scrapegraph/scrapegraph_agent.py --module all
```

---

## Canonical Output Schema

All 7 scrapers output to the same 25-column CSV schema (defined in `scrapers/shared/schema.py`):

| Column | Description |
|--------|-------------|
| `company_name` | Verified company name |
| `canonical_domain` | Employer's actual domain (not a job board or ATS) |
| `country` | ISO country code |
| `industry` | Vertical classification |
| `employee_range` | Size band (50-500, 500-2000, etc.) |
| `primary_signal_category` | Signal type (manual_onboarding, adp_confirmed, etc.) |
| `strongest_signal_summary` | Top evidence quote (≤30 words) |
| `strongest_signal_url` | URL of top evidence |
| `adp_status` | `confirmed` / `strongly_likely` / `not_found` / `not_checked` |
| `fit_score` | 0-100 |
| `intent_score` | 0-100 |
| `evidence_score` | 0-100 |
| `timing_score` | 0-100 |
| `total_score` | Weighted total |
| `confidence` | `confirmed` / `high` / `medium` |
| `best_hr_cloud_product` | `Onboard` / `Workmates` / `Onboard+Workmates` |
| `outreach_angle` | Personalized opener premise |
| `recommended_buyer_titles` | Decision-maker titles to target |
| `disqualifiers_or_risks` | Flags to verify before outreach |

**Score thresholds**: 85-100 = Tier 1 (outreach-ready) · 75-84 = Tier 2 · 65-74 = verification queue · <65 = reject

---

## Evidence Tiers

| Tier | Source | Use |
|------|--------|-----|
| **A** | Company's own domain (PDF, careers page, handbook) | Final proof — sufficient alone |
| **B** | Reputable independent (state gov, county job board, SAM.gov, CMS database) | Strong signal — combine with A for confirmed |
| **C** | Job aggregator, review site, news article | Directional — confirm with A or B before outreach |
| **D** | Reddit, Glassdoor, social media | Discovery only — never standalone proof |

**Rule**: Minimum Tier A or B evidence required for outreach. Tier C alone = verification queue.

---

## Domain Verification Protocol (7 Steps)

Implemented in `scrapers/shared/verifier.py`:
1. Extract netloc, strip `www.`
2. Apply manual corrections (ATS/CDN domains → actual employer domain)
3. Skip generic CDN/hosting domains (S3, WordPress, Squarespace, etc.)
4. Skip job boards (Indeed, LinkedIn, Greenhouse, Lever, etc.)
5. Collapse to root domain for deduplication
6. Flag holding company domains (detect "holdings", "group", "capital" in domain)
7. Return `domain_status`: `verified` / `verified_parent_only` / `facility_no_unique_domain` / `unresolved`

---

## Repo Structure

```
hr-intel-toolkit/
├── prompts/                        # 7 playbook prompts as markdown (human-readable specs)
│   ├── 01_manual_onboarding.md
│   ├── 02_lookalike.md
│   ├── 03_adp_confirmed.md
│   ├── 04_high_intent_signals.md
│   ├── 05_workmates_frontline.md
│   ├── 06_healthcare_senior_care.md
│   └── 07_education_intent.md
│
├── scrapers/
│   ├── shared/                     # Shared utilities
│   │   ├── schema.py               # Canonical 25-column output schema
│   │   ├── ddg.py                  # DDG search with 4-retry backoff
│   │   ├── fetcher.py              # HTML/PDF text fetcher
│   │   └── verifier.py             # 7-step domain verification protocol
│   │
│   ├── p01_manual_onboarding/      # Prompt 1: paper onboarding signals
│   │   ├── batch1.py               # 60 DDG queries
│   │   ├── batch2.py               # 60 DDG queries (expanded)
│   │   └── batch3.py               # 147 DDG queries (current production)
│   │
│   ├── p02_lookalike/              # Prompt 2: seed DNA lookalike model
│   │   └── lookalike.py            # 7-phase DNA matching engine
│   │
│   ├── p03_adp_confirmed/          # Prompt 3: ADP confirmed users
│   │   └── adp_finder.py           # 35-query ADP signal finder
│   │
│   ├── p04_high_intent/            # Prompt 4: 18 behavioral signal families
│   │   └── intent_signals.py       # Regulatory, acquisition, growth signals
│   │
│   ├── p05_workmates/              # Prompt 5: frontline comm gaps
│   │   └── workmates_finder.py     # Deskless workforce signal finder
│   │
│   ├── p06_healthcare/             # Prompt 6: healthcare/senior care
│   │   └── healthcare_finder.py    # CMS/OSHA-driven healthcare finder
│   │
│   └── p07_education/             # Prompt 7: education intent
│       └── education_finder.py     # K-12, Head Start, seasonal hiring
│
├── pipeline/
│   └── build_master.py             # Merge, dedup, clean all outputs → MASTER.csv
│
├── scrapegraph/
│   ├── scrapegraph_agent.py        # ScrapeGraph-compatible CLI agent
│   └── prompts/                    # LLM extraction prompts per module
│
├── instructions/
│   ├── 00_operating_model.md       # Playbook overview and operating principles
│   ├── 01_manual_onboarding.md     # Detailed guide: Prompt 1
│   ├── 02_adp_confirmed.md         # Detailed guide: Prompt 3
│   ├── 03_rfp_rfq.md               # RFP/RFQ scanner guide
│   └── 05_scrapegraph_integration.md
│
└── data/
    ├── nano_onboarding_MASTER.csv  # 78 verified manual onboarding companies
    └── .gitkeep
```

---

## Key Lessons Learned

1. **`filetype:pdf "new hire packet"` is the gold standard query** — surfaces company-hosted PDFs that are undeniable paper-onboarding evidence.
2. **DDG rate-limits hard** — use 4-second inter-query delay, 20s × attempt exponential backoff, `python3 -u` for unbuffered output.
3. **Filter patient paperwork** — healthcare searches surface patient intake forms. Check for `employee|HR|new hire` context before scoring.
4. **CDN domains are noise** — S3, HubSpot CDN, Squarespace host PDFs for unknown companies. The verifier filters these automatically.
5. **Domain guessing is not domain verification** — `verify_domain()` in `shared/verifier.py` is the only authority. A guessed domain is not a verified domain.
6. **Best verticals**: K-12 school districts (`.k12.XX.us`), community colleges (`.edu`), county/city government (`.gov`), home care agencies, faith-based orgs, small healthcare systems.
7. **ADP scope discipline** — a `workforcenow.adp.com` tenant proves recruiting module use ONLY. Never claim payroll confirmation from a tenant URL alone.

---

## Cost Estimate (ScrapeGraph / LLM runs)

| Module | Queries | Est. pages | GPT-4o-mini cost |
|--------|---------|------------|-----------------|
| p01 manual_onboarding | 147 | ~200 | ~$0.80 |
| p02 lookalike | 25 | ~60 | ~$0.25 |
| p03 adp_confirmed | 35 | ~80 | ~$0.30 |
| p04 high_intent | 35 | ~70 | ~$0.28 |
| p05 workmates | 35 | ~70 | ~$0.28 |
| p06 healthcare | 45 | ~90 | ~$0.36 |
| p07 education | 45 | ~90 | ~$0.36 |
| **Total** | **367** | **~660** | **~$2.60/run** |

Running weekly = ~$10/month for continuous lead discovery across all 7 verticals.
