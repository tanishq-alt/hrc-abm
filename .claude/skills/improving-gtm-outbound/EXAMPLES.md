# Examples — Good and Rejected Proposals

## Example 1: Well-Formed Proposal (Approved)

**Scenario**: After 3 months of healthcare outreach, Tier 1 accounts where the
primary signal was `rfp_hris` consistently book meetings at 12% vs the 4% average.

**Analysis output** (excerpt from analysis JSON):
```json
{
  "dimensions": {"vertical": "healthcare", "account_tier": "Tier 1", "signal_type": "rfp_hris"},
  "sends": 38,
  "replies": 11,
  "meetings": 5,
  "reply_rate_pct": 28.9,
  "meeting_rate_pct": 13.2,
  "vs_baseline_meeting_pct": 8.7,
  "signal": "above_baseline"
}
```

**Generated proposal YAML**:
```yaml
version: "001"
created_at: "2026-09-15T10:00:00Z"
status: "pending_review"
description: "Increase rfp_hris signal base score from 30 to 35 in engine/signals.py"

hypothesis:
  observation: >
    Healthcare Tier 1 accounts where rfp_hris is the primary signal show
    13.2% meeting rate vs 4.5% baseline (n=38). rfp_hris is the clearest
    buying intent signal — active procurement window is open.
  proposed_change:
    file: "engine/signals.py"
    parameter: "SIGNAL_BASE_SCORES['rfp_hris']"
    current_value: 30
    proposed_value: 35
    change_type: "signal_weight"

backtest:
  historical_periods: 3
  estimated_lift_pct: 2.1
  p_value: 0.03
  sample_size: 38
  confidence: "medium"

canary:
  status: "not_started"
  canary_pct: 20
  min_cycles: 2
```

**Why this is good**:
- Specific parameter with current and proposed values
- Concrete evidence from real send data (n=38 ≥ 30 minimum)
- Backtest p < 0.05
- The proposed change is proportional (5-point increase, not a wholesale rewrite)
- `change_type: signal_weight` correctly flags canary requirement

---

## Example 2: Correctly Rejected Proposal

**Scenario**: After 2 weeks, healthcare Tier 2 accounts seem to underperform.
The system generates a proposal to lower the Tier 2 floor.

**Why it was rejected**:
```
REJECTION REASON: Insufficient sample
  healthcare/Tier 2 sends: 14 (minimum 30 required for tier_floor changes)
  
The 2-week window is also too short. Tier 2 sequences run 3 steps over 3 weeks.
Many contacts haven't received step 3 yet. Re-evaluate after 45 days.
```

**Lesson**: Never evaluate sequence performance before the sequence is complete.
`analyze_outcomes.py` adds a warning when the analysis window < sequence length.

---

## Example 3: Copy Tuning Proposal (Low-Risk, No Canary)

**Scenario**: After 60 sends in education, subject line A ("August is your highest-volume
hiring month") had 31% reply rate vs subject line B ("HR Cloud moves teacher onboarding
from 2 days to 20 minutes") at 18%.

**Generated proposal YAML** (copy_tuning, no canary required):
```yaml
version: "003"
description: "Promote subject_a as default for education champion — 13pp lift"

hypothesis:
  proposed_change:
    file: "engine/personalizer.py"
    parameter: "generate_outreach() education champion email_subject_a template"
    current_value: "HR Cloud moves teacher onboarding from 2 days to 20 minutes"
    proposed_value: "August is your highest-volume hiring month — we move it to 20 minutes"
    change_type: "copy_tuning"

backtest:
  estimated_lift_pct: 13.0
  p_value: 0.02
  sample_size: 60
  confidence: "medium"

canary:
  status: "not_required"   # copy_tuning is low-risk
```

**Why this is a good candidate for fast approval**:
- `copy_tuning` is lowest risk (affects only one string)
- n=60 per variant ≥ 50 minimum
- 13 percentage point lift is material
- p < 0.05
- No canary required per EXPERIMENT_POLICY.md

---

## Example 4: Hard Gate Proposal (Blocked)

**Scenario**: A user suggests removing the `current_customer` hard gate because
a prospect replied saying they are an ex-customer, not a current one.

**What happens**:
```
ERROR: promote_learning.py — Hard gate proposals require explicit user sign-off.
Hard gate changes are not generated automatically. To propose a hard gate change,
manually create a proposal YAML with change_type: "hard_gate" and set
requires_explicit_signoff: true. Then contact your team lead for approval.

The current_customer suppression list (not the gate logic itself) can be updated
by editing the suppression CSV directly — no learning proposal needed.
```

**Lesson**: Hard gates are absolute. The suppression *list* is the right place
to handle ex-customer edge cases — not the gate logic.

---

## How to Read an Analysis Output

```
Total sends: 247
Overall reply rate: 13.8%   Overall meeting rate: 4.5%

TOP SEGMENTS (above 1.5x baseline meeting rate):
  healthcare / Tier 1 / rfp_hris: 13.2% meeting rate (n=38) ↑ 193%
  education / Tier 1 / pdf_new_hire_packet: 9.1% meeting rate (n=55) ↑ 102%

UNDERPERFORMING SEGMENTS (below 0.5x baseline meeting rate):
  manufacturing / Tier 2 / acquisition: 1.1% meeting rate (n=31) ↓ 76%

INSUFFICIENT DATA (below 30 sends — no proposals generated):
  government / Tier 1 / rfp_hris: 2.1% meeting rate (n=12)
  utilities / Tier 1 / osha_citation: 0% meeting rate (n=7)

PROPOSALS GENERATED: 2
  → data/learning/proposals/v001_rfp_hris_weight_increase.yaml
  → data/learning/proposals/v002_manufacturing_acquisition_query_review.yaml
```
