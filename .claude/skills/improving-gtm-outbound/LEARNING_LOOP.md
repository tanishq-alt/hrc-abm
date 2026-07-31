# Learning Loop — Step-by-Step Mechanics

## Overview

```
Campaign runs → Apollo sends emails → Outcomes collected
     ↓
ingest_outcomes.py   (normalise, validate, join, append)
     ↓
analyze_outcomes.py  (segment, compute metrics, find anomalies)
     ↓
evaluate_proposal.py (backtest against history)
     ↓
Human review         (inspect diff, decide approve/reject)
     ↓
promote_learning.py  (generate diff for human to apply)
     ↓
Human applies diff   (edits source file, runs tests, commits)
     ↓
APPROVED_LEARNINGS.md updated
     ↓
Next pipeline run uses improved parameters
```

---

## Step 1: Ingest

**Script**: `scripts/ingest_outcomes.py`
**Trigger**: Manually, after downloading Apollo/HubSpot CSV.

```bash
python3 .claude/skills/improving-gtm-outbound/scripts/ingest_outcomes.py \
    --input ~/Downloads/apollo_export_2026-08-01.csv \
    --campaign-date 2026-08-01
```

**What it does**:
1. Auto-detects column names (Apollo vs HubSpot format).
2. Normalises `canonical_domain` from Website column (strip www., lowercase, strip path).
3. Derives `contact_persona_role` from `contact_title` via `infer_persona_role()`.
4. Joins to the most recent `data/abm_accounts_*.csv` by `canonical_domain`.
   - Fills: `account_tier_at_send`, `icp_score_at_send`, `signal_type_at_send`,
     `vertical`, `adp_status_at_send`, `hris_fit_category_at_send`.
5. Deduplicates by `outcome_id` (SHA-256 of domain+date+title).
   - Skips rows that already exist in any prior outcomes CSV.
6. Writes to `data/learning/outcomes/YYYY-MM-DD_outcomes.csv`.
7. Appends to `data/learning/audit/YYYY-MM-DD_audit.jsonl`.

**Validation gates**:
- Rejects rows with no `canonical_domain` (logs skip reason).
- Rejects rows where `outcome` is not in the enum.
- Warns if `account_tier_at_send` could not be joined (no matching account).
- Errors if outcome CSV already has > 50% rows with unknown vertical (likely wrong file).

---

## Step 2: Analyse

**Script**: `scripts/analyze_outcomes.py`
**Trigger**: Manually, after ingestion.

```bash
python3 .claude/skills/improving-gtm-outbound/scripts/analyze_outcomes.py \
    [--window-days 180]   # default 180
```

**What it does**:
1. Reads all `data/learning/outcomes/*.csv` within the window.
2. Computes primary metrics (reply_rate, meeting_rate, positive_outcome_rate)
   across all segmentation dimensions defined in METRICS.md.
3. Computes baseline metrics (global average across all sends).
4. Identifies anomalies:
   - Segments with meeting_rate ≥ 1.5× baseline (outperforming — exploit)
   - Segments with meeting_rate ≤ 0.5× baseline (underperforming — investigate)
   - Tier floor misalignments (Tier 1 underperforms Tier 2 in same segment)
5. For each anomaly where `sends >= 30`: generates a hypothesis and proposal YAML.
6. Writes analysis snapshot to `data/learning/analysis/YYYY-MM-DD_analysis.json`.
7. Writes proposal YAMLs to `data/learning/proposals/vNNN_*.yaml`.
8. Appends to audit trail.

**Hypothesis generation logic**:

| Observation | Proposal type | File targeted |
|---|---|---|
| Signal type X has 2× meeting rate | Increase X's weight in SIGNAL_BASE_SCORES | engine/signals.py |
| Tier 1 accounts in vertical V have low meeting rate | Raise ICP floor for that vertical | engine/scorer.py |
| champion outperforms economic_buyer in vertical V | Update TITLE_TO_ROLE priority | engine/personalizer.py |
| Query pattern Q produces 0 qualified leads | Remove or rewrite Q | pipeline/run.py |
| Subject line A beats B by ≥ 3pp | Promote A as default for that persona | engine/personalizer.py |

---

## Step 3: Evaluate (Backtest)

**Script**: `scripts/evaluate_proposal.py`
**Trigger**: Manually, to check a specific proposal before human review.

```bash
python3 .claude/skills/improving-gtm-outbound/scripts/evaluate_proposal.py \
    --proposal data/learning/proposals/v001_healthcare_icp_floor.yaml
```

**What it does**:
1. Reads the proposal YAML.
2. Loads all historical outcome data.
3. Simulates: which accounts would have been promoted to Tier 1 under the new
   parameter value, and how did those accounts actually perform?
4. Computes estimated lift: `(hypothetical_meeting_rate - actual_meeting_rate)`.
5. Runs a two-proportion z-test for significance.
6. Updates the proposal YAML `backtest` section.
7. If `p_value < 0.05` and `sample_size >= 30`: sets `confidence: medium`.
   If `p_value < 0.01` and `sample_size >= 100`: sets `confidence: high`.
   Otherwise: sets `status: needs_more_data`.
8. Appends to audit trail.

---

## Step 4: Human Review

After `evaluate_proposal.py` runs successfully, the proposal YAML contains:
- The exact parameter to change
- The current value and proposed value
- Backtest lift estimate and p-value
- Supporting segment data

The human reads `data/learning/proposals/vNNN_*.yaml` and decides:
- **Approve**: run `promote_learning.py --proposal ... --decision approve`
- **Reject**: run `promote_learning.py --proposal ... --decision reject --notes "reason"`
- **Defer**: leave status as `pending_review` (no action needed)

---

## Step 5: Promote

**Script**: `scripts/promote_learning.py`
**Trigger**: Manually, after human reviews and approves a proposal.

```bash
python3 .claude/skills/improving-gtm-outbound/scripts/promote_learning.py \
    --proposal data/learning/proposals/v001_healthcare_icp_floor.yaml \
    --decision approve \
    --reviewer "Your Name"
```

**What it does**:
1. Runs `python3 -m pytest tests/ -q`. Aborts if any test fails.
2. Reads the proposal YAML.
3. Reads the target source file.
4. Generates a unified diff showing exactly what would change.
5. Writes the diff to `data/learning/proposals/v001_healthcare_icp_floor.diff`.
6. Prints human-readable instructions:
   ```
   PROPOSAL v001 — Approved by Your Name
   
   To apply this change:
     1. Open engine/scorer.py
     2. Apply the diff at: data/learning/proposals/v001_healthcare_icp_floor.diff
     3. Run: python3 -m pytest tests/ -q
     4. Commit: git add engine/scorer.py && git commit -m "learning: raise healthcare Tier 1 ICP floor to 28 (v001)"
     5. Append to APPROVED_LEARNINGS.md (instructions below)
   ```
7. Updates proposal YAML `human_review` section with reviewer and decision.
8. Appends approval entry to `APPROVED_LEARNINGS.md`.
9. Appends to audit trail.

**NEVER**: edits `engine/scorer.py` or any source file directly.

---

## Step 6: Apply (Human)

The human:
1. Reviews the diff file.
2. Applies it with: `git apply data/learning/proposals/v001_*.diff`
3. Runs: `python3 -m pytest tests/ -q`
4. Fixes any test failures.
5. Commits with the message suggested by `promote_learning.py`.

---

## Decision Tree

```
New outcome data uploaded?
├── YES → Run ingest_outcomes.py
│         └── Run analyze_outcomes.py
│               ├── Anomalies found with ≥ 30 sends?
│               │   ├── YES → Proposal YAML created
│               │   │         └── Run evaluate_proposal.py
│               │   │               ├── Backtest p < 0.05?
│               │   │               │   └── YES → Present for human review
│               │   │               │   └── NO  → status: needs_more_data
│               │   │               └── Sample < 30? → status: needs_more_data
│               │   └── NO  → Log "no proposals this cycle" to audit
│               └── All good → Done
└── NO → Nothing to do
```
