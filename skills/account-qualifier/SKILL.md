---
name: account-qualifier
title: HR Cloud Account Qualifier
description: "Use this skill to qualify evidence-backed HR Cloud accounts after signal interpretation. It independently scores ICP fit, pain-bearing intent, evidence confidence, and contactability; applies hard gates and tier floors; prevents composite-score inflation; and produces an auditable tier and rejection reason."
category: Prospecting
---

# HR Cloud Account Qualifier

## Purpose

Decide whether an account deserves:

- immediate ABM outreach;
- one more research step;
- nurture and monitoring;
- disqualification.

The qualifier consumes interpreted evidence. It does not search for evidence
and does not write outreach.

## Why the Current Composite Model Needs a Guardrail

A total score can be misleading.

Example:

- excellent firmographic fit;
- weak or stale signal;
- low-confidence evidence;
- no buyer.

A naïve total may still cross Tier 1. This skill prevents that by enforcing
independent minimums.

## Scoring Model

Total: 100 points.

### A. ICP Fit: 0 to 35

- priority vertical: 0 to 8;
- employee range: 0 to 7;
- frontline/distributed/multi-location complexity: 0 to 7;
- hiring or workforce volume: 0 to 5;
- geography: 0 to 3;
- product-workflow match: 0 to 5.

### B. Pain-Bearing Intent: 0 to 25

- signal directly reveals a problem: 0 to 8;
- signal is current: 0 to 5;
- why-now is concrete: 0 to 4;
- multiple independent or complementary signals: 0 to 4;
- product relevance is direct: 0 to 4.

### C. Evidence Confidence: 0 to 20

- source authority: 0 to 6;
- entity match: 0 to 4;
- date/status verification: 0 to 3;
- exact excerpt specificity: 0 to 3;
- contradiction resolved: 0 to 2;
- source independence: 0 to 2.

### D. Contactability and Buying Ownership: 0 to 20

- relevant champion title exists: 0 to 6;
- champion contact found: 0 to 4;
- economic buyer identifiable: 0 to 3;
- verified channel data: 0 to 3;
- centralized ownership likely: 0 to 2;
- no duplicate/current active touch: 0 to 2.

## Hard Gates

A hard gate overrides the total.

Default hard gates:

- company identity unresolved;
- no real employer entity;
- current HR Cloud customer in a net-new campaign;
- active opportunity already owned, unless routed to owner;
- competitor;
- vendor or implementation partner in a prospect campaign;
- below configured employee floor without an approved experiment;
- outside approved geography;
- no HR Cloud-relevant workflow;
- central signal proven false;
- active RFP already awarded or closed;
- only stale signals;
- do-not-contact or suppression;
- facility cannot buy and no parent owner can be resolved.

Do not hard-gate merely because a modern HRIS is present.

## Penalties

Penalties affect the total but should not replace hard gates.

Suggested:

- only Tier D evidence: `-20`;
- identity verified only at parent with weak facility link: `-5`;
- one weak discovery source: `-10`;
- signal aging: `-5` to `-15` based on type;
- contradictory evidence unresolved: `-10`;
- no exact excerpt: `-8`;
- no champion found: `-10`;
- likely decentralized/franchise ownership: `-8`;
- suspected duplicate: `-15`;
- current modern HRIS that clearly solves the exact workflow: `-15`;
- generic funding with no HR implication: no intent points, not an extra penalty.

## Modern HRIS Treatment

Classify the verified system:

1. `integration_fit`
2. `workflow_extension_fit`
3. `possible_displacement`
4. `exact_workflow_already_solved`
5. `unknown`

Only category 4 should materially reduce qualification, and only with evidence.

ADP, Workday, UKG, Paylocity, Paycom, Paycor, or another system may increase
buying maturity and integration relevance.

## Tier Floors

### Tier 1

All required:

- total score >= 80;
- ICP fit >= 26;
- intent >= 17;
- confidence >= 14;
- contactability >= 12;
- at least one Tier A or authoritative Tier B evidence object for the central
  claim;
- identity status not `unresolved`;
- signal is fresh or currently active;
- champion found;
- no hard gate;
- audit passed.

### Tier 2

All required:

- total score 65 to 79;
- ICP fit >= 23;
- intent >= 11;
- confidence >= 11;
- identity verified;
- no hard gate.

Typical missing item:

- second signal;
- economic buyer;
- fresh confirmation;
- source upgrade.

Tier 2 must carry a `next_research_action`.

### Tier 3

- total score 45 to 64;
- fit may be acceptable;
- intent or confidence below activation floor;
- nurture or monitor only;
- recheck date required.

### Disqualified

- hard gate;
- total below 45;
- no relevant workflow;
- false-positive evidence;
- unresolved identity after allowed retries.

## Vertical Adjustments

### Healthcare

Boost:

- multi-state licenses;
- credential expirations;
- mobile/frontline hiring;
- home health, hospice, SNF, behavioral, staffing;
- multiple offices;
- high caregiver hiring.

Do not infer manual credential tracking solely from license requirements.

### Manufacturing

Boost:

- multiple plants;
- hourly workforce;
- safety training;
- paper forms;
- expansion;
- shift hiring;
- asset handoff.

### Education

Boost:

- seasonal hiring;
- district or multi-campus structure;
- teacher certifications;
- active RFP;
- summer onboarding surge.

### Construction and Field Services

Boost:

- project-based hiring;
- job-site onboarding;
- certification and safety requirements;
- rehires;
- mobile workforce.

### Retail and Hospitality

Boost:

- new locations;
- seasonal frontline hiring;
- no corporate email;
- high turnover;
- distributed communication.

### Government

Require:

- procurement path;
- active solicitation;
- budget or award timing;
- buying authority.

Do not score generic public-sector fit as intent.

## Output

```yaml
icp_score:
intent_score:
confidence_score:
contactability_score:
penalties:
total_score:
hard_gate_status:
hard_gate_reason:
tier:
tier_floor_checks:
missing_activation_requirement:
next_research_action:
recheck_date:
qualification_explanation:
```

## Calibration

Every month:

- compare Tier 1 and Tier 2 positive replies;
- compare false-positive reasons;
- inspect score distributions by source and vertical;
- reduce weights for noisy signals;
- increase hard gates for recurring failure modes;
- never change thresholds solely to hit a lead-count target.

## Hard Rules

- Composite score never overrides a failed floor.
- Modern HRIS is not an automatic disqualifier.
- One Tier A source can be sufficient for a narrow claim.
- Three syndicated sources count as one.
- No contact enrichment score when no contact was actually found.
- No Tier 1 without a buyer and current evidence.
