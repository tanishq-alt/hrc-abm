# Metrics — KPIs and Measurement

## Primary KPIs

| Metric | Formula | Target |
|---|---|---|
| `reply_rate` | replies / sends | Tier 1 ≥ 20%, Tier 2 ≥ 10% |
| `meeting_rate` | meetings_booked / sends | Tier 1 ≥ 5%, Tier 2 ≥ 2% |
| `positive_outcome_rate` | (replies + meetings) / sends | Tier 1 ≥ 22% |
| `bounce_rate` | bounced / sends | < 3% (data quality signal) |
| `disqualification_rate` | disqualified / sends | < 5% (precision signal) |

## Segmentation Dimensions

Every metric is computed across every combination of these dimensions:

```
Primary (always segmented):
  vertical               healthcare | education | manufacturing | nonprofit | government | utilities
  account_tier           Tier 1 | Tier 2 | Tier 3

Secondary (when sample permits):
  signal_type            pdf_new_hire_packet | adp_confirmed | rfp_hris | osha_citation | ...
  contact_persona_role   champion | economic_buyer | influencer | blocker | unknown
  adp_status             confirmed | strongly_likely | not_found | not_checked
  icp_score_bucket       <26 | 26-28 | 29-32 | 33-35
  hris_fit_category      integration_fit | workflow_extension_fit | possible_displacement | unknown

Cross-cuts (when ≥ 30 sends):
  vertical × tier
  vertical × signal_type
  tier × signal_type
  vertical × contact_persona_role
```

## Minimum Sample Requirements

| Use | Minimum Sends | Rationale |
|---|---|---|
| Reporting (show metric) | 10 | Below this: display "--" not a number |
| Hypothesis generation | 30 | Below this: no proposal produced |
| Signal weight change | 50 | Weight changes affect many accounts |
| Tier floor change | 50 | Floor changes affect tier assignment |
| Hard gate addition | 100 | Hard gates disqualify all future accounts |
| Canary evaluation | 20 per arm | Minimum before reading canary results |

## Baseline Hypotheses (to validate against real data)

These are directional expectations before real data arrives:

```
H1: Tier 1 meeting_rate ≥ 2× Tier 2 meeting_rate
H2: pdf_new_hire_packet meeting_rate ≥ 1.5× adp_confirmed meeting_rate
H3: champion reply_rate ≥ economic_buyer reply_rate
H4: ADP confirmed reply_rate ≥ 1.5× ADP not_checked
H5: Tier A/B evidence accounts: positive_outcome_rate ≥ 1.5× Tier C
H6: healthcare Tier 1 meeting_rate ≥ 4% (absolute)
H7: rfp_hris accounts: meeting_rate ≥ 8% (highest urgency signal)
```

## Signal Strength Thresholds (for hypothesis generation)

`analyze_outcomes.py` generates a hypothesis when:

```python
# Segment outperforms baseline
if segment.reply_rate_pct > baseline.reply_rate_pct * 1.5 and segment.sends >= 30:
    generate_positive_hypothesis(segment)

# Segment underperforms baseline
if segment.reply_rate_pct < baseline.reply_rate_pct * 0.5 and segment.sends >= 30:
    generate_negative_hypothesis(segment)

# Tier floor misalignment
if tier1_accounts_in_segment.meeting_rate < tier2_accounts_in_segment.meeting_rate:
    generate_floor_hypothesis(segment)
```

## A/B Subject Line Tracking

Both `email_subject_a` and `email_subject_b` are in every Account CSV.
Apollo sends one variant per contact (alternating or random split).
Track which was sent via the `email_subject_used` field in outcomes CSV.

Declare a winner after:
- ≥ 50 sends per variant
- p < 0.05 on a two-proportion z-test

Lift threshold for promotion: ≥ 3 percentage points absolute improvement
in reply_rate.

## Metric Freshness

Outcome data decays in relevance — market conditions change.
Apply a 6-month rolling window by default:
- Data > 6 months old is retained in `data/learning/outcomes/` but
  de-weighted in hypothesis generation.
- Data > 12 months old is tagged as `historical_context_only`.

`analyze_outcomes.py --window-days 180` controls this.
