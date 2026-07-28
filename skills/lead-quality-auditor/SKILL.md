---
name: lead-quality-auditor
title: HR Cloud Lead Quality Auditor
description: "Use this skill as the final adversarial gate before HR Cloud accounts are exported. It checks entity identity, claim traceability, source authority, signal freshness, contradiction, scoring floors, duplicate entities, buying ownership, product fit, and CSV integrity. It can downgrade, reject, or return a record for research but never silently fixes evidence."
category: Prospecting
---

# HR Cloud Lead Quality Auditor

## Purpose

Try to prove that each lead should not ship.

The auditor is independent from the scraper that found the record.

## Inputs

- enriched account;
- evidence ledger;
- signal interpretation;
- qualification result;
- buying committee;
- suppression data;
- intended output mode.

## Audit Result

```yaml
audit_status:
audit_score:
fatal_errors:
warnings:
downgrade_reason:
required_fix:
rejection_reason:
traceability_pass:
identity_pass:
freshness_pass:
confidence_pass:
persona_pass:
product_fit_pass:
export_integrity_pass:
```

Statuses:

- `pass`
- `pass_with_warning`
- `return_to_research`
- `downgrade`
- `reject`

## Fatal Checks

Reject or return to research when:

- canonical domain unresolved;
- evidence belongs to another entity;
- central claim has no exact excerpt;
- source URL missing;
- central signal is stale;
- RFP closed or awarded;
- duplicated account;
- company is current customer, partner, competitor, or suppressed;
- no HR Cloud-relevant workflow;
- Tier 1 lacks a champion;
- Tier 1 lacks an A/B evidence source;
- score floor failed;
- proof is contradicted by a newer source;
- generated fields contain invented facts.

## Traceability Audit

For every claim used in:

- score;
- tier;
- product mapping;
- why-now;
- personalization context;

verify that an evidence ID exists.

No orphan claims.

## Entity Audit

Confirm:

- canonical domain;
- parent/facility relationship;
- legal or operating entity;
- source ownership;
- dedupe key;
- buyer ownership.

## Freshness Audit

Use the signal-specific window.

Flag:

- old job post;
- old leadership move;
- expired RFP;
- outdated handbook;
- stale technology;
- closed facility;
- acquired or renamed entity.

## Evidence Audit

Check:

- Tier A/B requirement;
- duplicate/syndicated sources;
- search snippet reliance;
- claim-specific authority;
- exact excerpt;
- event date;
- contradiction;
- source accessibility.

## Scoring Audit

Recompute:

- ICP;
- intent;
- confidence;
- contactability;
- penalties;
- floor checks.

Detect:

- total score arithmetic errors;
- penalty applied twice;
- modern HRIS incorrectly treated as a hard negative;
- duplicate signals counted independently;
- contactability points awarded without a contact;
- Tier 1 assigned despite failed floor.

## False-Positive Audit

Ask:

- Could the evidence describe an optional process?
- Could it belong to volunteers or contractors?
- Could it be old?
- Could the company be a vendor?
- Could the job posting be duplicated?
- Could the technology be client-facing rather than internally used?
- Could the facility lack buying authority?
- Could the company already have a system solving the exact workflow?
- Could the signal belong to a parent or affiliate?
- Could the account be too small?

## Product-Fit Audit

The recommended product must be the shortest logical distance from the signal.

Examples:

- paper packet -> Onboard, not Workmates;
- candidate handoff -> Recruit + Onboard;
- licenses -> Credential Tracking;
- frontline communication -> Workmates;
- required training -> Train;
- ADP evidence without pain -> integration/extension hypothesis, not automatic
  Onboard pain.

## Buying-Committee Audit

- champion title relevant;
- economic buyer appropriate for company size;
- no unrelated contacts;
- no more than five;
- no active duplicate sequence;
- warm relationship surfaced first;
- role gaps explicit.

## Export Audit

- original rows preserved;
- canonical domain populated;
- evidence columns valid;
- tier and scores consistent;
- rejection reasons retained;
- no multiline CSV corruption;
- no duplicate headers;
- no hidden null placeholders;
- URLs not malformed.

## Sampling and Source Health

After every run:

- manually review all Tier 1;
- review 20% of Tier 2;
- review 5% of rejected accounts;
- calculate rejection by source;
- calculate false-positive rate by play;
- suspend a source when fatal error rate exceeds 20%;
- suspend a play when more than 30% of Tier 1 is downgraded.

## Audit Score

100 points:

- identity: 15;
- traceability: 20;
- source authority: 15;
- freshness: 10;
- interpretation discipline: 10;
- scoring correctness: 10;
- product fit: 8;
- buying committee: 7;
- export integrity: 5.

Thresholds:

- 90+: pass;
- 80 to 89: pass with warning;
- 70 to 79: downgrade or research;
- below 70: reject.

Fatal errors override score.

## Hard Rules

- Never silently manufacture missing evidence.
- Never improve a score to hit a target count.
- Never hide negative evidence.
- Never pass Tier 1 without manual review.
- Every rejection gets a normalized reason.
