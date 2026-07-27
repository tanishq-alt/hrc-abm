# HR Cloud ABM Scraper

A signal-driven, account-based marketing intelligence engine for HR Cloud. Not a generic scraper — an end-to-end ABM pipeline that discovers accounts, scores them on a composite ICP model, maps the buying committee, and generates personalized, evidence-specific outreach for each stakeholder.

> **Rule**: Every outreach claim must be traceable to a verified signal. No assumed pain. No generic openers. No spray and pray.

---

## How It Works

```
Signal Discovery → ICP Scoring → Composite Score → Tier Classification
       ↓                                                     ↓
  Evidence Tiers                                   Buying Committee Map
  (A / B / C / D)                                  (Champion → Econ Buyer)
       ↓                                                     ↓
Domain Verification                           Personalized Outreach Package
(7-step protocol)                             (Email 1/2/3 + LinkedIn note)
       ↓                                                     ↓
                    Apollo.io CSV Export
```

---

## Run the Pipeline

```bash
pip install -r requirements.txt
cp .env.example .env

# Single vertical
python3 pipeline/run.py --vertical healthcare --state TX
python3 pipeline/run.py --vertical education --state FL --min-score 60

# All verticals
python3 pipeline/run.py --vertical all --max-accounts 200

# Output formats
python3 pipeline/run.py --vertical healthcare --output apollo      # Apollo import CSV
python3 pipeline/run.py --vertical healthcare --output sequences   # Full email sequences
python3 pipeline/run.py --vertical healthcare --output all         # Everything
```

**Output files** land in `data/`:
- `abm_accounts_[vertical]_[timestamp].csv` — scored account list
- `apollo_import_[vertical]_[timestamp].csv` — Apollo.io ready import
- `sequences_[vertical]_[timestamp].csv` — full 3-email + LinkedIn sequences

---

## The 5 Verticals

| Vertical | Target | Primary Signals | Sweet Spot |
|----------|--------|-----------------|------------|
| `healthcare` | Home health, hospice, SNF, assisted living, behavioral health | PDF new hire packets, CMS deficiencies, caregiver hiring surges | 50-500 caregivers, multi-site |
| `education` | K-12 districts, charter networks, Head Start, community colleges | PDF packets on .k12 domains, seasonal hiring, RFPs | 200-2000 staff, annual surge |
| `manufacturing` | Plant-floor employers, logistics, distribution, construction | OSHA citations, ADP job posts, acquisition signals | 100-2000 hourly workers |
| `nonprofit` | Social services, faith-based, human services, community orgs | PDF packets on .org domains, grant awards, first HR hire | 50-500, lean HR team |
| `government` | County, municipality, transit, special districts | RFPs, SAM.gov awards, ADP job posts, PDF packets | 50-2000, procurement-driven |

---

## ICP Scoring Model (0-100)

Every account is scored across 4 dimensions before outreach is generated:

| Dimension | Points | What It Measures |
|-----------|--------|-----------------|
| **Firmographic fit** | 0-30 | Industry match, employee size (50-2000 sweet spot), multi-location, US-based |
| **Technographic fit** | 0-25 | ADP/legacy confirmed, paper evidence, no modern HRIS detected |
| **Behavioral/intent** | 0-25 | Signal tier quality, signal count, freshness |
| **Buying trigger** | 0-20 | New HR leader, acquisition, regulatory pressure, grant funding, RFP |

**Penalties applied on top:**
- Single source only: -10
- No Tier A or B evidence: -15
- Unverified domain: -20
- All signals stale (>180 days): -8
- Modern HRIS confirmed (Workday/UKG/SAP): -30

---

## Account Tiers

| Tier | Score | Action |
|------|-------|--------|
| **Tier 1** | ≥ 80 | Outreach-ready immediately. Personalized 1:1 sequence. Multi-thread: champion + economic buyer within 48 hours. |
| **Tier 2** | 60-79 | Semi-personalized sequence. Champion only. Find one more confirming signal before Tier 1 upgrade. |
| **Tier 3** | 40-59 | Nurture only. Re-score in 30 days. Do NOT send cold outreach. |
| **Disqualified** | <40 or hard gate | Drop. Log rejection reason. Hard gates: no Tier A/B, confirmed modern HRIS, <50 employees. |

---

## Evidence Tiers

| Tier | Source | Weight |
|------|--------|--------|
| **A** | Company-hosted PDF, company careers page, company handbook | 1.0× |
| **B** | SAM.gov, CMS database, state licensing portal, job posting on company domain | 0.8× |
| **C** | Job aggregator (Indeed/LinkedIn), news article, press release | 0.5× |
| **D** | Reddit, Glassdoor, social media | 0.1× — discovery only, never standalone |

---

## Buying Committee Mapping

For every Tier 1 and Tier 2 account, the engine maps:

| Role | Who | Priority |
|------|-----|----------|
| **Champion** | HR Director, VP HR, CHRO, Director of People | 1st — initiates the evaluation |
| **Economic Buyer** | CFO, CEO, COO, Administrator | 2nd — approves budget |
| **Influencer** | HR Manager, HR Coordinator, Payroll Specialist | 3rd — daily user |
| **Blocker** | IT Director, Legal/Compliance | Prepare objection response |

Each persona gets their own: title options, key concerns, outreach hook, likely objection, and LinkedIn note.

---

## Personalization Rules (Non-Negotiable)

1. **Every opener cites specific verified evidence** — "Found your new hire packet on your website" not "I noticed you might struggle with onboarding"
2. **No assumed pain** — if there's no evidence, don't claim the pain
3. **One message, one pain point** — pick the strongest signal, build the whole message around it
4. **Banned phrases**: "I hope this finds you well", "I wanted to reach out", "touching base", "circling back", "quick question"
5. **Social proof must match vertical** — healthcare proof for healthcare accounts, education proof for education accounts
6. **CTA must be specific and low-friction** — "15-min call this week" or "I'll send a 2-page overview" — never "let me know if interested"

---

## Outreach Sequence Structure

| Touch | Timing | What |
|-------|--------|------|
| Email 1 | Day 0 | Evidence-based opener + single value prop + low-friction CTA |
| LinkedIn | Day 2 | Personalized connection note referencing company specifically |
| Email 2 | Day 4 | Different angle + social proof from same vertical |
| Email 3 | Day 9 | Break-up — compress value to 2 sentences, keep door open |

---

## Domain Verification Protocol

All discovered domains pass through `scrapers/shared/verifier.py` — a 7-step protocol:
1. Extract netloc, strip `www.`
2. Apply manual corrections (ATS subdomains → employer domain)
3. Skip CDN/generic hosts (S3, WordPress, Squarespace)
4. Skip job boards (Indeed, LinkedIn, Greenhouse)
5. Collapse to root domain
6. Flag parent/holding company domains
7. Return `verified` / `verified_parent_only` / `facility_no_unique_domain` / `unresolved`

Only `verified` domains proceed past the quality gate.

---

## Repo Structure

```
hrcloud-abm-scraper/
│
├── engine/                         # ABM intelligence core
│   ├── icp.py                      # ICP scoring (firmographic + tech + behavioral + trigger)
│   ├── signals.py                  # Signal normalization, tier weighting, freshness decay
│   ├── scorer.py                   # Composite account scorer with penalty model
│   ├── committee.py                # Buying committee mapper (per vertical)
│   └── personalizer.py             # Evidence-to-outreach personalization engine
│
├── abm/                            # ABM output layer
│   ├── account.py                  # Full enriched Account dataclass
│   ├── tiers.py                    # Tier 1/2/3/Disqualified classification
│   └── apollo_export.py            # Apollo.io CSV formatter + sequence export
│
├── pipeline/
│   ├── run.py                      # Main CLI — runs full ABM pipeline per vertical
│   └── build_master.py             # Legacy: merge all scraper CSVs → MASTER.csv
│
├── scrapers/                       # Source scrapers (feed signals into engine)
│   ├── shared/                     # schema.py, ddg.py, fetcher.py, verifier.py
│   ├── p01_manual_onboarding/      # Prompt 1: paper onboarding signals
│   ├── p02_lookalike/              # Prompt 2: DNA-based lookalike finder
│   ├── p03_adp_confirmed/          # Prompt 3: ADP confirmed users
│   ├── p04_high_intent/            # Prompt 4: 18 signal families
│   ├── p05_workmates/              # Prompt 5: frontline comm gap
│   ├── p06_healthcare/             # Prompt 6: CMS/OSHA-driven healthcare
│   └── p07_education/              # Prompt 7: NCES/seasonal education
│
├── prompts/                        # 7 agent prompt specifications (markdown)
├── instructions/                   # Per-module how-to guides + operating model
├── scrapegraph/                    # ScrapeGraph cloud agent entrypoint
│
└── data/
    ├── nano_onboarding_MASTER.csv  # 78 verified manual onboarding companies
    ├── abm_accounts_*.csv          # ABM pipeline output (generated)
    ├── apollo_import_*.csv         # Apollo import files (generated)
    └── sequences_*.csv             # Email sequences (generated)
```

---

## GTM Principles Embedded

These are the principles the best GTM teams apply:

1. **Account-first, contact-second** — score the account before finding contacts
2. **Signal-based selling** — only reach out when evidence justifies it
3. **Multi-threaded outreach** — Tier 1 accounts get champion + economic buyer simultaneously
4. **Timing intelligence** — signals decay weekly; fresh signals score higher
5. **Rejection discipline** — fewer, better accounts beat more, weaker accounts
6. **Evidence-specific personalization** — every opener cites specific verified evidence
7. **One message, one pain** — pick the strongest signal, build around it
8. **Vertical social proof** — match the proof point to the account's industry
9. **Trigger-event sequences** — outreach triggered by events, not calendar
10. **Buying committee coverage** — a deal dies with only one contact

---

## Apollo Integration

The pipeline outputs Apollo-ready CSVs with:
- Pre-assigned sequence names (ABM Tier 1 Personalized / ABM Tier 2 Semi-Personalized)
- Personalized first lines per account (paste directly into Apollo custom fields)
- Champion and economic buyer titles for contact search
- Email subject A/B variants for testing

Import to Apollo: `Contacts → Import → Upload CSV → Map fields`
