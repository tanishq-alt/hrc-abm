# Guardrails — Absolute Constraints

## NEVER (hard stops — no exceptions)

### Never auto-apply code changes
`promote_learning.py` produces a diff file and human instructions.
It does NOT edit `engine/`, `pipeline/`, or any source file directly.
A human must apply the diff, run `python3 -m pytest tests/`, and commit.

### Never auto-send outreach
This system produces leads and scoring improvements. It has no path to
Apollo sequences, email sending, or LinkedIn messages. No script in
`.claude/skills/improving-gtm-outbound/scripts/` imports abm/sequence.py
or calls any Apollo API endpoint.

### Never promote below minimum sample
Any proposal that covers a segment with fewer than 30 sends is blocked by
`evaluate_proposal.py` with a hard error:
```
ERROR: Insufficient data — 23 sends in segment healthcare/Tier 1.
Minimum required: 30. Collect more data before re-evaluating.
```

### Never remove a hard gate
Hard gates in `engine/scorer.py:HARD_GATES` protect against catastrophic
outreach errors (current customers, competitors, below employee floor).
No outcome data justifies removing them. If a hard gate fires incorrectly,
fix the suppression list, not the gate.

### Never write to data/learning/audit/
The audit directory is append-only. Scripts append to existing JSONL files
using Python's `open("...", "a")`. Nothing in this skill deletes or
overwrites audit records. If a record needs correction, append a
superseding entry with a `supersedes` field.

### Never generate proposals from canary data that hasn't completed 2 cycles
A canary run must complete at minimum 2 full pipeline cycles (typically
≥14 calendar days) before its data is used to evaluate a proposal.
`evaluate_proposal.py` checks the `canary_start_date` in the proposal YAML
and blocks evaluation if < 14 days have elapsed.

### Never use company name as a join key
Campaign outcomes are always joined to Account records by `canonical_domain`.
Company name matching is unreliable (aliases, abbreviations, name changes).
If a canonical_domain cannot be resolved from the outcome row, that row is
logged to the audit trail and skipped — never matched on name.

---

## ALWAYS (required behaviors)

### Always run tests before generating a diff
`promote_learning.py` runs `python3 -m pytest tests/ -q` as its first step.
If any test fails, it aborts with:
```
ERROR: Test suite failed. Fix failing tests before promoting this learning.
```

### Always version-stamp proposals
Proposal files use the naming convention `vNNN_{description}.yaml` where
NNN is zero-padded and auto-incremented from the highest existing version.

### Always include backtest results in every proposal YAML
A proposal YAML must contain:
```yaml
backtest:
  historical_periods: 3
  estimated_lift_pct: 8.2
  p_value: 0.04
  sample_size: 47
  confidence: medium
```
If `evaluate_proposal.py` cannot compute a backtest (insufficient history),
the proposal is marked `status: needs_more_data` and not presented for review.

### Always append to the audit trail
Every script invocation appends an entry to
`data/learning/audit/YYYY-MM-DD_audit.jsonl` with:
- script name
- timestamp
- input files
- rows processed
- outcome counts
- any errors or warnings

### Always preserve account_tier_at_send
When computing segment metrics, always use the tier that was assigned
at the time of outreach, not the current tier. Tier changes after send
would distort the measurement.
