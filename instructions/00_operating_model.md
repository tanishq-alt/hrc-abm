# HR Cloud GTM Intelligence — Operating Model

## The Core Premise

This toolkit implements the **HR Cloud GTM Intelligence Playbook** — a system for finding companies with genuine HR software buying intent using verifiable evidence, not guesswork.

The weak version of this project produces thousands of companies with guessed domains, stale job posts, and vague "intent." That data wastes sales capacity.

This system only outputs leads that pass:
1. **Evidence quality gate** — Tier A or B source (not just job aggregators)
2. **Domain verification** — 7-step canonical domain protocol
3. **Scoring threshold** — total_score ≥ 65 (typically only Tier 1/2 go to outreach)

---

## The 4 Evidence Tiers

Every piece of evidence in this system is classified by tier before scoring:

| Tier | Source Type | Reliability | Use |
|------|-------------|-------------|-----|
| **A** | Company's own domain — handbook PDF, careers page, HR policy doc | Very High | Sufficient alone for "confirmed" |
| **B** | Reputable independent — state gov portal, SAM.gov, CMS database, county job board | High | Combine with A for confirmed; alone = "strongly likely" |
| **C** | Job aggregator, review site, news article | Medium | Directional only — confirm with A or B |
| **D** | Reddit, Glassdoor, social media, anonymous forum | Low | Discovery only — never standalone proof |

**Hard rule**: Tier C alone = verification queue (not outreach-ready). Tier D alone = reject.

---

## The 7-Step Domain Verification Protocol

Implemented in `scrapers/shared/verifier.py`. Run on every URL before saving a record:

1. **Extract netloc** — parse URL, strip `www.`
2. **Apply manual corrections** — ATS subdomains (lever.co, greenhouse.io, workforcenow.adp.com) → actual employer domain
3. **Check CDN/generic hosts** — S3, HubSpot CDN, WordPress, Squarespace, Netlify → mark `facility_no_unique_domain`
4. **Check job boards** — Indeed, LinkedIn, ZipRecruiter, Greenhouse → mark `unresolved`
5. **Collapse to root domain** — remove subdomains except k12.XX.us school districts
6. **Flag parent/holding companies** — domains containing "holdings", "group", "capital", "ventures" → mark `verified_parent_only`
7. **Return verified** — company has a real, unique, employer domain

**Output**: `(canonical_domain, domain_status)` tuple. Only `verified` status passes quality gate.

---

## ADP Evidence Taxonomy

ADP is the most common incumbent in HR Cloud's competitive displacement plays. Evidence levels matter:

| Level | What it proves | Status |
|-------|----------------|--------|
| **A — Confirmed** | Official company page names ADP; `workforcenow.adp.com/[subdomain]` tenant; handbook references ADP | `adp_status = confirmed` |
| **B — Strongly Likely** | Two independent Level C signals; company careers page (not aggregator) requires ADP proficiency | `adp_status = strongly_likely` |
| **C — Directional** | Job aggregator listing requiring "ADP experience"; G2/Capterra review; "ADP preferred" language | Never confirms alone |

**Critical scope rule**: A `workforcenow.adp.com` tenant URL proves ADP Workforce Now use for the **recruiting/onboarding module only** — it does NOT confirm payroll scope. Never claim payroll confirmation from a tenant URL alone. Set `adp_product_or_scope = "ADP Workforce Now (recruiting module only)"`.

---

## Scoring Model Overview

All 7 prompts use component scoring that sums to 100:

| Component | Points | What it measures |
|-----------|--------|-----------------|
| Signal/evidence strength | 25-35 | How strong and direct is the evidence of buying intent? |
| Commercial fit | 15-25 | Size, industry, and product match |
| Evidence quality | 15-25 | Tier A evidence scores higher than Tier C |
| Timing | 10-15 | How recent and urgent is the signal? |
| Uniqueness | 5-10 | Is this already in our pipeline? |

**Qualification thresholds** (applies to all prompts):
- **85-100**: Tier 1 — outreach-ready immediately
- **75-84**: Tier 2 — outreach with qualification step
- **65-74**: Verification queue — needs one more confirming signal
- **< 65**: Reject — insufficient evidence

---

## The 7 Prompts and When to Use Each

| Prompt | Use When | Primary Source |
|--------|----------|----------------|
| 1 — Manual Onboarding | Regular discovery (weekly) | DDG `filetype:pdf "new hire packet"` |
| 2 — Lookalike | After getting new customer wins | Seed DNA model → DDG candidate queries |
| 3 — ADP Confirmed | Building displacement pipeline | Job posting evidence, ADP tenant URLs |
| 4 — High Intent | Monitoring buying signals | OSHA, USAspending, acquisition news, G2 |
| 5 — Workmates | Expanding into comm/engagement | Frontline comm gap signals |
| 6 — Healthcare | Healthcare vertical focus | CMS, NPPES, state licensing lists |
| 7 — Education | Education vertical focus | NCES, .k12 domains, Head Start database |

---

## Underused Official Sources (Tier A/B)

These sources are often overlooked but produce the highest-quality signals:

| Source | URL | Best For |
|--------|-----|----------|
| SAM.gov | sam.gov/search | Federal contract awards → hiring surges |
| USAspending.gov | usaspending.gov | Contract awardees needing to scale staff |
| CMS Care Compare | medicare.gov/care-compare | SNF/home health deficiency pressure |
| CMS data.cms.gov | data.cms.gov | Provider lists, deficiency reports |
| OSHA Establishment Search | osha.gov/establishment-search | Violation pressure → HR reform trigger |
| DOL Wage/Hour | dol.gov/agencies/whd | Enforcement → compliance urgency |
| NPPES/NPI Registry | npiregistry.cms.hhs.gov | Healthcare employer identification |
| HHS OIG Exclusions | oig.hhs.gov/exclusions | Healthcare screening gap signal |
| NCES CCD | nces.ed.gov/ccd | K-12 district employee counts |
| Head Start ECLKC | eclkc.ohs.acf.hhs.gov | Head Start grantee directory |
| NLRB Cases | nlrb.gov/cases | Union complexity signals |
| Grants.gov | grants.gov | Grant awardees about to hire |

---

## Common False Positives and How to Handle Them

### Patient paperwork (healthcare searches)
**Problem**: "bring completed paperwork" surfaces patient intake forms.
**Fix**: Check for `employee|HR|new hire` context before scoring. If document is addressed to "patients" or "clients", discard.

### Vendor / consultant pages
**Problem**: HR software vendors write about manual onboarding as a pain point.
**Fix**: Check `is_employer_page()` — reject pages with "our platform", "free trial", "pricing" language.

### ATS domain confusion
**Problem**: `boards.greenhouse.io/[company]` looks like a company domain.
**Fix**: `verifier.py` DOMAIN_CORRECTIONS maps these to the actual employer domain.

### Large enterprise false matches
**Problem**: Fortune 500 companies appear in searches but already have Workday/Oracle.
**Fix**: Check SKIP_DOMAINS list; look for `workday|oracle|sap successfactors` in page text before scoring.

---

## Operating Schedule

| Prompt | Recommended Frequency | Rationale |
|--------|----------------------|-----------|
| 1 Manual Onboarding | Weekly | New PDFs get indexed constantly |
| 2 Lookalike | After new customer wins | DNA model needs fresh seeds |
| 3 ADP Confirmed | Daily | Job postings refresh daily |
| 4 High Intent | Daily | Regulatory events and acquisition news break daily |
| 5 Workmates | Weekly | Frontline comm signals are slower-moving |
| 6 Healthcare | 2x/week | CMS surveys and caregiver hiring are time-sensitive |
| 7 Education | Weekly in Jan-Mar; daily in Jun-Aug | Seasonal surge timing |
