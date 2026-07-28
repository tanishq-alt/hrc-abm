---
name: high-intent-lead-scout
title: HR Cloud High-Intent Lead Scout
description: "Use this skill to run the complete HR Cloud account-first lead-scout workflow. It discovers evidence-backed accounts, resolves company identity, interprets signals, applies hard ICP and confidence gates, rejects false positives, maps the buying committee, audits traceability, and exports only outreach-ready or nurture-ready records. It never uses copy quality to rescue a bad account and never auto-sends outreach."
category: Prospecting
---

# HR Cloud High-Intent Lead Scout

## Purpose

Build a small, defensible set of companies that HR Cloud should contact now.

The job is not to collect the largest possible list. The job is to identify
accounts where:

1. the company fits an HR Cloud segment;
2. a current, inspectable signal implies a workflow HR Cloud can solve;
3. the company identity is verified;
4. the signal is strong enough to justify action;
5. the relevant buyer can be found;
6. the record survives an adversarial quality audit.

## HR Cloud Domain

The scout operates inside these workflows:

- recruiting and applicant tracking;
- candidate communication and offer management;
- recruiting-to-onboarding handoff;
- new-hire forms, documents, tasks, and e-signatures;
- mobile, kiosk, frontline, and distributed onboarding;
- text-led AI onboarding with company-approved knowledge;
- employee records, permissions, documents, and directories;
- licenses, certifications, credentials, and renewal tracking;
- required training and workforce readiness;
- employee communication, recognition, mandatory reads, and surveys;
- time off, time clock, shift planning, performance, and asset handoff;
- workflow extensions around payroll and HRIS platforms.

A signal outside this domain is not relevant merely because the company is
large or growing.

## Default ICP

Configure these values, do not hard-code them:

- Geography: United States and Canada
- Employee range: 50 to 5,000
- Priority: 50%+ frontline/hourly, multi-location, distributed, seasonal, or
  high-hiring workforces
- Strong fit: 150+ annual hires or material compliance/credential complexity
- Priority verticals:
  - healthcare and home health;
  - manufacturing;
  - construction and field services;
  - education;
  - retail and hospitality;
  - staffing;
  - logistics;
  - other frontline-heavy organizations.
- Optional motions:
  - nonprofit;
  - government and public sector;
  - professional services.

## Inputs

Required:

- vertical or segment;
- geography;
- target account count;
- allowed signal playbooks;
- minimum ICP threshold;
- maximum signal age by signal type;
- source and scraping configuration.

Optional:

- state or region;
- known customer seed list;
- known competitor list;
- current customer and active-pipeline suppression list;
- product focus;
- campaign objective;
- minimum employee count;
- procurement-only or ADP-only mode.

## Outputs

For each candidate account return:

```yaml
account_id:
company_name:
canonical_domain:
parent_company:
facility_or_subsidiary:
vertical:
employee_count:
locations:
workforce_type:
icp_score:
intent_score:
evidence_confidence_score:
contactability_score:
composite_score:
tier:
hard_gate_status:
hard_gate_reason:
primary_signal:
signal_subtype:
signal_date:
signal_freshness:
signal_strength:
signal_confidence:
signal_safe_to_mention:
why_now:
business_implication:
primary_hrcloud_product:
secondary_hrcloud_product:
evidence:
negative_evidence:
false_positive_reason:
champion_titles:
economic_buyer_titles:
influencer_titles:
blocker_titles:
recommended_action:
audit_status:
audit_flags:
```

Every positive claim must be traceable to at least one evidence object.

## Execution State Machine

### State 0: Lock the brief

Restate:

- WHO: company segment and personas;
- WHAT: hard and soft filters;
- WHY: signal-led motion;
- SIZE: target number of passing accounts;
- FRESHNESS: maximum ages by signal type.

Push back on vague requests such as "find companies that need onboarding."
Require an observable signal thesis.

### State 1: Size and source candidates

Run a cheap sizing pass before expensive research.

Candidate discovery may use:

- company-hosted PDFs;
- careers pages and ATS pages;
- public handbooks;
- official RFP portals;
- government procurement systems;
- licensing portals;
- official press releases;
- job postings;
- customer and competitor review sites;
- public event or community data;
- closed-won lookalikes;
- champion moves.

Discovery sources create candidates. They do not automatically prove the
claim.

### State 2: Resolve company identity

Call `domain-entity-resolver`.

No account proceeds without one of:

- `verified`;
- `verified_parent_only`;
- `facility_no_unique_domain`, with a verified parent and facility identity.

`unresolved` accounts stay in a research queue and cannot be Tier 1 or Tier 2.

### State 3: Build the evidence ledger

Call `evidence-sourcer`.

Store exact excerpts, source URLs, observed dates, event dates, evidence tiers,
claim types, and source ownership.

Do not reduce evidence to a vague summary.

### State 4: Interpret each signal

Call `signal-interpreter`.

The interpreter must remain pure. It returns meaning, strength, confidence,
relevance, freshness, why-now, product relevance, and what not to assume.

It does not assign a tier.

### State 5: Try to disprove the account

Before scoring, search for negative evidence:

- current HR Cloud customer;
- active deal;
- vendor or partner;
- competitor;
- company below the hard size floor;
- no employees;
- franchise or facility with no centralized HR ownership;
- irrelevant hiring;
- old or closed RFP;
- current modern workflow that already solves the exact problem;
- duplicate parent/facility;
- signal attached to another legal entity;
- job aggregator content with no official confirmation;
- explicit "no longer accepting bids" or awarded contract;
- current HR leader no longer employed.

A scout that only looks for confirming evidence is not reliable.

### State 6: Qualify the account

Call `account-qualifier`.

Score four concepts separately:

1. ICP fit;
2. pain-bearing intent;
3. evidence confidence;
4. contactability.

Then apply hard gates and tier floors.

### State 7: Map the buying committee

Only after the account passes.

Call `buying-committee-mapper`.

For Tier 1:

- one champion;
- one economic buyer;
- optional evaluator/influencer;
- optional blocker;
- maximum five contacts.

For Tier 2:

- one champion first;
- enrich the economic buyer only when the account is upgraded or selected for
  ABM.

Never enrich dozens of contacts at a weak account.

### State 8: Audit

Call `lead-quality-auditor`.

Any failed audit must be rewritten, downgraded, moved to research, or
disqualified.

### State 9: Route

Call `activation-router`.

This skill may produce Apollo-ready records and outreach context. It never
auto-sends.

## Tier Rules

### Tier 1: Outreach-ready

Must pass all:

- composite score at or above configured threshold;
- ICP score above its independent floor;
- intent score above its independent floor;
- confidence above its independent floor;
- verified identity;
- current signal;
- at least one Tier A or Tier B evidence source for the central claim;
- relevant champion found;
- no hard gate;
- audit passed.

### Tier 2: Research or semi-personalized

- strong fit;
- moderate signal;
- identity verified;
- confidence acceptable;
- one missing element, usually corroboration or economic buyer;
- cannot be promoted until the missing element is resolved.

### Tier 3: Nurture or monitor

- fit may be acceptable;
- no current pain-bearing signal;
- no cold outreach;
- set a recheck date based on likely signal cadence.

### Disqualified

- hard gate;
- wrong company;
- unresolved identity;
- false-positive evidence;
- non-ICP;
- current customer or partner in a net-new motion;
- signal cannot support a relevant HR Cloud workflow.

## Batch Rules

- Companies first, people second.
- Pilot any new scraper or AI classifier on 10 accounts.
- If more than 20% of a source's records fail audit, pause that source.
- If more than 30% of a signal class is stale, change the query or freshness
  window.
- Do not pad a cohort to meet a requested number.
- Preserve rejected records with reasons for future query improvement.

## Hard Rules

- MUST separate fit, intent, confidence, and contactability.
- MUST retain exact evidence.
- MUST search for negative evidence.
- MUST use signal-specific freshness.
- MUST verify entity identity before scoring.
- MUST audit before export.
- NEVER promote an account on composite score alone.
- NEVER assume pain from industry alone.
- NEVER treat a modern HRIS as an automatic disqualifier.
- NEVER enrich contacts before the account gate.
- NEVER auto-send outreach.
- NEVER invent missing evidence.

## What Good Looks Like

A reviewer can open any Tier 1 row and answer:

- Why this company?
- Why now?
- What exact evidence proves it?
- What could make the inference wrong?
- Which HR Cloud workflow fits?
- Who owns that workflow?
- Why is the record safe to activate?

If any answer requires guessing, the account is not Tier 1.
