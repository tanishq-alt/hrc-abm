# Experiment Policy — A/B Testing and Canary Rules

## Change Risk Classification

| Type | Risk | Approval | Canary Required |
|---|---|---|---|
| Copy tuning (subject line, first line) | Low | Human review | No |
| Query bank addition (new DDG query) | Low | Human review | No |
| Signal weight adjustment (±10%) | Medium | Human review + backtest | Yes (20%, 2 cycles) |
| Tier floor adjustment (±2 points) | High | Human review + backtest | Yes (20%, 2 cycles) |
| ICP score boundary change | High | Human review + backtest | Yes (20%, 2 cycles) |
| Hard gate addition or removal | Critical | Explicit user sign-off | Yes (20%, 4 cycles) |
| New vertical added | Medium | Human review | No |

## Canary Protocol

### Setup
1. `promote_learning.py` generates a change proposal diff.
2. Human applies it to a branch (e.g. `learning/v001-healthcare-floor`).
3. Next pipeline run uses `--canary-pct 20` (not yet implemented — flag reserved).
4. 20% of accounts processed in that run use the new parameters.
5. Remaining 80% use the existing parameters (control).

### Measurement
- Run pipeline twice (≥ 2 cycles, ≥ 14 calendar days apart).
- After each run, upload Apollo outcomes CSV with `--campaign-batch canary_v001`.
- `analyze_outcomes.py` separates canary vs control using the batch tag.

### Rollback Criteria
Automatically flag for rollback if:
- Canary meeting_rate < 80% of control meeting_rate after 2 cycles
- Canary bounce_rate > control bounce_rate × 1.5
- Canary disqualification_rate > 10%

Rollback is performed by the human reverting the branch.

### Promotion Criteria
Promote to main if:
- Canary meeting_rate ≥ control meeting_rate × 1.1 (10% lift)
- Sample ≥ 20 sends per arm
- No negative side effects in bounce_rate or disqualification_rate

## A/B Subject Line Policy

### Existing infrastructure
Each Account has `email_subject_a` and `email_subject_b`.
Apollo can randomise which subject is used per contact.
The `email_subject_used` field in the outcomes CSV records which was sent.

### Decision rule
```
After ≥ 50 sends per variant:
  winner = variant with higher reply_rate
  if |reply_rate_a - reply_rate_b| >= 3 percentage points:
    generate copy_tuning proposal
  else:
    log "no significant difference" to audit trail
```

### Copy proposal format
A copy_tuning proposal targets a specific vertical + persona_role combination:
```yaml
hypothesis:
  proposed_change:
    file: "engine/personalizer.py"
    parameter: "PERSONA_TONE['champion']['email_subject_template']"
    current_value: "Your new hire packet is still on paper..."
    proposed_value: "3 things {company} caregivers complete before day one..."
    change_type: "copy_tuning"
```

## Proposal Versioning

### Auto-increment
`analyze_outcomes.py` reads existing proposal files in `data/learning/proposals/`
and sets the next version to max(existing) + 1.

### File naming
```
vNNN_{snake_case_description}.yaml
v001_healthcare_icp_floor_raise.yaml
v002_pdf_signal_weight_increase.yaml
v003_champion_subject_line_education.yaml
```

### Status lifecycle
```
pending_review → approved (human decision) → [promoted to APPROVED_LEARNINGS.md]
pending_review → rejected (human decision) → [archived, never deleted]
pending_review → needs_more_data (auto, insufficient sample)
approved → superseded (if a newer proposal covers the same parameter)
```

## A/B Testing Calendar

To avoid interference between concurrent experiments:
- Run only one medium/high-risk experiment at a time per vertical.
- Low-risk copy tests can run concurrently.
- Allow 2 full cycles between completing one experiment and starting the next in the same segment.
