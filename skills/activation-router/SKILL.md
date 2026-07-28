---
name: activation-router
title: HR Cloud Lead Activation Router
description: "Use this skill after qualification and audit to route HR Cloud accounts into Apollo-ready outreach, research, nurture, procurement, owner follow-up, or suppression. It prepares evidence-safe context and buying-committee fields but never auto-sends."
category: Outreach
---

# HR Cloud Lead Activation Router

## Purpose

Turn an approved account record into the correct next action.

The router does not decide whether the lead is good. It trusts the qualifier
and auditor.

## Routes

### Tier 1: ABM Ready

- manual review required;
- champion and economic buyer;
- separate angle by persona;
- activate within the signal's SLA;
- include evidence-safe context;
- no auto-send.

### Tier 2: Research or Semi-Personalized

- champion only;
- one missing activation requirement;
- create research task;
- do not call it Tier 1;
- optional semi-personalized sequence only when allowed.

### Tier 3: Nurture

- no cold outreach;
- add monitoring date;
- subscribe to signal watch;
- content or low-touch nurture.

### Procurement

- route to RFP workflow;
- preserve solicitation number, deadline, requirements, and owner;
- do not run generic outbound.

### Existing Relationship

- route to deal owner, CSM, or prior relationship owner;
- do not create a duplicate sequence.

### Suppressed

- current customer;
- partner;
- competitor;
- DNC;
- active opportunity;
- invalid identity.

## Apollo Export Fields

Recommended:

```text
company_name
canonical_domain
parent_company
facility_or_subsidiary
vertical
employee_count
account_tier
icp_score
intent_score
confidence_score
contactability_score
primary_signal
signal_subtype
signal_date
signal_strength
signal_confidence
signal_safe_to_mention
why_now
evidence_1_url
evidence_1_excerpt
evidence_1_tier
evidence_2_url
evidence_2_excerpt
negative_evidence
primary_hrcloud_product
secondary_hrcloud_product
champion_title_options
economic_buyer_title_options
recommended_sequence
recommended_action
research_gap
audit_status
audit_flags
```

Contact exports add:

```text
first_name
last_name
title
buying_role
email
email_status
linkedin_url
relationship_strength
contact_inclusion_reason
persona_angle
likely_objection
```

## Evidence-Safe Context

Separate:

- `internal_signal_context`: may include tracking and intent;
- `safe_outreach_context`: only public or directly volunteered facts.

Do not expose:

- website visit;
- ad click;
- profile view;
- email opens;
- anonymous intent;
- IP tracking.

## LinkedIn Rule

Default connection request: blank.

Do not generate a personalized connection note merely because the repo can.
Personalized DMs may follow acceptance when justified.

## Multi-Thread Rule

Tier 1 accounts may have:

- champion message focused on workflow;
- economic buyer message focused on scale, risk, and standardization;
- evaluator message focused on data, integration, and governance.

Never send the same message to all contacts.

## Timing

Suggested:

- direct hand-raise: same day;
- active RFP: immediate procurement action;
- event: within 48 to 72 hours;
- new leader: days 14 to 45;
- hiring cluster: within one to two weeks;
- expansion: within two to four weeks;
- champion move: days 14 to 45;
- manual-process evidence: activate when paired with a current trigger, or run a
  lower-priority evidence-led campaign.

## Approval

Manual approval required for:

- Tier 1;
- senior executives;
- named customer proof;
- competitor displacement;
- healthcare compliance;
- procurement;
- multiple contacts at one account;
- any low-confidence outreach context.

## Hard Rules

- No auto-send.
- No duplicate active sequence.
- No contact export without account pass.
- No unsafe signal in outreach fields.
- No generic cold outreach for procurement.
- No Tier 3 cold sequence.
