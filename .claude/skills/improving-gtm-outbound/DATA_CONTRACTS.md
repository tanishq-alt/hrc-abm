# Data Contracts — Outcome CSV Schema

## Ingestion Input: Apollo/HubSpot Export

`ingest_outcomes.py` accepts raw exports from Apollo.io or HubSpot.
It normalises them to the canonical outcome schema below.

### Apollo export columns used (auto-detected):
- `Company` → company_name (lookup join)
- `Website` → canonical_domain (primary join key after normalisation)
- `Title` → contact_title
- `Email Sequence` → sequence_name
- `Sequence Step #` → sequence_step
- `Replied` → outcome = "reply" if "Yes"
- `Meeting Booked` → outcome = "meeting_booked" if "Yes"
- `Bounced` → outcome = "bounced" if "Yes"
- `Unsubscribed` → outcome = "unsubscribed" if "Yes"
- `Email Subject` → email_subject_used
- `Sent At` → outreach_date
- `Last Activity` → outcome_date

---

## Canonical Outcome Schema

File location: `data/learning/outcomes/YYYY-MM-DD_outcomes.csv`

| Field | Type | Source | Required | Notes |
|---|---|---|---|---|
| `outcome_id` | str | auto | yes | SHA-256 of canonical_domain+outreach_date+contact_title |
| `canonical_domain` | str | normalised from input | yes | Primary join key — strip www., lowercase |
| `company_name` | str | input | no | For human readability only |
| `outreach_date` | date (YYYY-MM-DD) | input | yes | Date first email was sent |
| `contact_title` | str | input | no | Exact title as used in Apollo |
| `contact_persona_role` | enum | derived | no | champion/economic_buyer/influencer/blocker/unknown |
| `sequence_name` | str | input | no | Apollo sequence name |
| `sequence_step` | int | input | no | Which step triggered the outcome |
| `outcome` | enum | input | yes | reply/meeting_booked/disqualified/bounced/unsubscribed/no_response |
| `outcome_date` | date (YYYY-MM-DD) | input | no | Blank for no_response |
| `days_to_outcome` | int | computed | no | outcome_date - outreach_date; null if no_response |
| `email_subject_used` | str | input | no | Actual subject line sent |
| `account_tier_at_send` | str | joined from Account CSV | yes | Tier 1/2/3/Disqualified at send time |
| `icp_score_at_send` | int | joined from Account CSV | no | 0-35 |
| `intent_score_at_send` | int | joined from Account CSV | no | 0-25 |
| `signal_type_at_send` | str | joined from Account CSV | no | Primary signal used |
| `vertical` | str | joined from Account CSV | yes | healthcare/education/manufacturing/nonprofit/government/utilities |
| `adp_status_at_send` | str | joined from Account CSV | no | confirmed/strongly_likely/not_found/not_checked |
| `hris_fit_category_at_send` | str | joined from Account CSV | no | integration_fit/workflow_extension_fit/possible_displacement/unknown |
| `campaign_batch` | str | ingest arg | yes | Identifies which upload batch this row came from |

### Outcome enum values

| Value | Meaning |
|---|---|
| `reply` | Prospect replied (positive, neutral, or negative) |
| `meeting_booked` | Calendar meeting confirmed |
| `disqualified` | Prospect replied and disqualified (wrong fit, current customer, etc.) |
| `bounced` | Hard bounce (invalid email) |
| `unsubscribed` | Opted out |
| `no_response` | Sequence completed with no reply |

### Contact persona role derivation

`ingest_outcomes.py` calls `engine.personalizer.infer_persona_role(contact_title)`.
If the title is not in TITLE_TO_ROLE, falls back to `"unknown"`.

---

## Proposal Schema

File location: `data/learning/proposals/vNNN_{description}.yaml`

```yaml
version: "001"
created_at: "2026-07-31T14:00:00Z"
status: "pending_review"   # pending_review | approved | rejected | superseded
description: "Increase healthcare Tier 1 ICP floor from 26 to 28"

hypothesis:
  observation: >
    Healthcare Tier 1 accounts with icp_score 26-27 show 1.2% meeting rate
    vs 4.8% for accounts with icp_score ≥ 28 (n=47 and n=62 respectively).
  proposed_change:
    file: "engine/scorer.py"
    parameter: "TierFloorCheck icp_score for Tier 1"
    current_value: 26
    proposed_value: 28
    change_type: "tier_floor_adjustment"   # copy_tuning|query_addition|signal_weight|tier_floor|hard_gate

supporting_evidence:
  segments:
    - vertical: "healthcare"
      account_tier: "Tier 1"
      icp_score_bucket: "26-27"
      sends: 47
      replies: 3
      meetings: 1
      reply_rate_pct: 6.4
      meeting_rate_pct: 1.2
    - vertical: "healthcare"
      account_tier: "Tier 1"
      icp_score_bucket: "28+"
      sends: 62
      replies: 12
      meetings: 3
      reply_rate_pct: 19.4
      meeting_rate_pct: 4.8

backtest:
  historical_periods: 3
  estimated_lift_pct: 8.2
  p_value: 0.04
  sample_size: 47
  confidence: "medium"   # high (p<0.01, n≥100) | medium (p<0.05, n≥30) | low

canary:
  status: "not_started"   # not_started | running | completed | rolled_back
  canary_start_date: null
  canary_pct: 20
  min_cycles: 2
  canary_meeting_rate: null
  control_meeting_rate: null

human_review:
  reviewer: null
  reviewed_at: null
  decision: null   # approved | rejected
  notes: null

diff_file: null   # path to generated diff after promote_learning.py runs
```

---

## Analysis Output Schema

File location: `data/learning/analysis/YYYY-MM-DD_analysis.json`

```json
{
  "generated_at": "2026-07-31T14:00:00Z",
  "total_sends": 247,
  "total_replies": 34,
  "total_meetings": 11,
  "overall_reply_rate_pct": 13.8,
  "overall_meeting_rate_pct": 4.5,
  "segments": [
    {
      "dimensions": {"vertical": "healthcare", "account_tier": "Tier 1", "signal_type": "pdf_new_hire_packet"},
      "sends": 52,
      "replies": 14,
      "meetings": 6,
      "reply_rate_pct": 26.9,
      "meeting_rate_pct": 11.5,
      "vs_baseline_reply_pct": 13.1,
      "vs_baseline_meeting_pct": 7.0,
      "signal": "above_baseline",
      "min_sample_met": true
    }
  ],
  "hypotheses_generated": 2,
  "proposal_files": [
    "data/learning/proposals/v001_healthcare_icp_floor.yaml"
  ]
}
```

---

## Audit Trail Schema

File location: `data/learning/audit/YYYY-MM-DD_audit.jsonl`
(One JSON object per line, append-only)

```json
{"ts": "2026-07-31T14:00:00Z", "script": "ingest_outcomes.py", "action": "ingest", "input": "apollo_export_2026-07-30.csv", "rows_read": 312, "rows_normalised": 289, "rows_skipped": 23, "skip_reasons": {"no_canonical_domain": 18, "duplicate_outcome_id": 5}, "campaign_batch": "2026-07-30"}
{"ts": "2026-07-31T14:02:00Z", "script": "analyze_outcomes.py", "action": "analyse", "outcome_files": ["2026-07-30_outcomes.csv"], "total_sends": 289, "segments_computed": 48, "hypotheses_generated": 2, "proposals_written": ["v001_healthcare_icp_floor.yaml"]}
```
