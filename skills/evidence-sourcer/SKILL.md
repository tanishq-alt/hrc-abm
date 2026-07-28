---
name: evidence-sourcer
title: HR Cloud Evidence Sourcer
description: "Use this skill to discover and preserve claim-level evidence for HR Cloud lead scouting. It distinguishes discovery clues from proof, ranks sources by claim authority, captures exact excerpts and dates, detects duplicated or syndicated evidence, and produces a structured evidence ledger that downstream interpretation and scoring can audit."
category: Signals
---

# HR Cloud Evidence Sourcer

## Purpose

Find evidence another analyst can inspect and reproduce.

The output is not "the company probably uses paper." The output is:

- the exact source;
- the exact excerpt;
- the claim it supports;
- when the event happened;
- when it was observed;
- who owns the source;
- how authoritative the source is;
- what it does not prove.

## Evidence Object

```yaml
evidence_id:
company_name:
candidate_domain:
source_url:
source_title:
source_owner:
source_type:
evidence_tier:
claim_type:
exact_excerpt:
normalized_claim:
event_date:
observed_at:
fresh_until:
is_primary_source:
is_syndicated:
duplicate_group:
company_identity_match:
safe_to_quote:
safe_to_use_for_outreach:
supports:
contradicts:
limitations:
content_hash:
```

## Evidence Tiers

### Tier A: First-party or authoritative primary evidence

Examples:

- company-hosted employee handbook;
- company-hosted onboarding packet;
- company careers page;
- company ATS page;
- official company press release;
- official procurement document;
- official school district or government PDF;
- signed or issued public award;
- official licensing record.

Weight: strongest.

A single Tier A source may be enough for a narrow claim when identity and date
are clear.

### Tier B: Authoritative external evidence

Examples:

- SAM.gov;
- state procurement portal;
- CMS or state healthcare database;
- state licensing portal;
- government minutes;
- official grant record;
- job posting on the employer's verified ATS;
- regulatory filing.

Weight: strong.

### Tier C: Reputable secondary evidence

Examples:

- reputable news;
- trade publication;
- press-release wire;
- LinkedIn company post;
- Indeed or LinkedIn job listing when the company ATS is unavailable;
- review site with identifiable author and date.

Weight: moderate.

Use for discovery or corroboration. Do not let an aggregator prove a strong
claim alone when a primary source should exist.

### Tier D: Discovery-only evidence

Examples:

- Reddit;
- Glassdoor;
- generic social posts;
- forum comments;
- scraped snippets;
- listicles;
- SEO pages;
- anonymous complaints.

Weight: weak.

Tier D never stands alone for Tier 1 or Tier 2.

## Claim-Specific Authority

Source quality depends on the claim.

- A company handbook is strong for onboarding instructions.
- A state license portal is strong for credential requirements.
- A careers page is strong for current hiring.
- A review site is useful for dissatisfaction but weak for company-wide
  technology ownership.
- A job posting is useful for role demand and named tools, but it may not prove
  production use.
- An RFP is strong for active procurement only when status and deadline are
  current.

Do not apply one universal source score without considering claim type.

## Discovery Versus Proof

A discovery clue creates a research task.

Example:

> A Reddit user says their employer uses paper onboarding.

This is not enough. Search for:

- company-hosted onboarding forms;
- careers instructions;
- new-hire packets;
- handbook language;
- official job postings mentioning manual document handling;
- public procurement records.

If no stronger evidence exists, keep the record as a low-confidence discovery
lead or reject it.

## Sourcing Procedure

### Step 1: Generate claim-specific queries

For manual onboarding:

- `site:companydomain.com filetype:pdf "new hire packet"`
- `site:companydomain.com filetype:pdf "employment application"`
- `site:companydomain.com "bring completed forms"`
- `site:companydomain.com "print and complete"`
- `site:companydomain.com "fax" onboarding`
- `site:companydomain.com "new employee orientation packet"`

For ADP confirmation:

- `site:companydomain.com ADP`
- `site:companydomain.com/careers ADP`
- `site:jobs.* company ADP Workforce Now`
- `"company name" "ADP Workforce Now"`
- official partner or implementation case study.

For RFPs:

- `"human resources information system" RFP`
- `"employee onboarding" RFP`
- `"applicant tracking system" RFP`
- site filters for `.gov`, `.edu`, state procurement, SAM.gov.

For credentials:

- company job posts plus required licenses;
- official facility or state licensing data;
- public new-hire requirements;
- employee handbook renewal language.

### Step 2: Fetch the full source

Do not rely on search snippets when the source is accessible.

For PDFs, capture:

- title;
- issuing entity;
- publication date;
- page;
- exact excerpt;
- current status;
- deadline;
- amendments or awards.

### Step 3: Resolve source ownership

Confirm that:

- the domain belongs to the company or official entity;
- the ATS is linked from the company site;
- a PDF is not an old mirrored copy;
- a facility document belongs to the facility being scored;
- an RFP issuer matches the target organization.

### Step 4: Date the evidence

Store two dates:

- `event_date`: when the event happened;
- `observed_at`: when the scraper verified it.

When no event date exists, do not invent one.

### Step 5: Deduplicate evidence

Syndicated copies do not count as independent corroboration.

Use:

- canonical URL;
- title;
- excerpt similarity;
- content hash;
- originating press release;
- publication timestamps.

Group duplicates under one `duplicate_group`.

### Step 6: Capture limitations

Every evidence object states what it does not prove.

Example:

```text
The job posting names ADP Workforce Now as a required skill. This supports likely
ADP exposure but does not by itself prove the company currently runs ADP in
production.
```

### Step 7: Search for contradiction

Examples:

- a newer handbook replaces the old packet;
- the RFP has been awarded;
- the job is closed;
- the facility was acquired;
- the company moved to a modern onboarding platform;
- the signal belongs to a parent or affiliate;
- the HR leader left.

Store contradictions, do not hide them.

## Freshness Defaults

Configure by signal:

- website, pricing, event engagement: 1 to 7 days;
- active job posting: 14 to 45 days;
- leadership move: 14 to 90 days;
- hiring cluster: 30 to 60 days;
- funding or expansion: 30 to 120 days;
- RFP: active until deadline or award;
- handbook/manual process: valid until superseded, but reverify within 180 days;
- stable firmographics: reverify within 180 days;
- customer or technology evidence: reverify within 90 days.

## Quality Rules

- Exact excerpt required for the central claim.
- Source URL required.
- Company identity match required.
- Date required when available.
- Search snippet alone cannot produce high confidence.
- Multiple pages on the same root source are not automatically independent.
- One strong primary source can beat several weak secondary sources.
- Evidence must support a specific claim, not merely mention a keyword.
- Keyword presence is not intent.

## Output

Return:

- evidence ledger;
- strongest supporting evidence;
- strongest contradiction;
- source diversity;
- claim coverage;
- missing proof;
- recommended next query;
- source-level audit flags.
