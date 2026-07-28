---
name: signal-interpreter
title: HR Cloud Signal Interpreter
description: "Use this skill after identity resolution and evidence collection to interpret a raw business event, workflow clue, procurement record, technology clue, or intent signal. It returns relevance, meaning, strength, confidence, freshness, safe-to-mention status, why-now, product relevance, false-positive risks, and open questions. It is a pure interpretation layer: no scoring, tiering, CRM writes, contact enrichment, or outreach."
category: Signals
---

# HR Cloud Signal Interpreter

## Purpose

Convert evidence into a disciplined hypothesis.

The interpreter answers:

- What happened?
- Does it matter to HR Cloud?
- What workflow complexity might it create?
- How strong is the signal?
- How confident are we?
- Why now?
- What must not be assumed?
- Is the signal safe to mention?
- What question must be resolved before activation?

It does not decide whether to contact the company.

## Inputs

```yaml
company_name:
canonical_domain:
vertical:
icp_verdict:
signal_type:
signal_subtype:
event_details:
evidence_objects:
negative_evidence:
company_context:
account_history:
known_technology:
```

## Relevance Gate

Ask:

> Does this evidence create or reveal complexity in a workflow HR Cloud can
> credibly solve?

Relevant workflow categories:

- candidate and recruiting workflow;
- offer-to-onboarding handoff;
- new-hire forms and tasks;
- mobile/frontline onboarding;
- onboarding questions and guidance;
- credentials, licenses, and readiness;
- training and renewals;
- employee records and permissions;
- employee communication and recognition;
- time, shifts, performance, or asset handoff;
- integration or workflow gaps around payroll/HRIS.

If clearly no, return `not_relevant` and stop.

## Structured Output

```yaml
relevance_verdict:
clean_summary:
likely_meaning:
business_implication:
primary_product:
secondary_product:
signal_category:
signal_strength:
signal_strength_reason:
confidence:
confidence_reason:
freshness_status:
fresh_until:
why_now:
safe_to_mention:
safe_to_mention_reason:
what_not_to_assume:
false_positive_risks:
competitive_context:
open_questions:
```

## Signal Strength and Confidence Are Different

### Strength

How directly the signal indicates an active HR Cloud-relevant problem or buying
window.

### Confidence

How certain the interpretation is based on source authority, entity match,
specificity, and contradiction.

Examples:

- A current official RFP can be high strength and high confidence.
- A credible funding announcement may be medium strength and high confidence.
- An anonymous complaint may be medium apparent strength but low confidence.
- A company handbook that says "print, complete, and bring on Day 1" may be high
  confidence evidence of a manual process, but its strength depends on whether
  the document is current.

Never merge strength and confidence into one adjective.

## Signal Categories

Choose one:

- `direct_intent`
- `procurement`
- `workflow_pain`
- `growth`
- `leadership_change`
- `technology_change`
- `compliance_or_readiness`
- `relationship`
- `competitive_dissatisfaction`
- `content_or_event_engagement`
- `stable_fit`
- `noise`

## Strength Rules

### High

Examples:

- active RFP for ATS, HRIS, onboarding, employee engagement, or training;
- official current manual new-hire packet with clear paper/fax/in-person steps;
- direct inbound or prior relationship;
- champion moved to a strong-fit company;
- verified competitor dissatisfaction plus active evaluation;
- multiple relevant hiring roles plus expansion;
- explicit ADP workflow gap or integration requirement;
- licensing/credential process documented as manual and current.

### Medium

Examples:

- new HR leader with relevant mandate;
- hiring cluster;
- new locations;
- acquisition;
- verified ADP use without a documented pain;
- relevant technology change;
- role-specific pain inferred from strong company context;
- current job posting indicating manual coordination.

### Low

Examples:

- generic funding;
- one unrelated job post;
- broad company growth;
- old handbook;
- generic review;
- industry fit alone;
- modern HRIS use without evidence of a gap.

## Confidence Rules

### High

- central claim supported by Tier A or authoritative Tier B evidence;
- entity and date verified;
- no material contradiction;
- excerpt directly supports the claim.

### Medium

- claim supported by good secondary evidence;
- implication requires one reasonable inference;
- identity is verified;
- contradiction is absent or minor.

### Low

- discovery-only source;
- claim requires multiple inferences;
- date unclear;
- entity match uncertain;
- contradiction exists;
- source is syndicated or anonymous.

## Freshness

Apply signal-specific rules.

Do not classify a 179-day-old hiring post as "current" merely because a global
180-day limit permits it.

Return:

- `fresh`
- `aging`
- `stale`
- `timeless_but_needs_reverification`
- `unknown`

## Safe-to-Mention Rules

### Usually safe

- public job posting;
- public leadership announcement;
- official expansion;
- official RFP;
- company-hosted handbook or packet;
- public article or post;
- direct webinar participation;
- direct prior conversation.

### Background only

- website visit;
- ad click;
- profile view;
- email opens;
- third-party intent topic;
- inferred competitor research;
- anonymous community behavior.

The lead-scout record may retain background signals, but outreach must not
expose surveillance.

## Modern HRIS Rule

A modern HRIS is not inherently negative.

Interpret it as one of:

- mature buyer and integration fit;
- adjacent workflow opportunity;
- potential system-of-record with HR Cloud as workflow layer;
- displacement opportunity only when dissatisfaction is verified;
- low relevance when the exact target workflow is demonstrably solved.

Do not default to `noise` or disqualification.

## What Not to Assume

Always include at least one.

Examples:

- A job posting mentioning ADP does not prove production use.
- A paper packet may be optional rather than the primary onboarding process.
- A new HR leader does not prove budget.
- An RFP may have been amended or awarded.
- A license requirement does not prove expiration tracking is manual.
- A funding round does not prove HR technology priority.
- A negative review from one user does not prove company-wide dissatisfaction.
- A facility-level signal may not be owned by the parent HR team.

## Why-Now Discipline

Return a why-now only when concrete:

- RFP deadline;
- new role in first 90 days;
- active hiring cluster;
- facility opening;
- acquisition integration;
- seasonal hiring window;
- product launch;
- credential renewal cycle;
- current public process.

When no real timing exists, set `why_now: null`.

## Open Questions

Maximum five, ordered by activation impact.

Examples:

- Is the packet still the current onboarding method?
- Is HR centralized at the parent or facility?
- Does the company use ADP in production?
- Is the RFP still open?
- Who owns credential readiness?
- Does the current HRIS already cover this workflow?

## Hard Rules

- No tiers.
- No composite score.
- No contact enrichment.
- No CRM write.
- No outreach.
- No invented urgency.
- No hidden contradictions.
- No assumption that a keyword proves intent.
