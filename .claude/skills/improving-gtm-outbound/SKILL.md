---
name: improving-gtm-outbound
title: Self-Improving GTM Outbound Learning System
description: >
  Closes the feedback loop between sent campaigns and pipeline scoring.
  Ingests campaign outcomes (replies, meetings, disqualifications) from
  Apollo/HubSpot exports, segments performance by vertical/tier/signal/persona,
  generates versioned improvement proposals, backtests them against history,
  and presents human-readable diffs for approval. Never auto-applies changes.
  Never auto-sends outreach.
category: Learning
---

# Self-Improving GTM Outbound — Skill

## What This Skill Does

1. **Ingests** campaign outcome data (replies, meetings booked, bounces) from
   Apollo/HubSpot CSV exports and normalises it to a canonical outcome schema.

2. **Analyses** performance by every meaningful segment — vertical, account tier,
   signal type, persona role, ADP status, ICP score bucket — and computes reply
   rate, meeting rate, and positive outcome rate per cell.

3. **Generates hypotheses** when a segment performs materially better or worse
   than baseline (minimum 30 sends per cell).

4. **Evaluates proposals** by backtesting the proposed change against historical
   outcome data to estimate its expected lift.

5. **Presents proposals** as human-readable YAML diffs — exact parameter, current
   value, proposed value, expected lift, supporting evidence.

6. **Never** auto-applies any change to engine code. A human must inspect the
   diff, apply it manually, run tests, and commit.

---

## When to Invoke This Skill

- After uploading a new Apollo/HubSpot outcomes CSV to `data/learning/outcomes/`
- When you want to understand why Tier 1 reply rates are lower than expected
- When you want to evaluate whether a scoring change is warranted
- When reviewing a pending proposal in `data/learning/proposals/`
- On a cadence (e.g. monthly) after accumulating enough outcome data

---

## Workflow

```
Step 1 — Ingest
  python3 .claude/skills/improving-gtm-outbound/scripts/ingest_outcomes.py \
      --input path/to/apollo_export.csv \
      --campaign-date 2026-07-01

Step 2 — Analyse
  python3 .claude/skills/improving-gtm-outbound/scripts/analyze_outcomes.py

Step 3 — Review analysis output
  → Check data/learning/analysis/YYYY-MM-DD_analysis.json

Step 4 — Evaluate a specific proposal (optional)
  python3 .claude/skills/improving-gtm-outbound/scripts/evaluate_proposal.py \
      --proposal data/learning/proposals/v001_example.yaml

Step 5 — Human review and promotion (if warranted)
  python3 .claude/skills/improving-gtm-outbound/scripts/promote_learning.py \
      --proposal data/learning/proposals/v001_example.yaml

  → Produces a human-readable diff. Human applies manually, runs tests, commits.
```

---

## Files This Skill Reads

| Path | What It Contains |
|---|---|
| `data/abm_accounts_*.csv` | Pipeline output — accounts with tier, scores, signals |
| `data/enriched_*.csv` | Deduped, re-scored accounts |
| `data/learning/outcomes/*.csv` | Normalised campaign outcome records |
| `data/learning/proposals/*.yaml` | Pending improvement proposals |
| `.claude/skills/improving-gtm-outbound/APPROVED_LEARNINGS.md` | Promoted changes ledger |
| `engine/icp.py` | Current ICP scoring weights |
| `engine/scorer.py` | Current tier floor thresholds |
| `pipeline/run.py` | Current query banks |

## Files This Skill Writes (outcomes only — never source code)

| Path | Trigger |
|---|---|
| `data/learning/outcomes/YYYY-MM-DD_outcomes.csv` | ingest_outcomes.py |
| `data/learning/analysis/YYYY-MM-DD_analysis.json` | analyze_outcomes.py |
| `data/learning/proposals/vNNN_*.yaml` | analyze_outcomes.py (hypothesis) |
| `data/learning/canary/vNNN_canary.csv` | promote_learning.py (diff only) |
| `data/learning/audit/YYYY-MM-DD_audit.jsonl` | Every script appends here |

## Files This Skill NEVER Writes Directly

```
engine/icp.py
engine/scorer.py
engine/personalizer.py
engine/committee.py
pipeline/run.py
```

These are modified only by a human, after reviewing the diff from `promote_learning.py`.

---

## See Also

- `GUARDRAILS.md` — absolute constraints
- `DATA_CONTRACTS.md` — outcome CSV field definitions and validation rules
- `METRICS.md` — KPIs and minimum sample sizes
- `EXPERIMENT_POLICY.md` — A/B window sizes, canary %, rollback criteria
- `LEARNING_LOOP.md` — detailed loop mechanics with decision tree
- `APPROVED_LEARNINGS.md` — append-only ledger of all promoted changes
- `EXAMPLES.md` — worked examples of good and rejected proposals
- `REPO_MAP.md` — exact file paths with descriptions
