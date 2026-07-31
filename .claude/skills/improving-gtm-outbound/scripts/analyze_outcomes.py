"""
Outcome analysis script — segments performance data and generates proposals.

Usage:
  python3 .claude/skills/improving-gtm-outbound/scripts/analyze_outcomes.py \
      [--window-days 180]

Output: data/learning/analysis/YYYY-MM-DD_analysis.json
        data/learning/proposals/vNNN_*.yaml (one per hypothesis)
        data/learning/audit/YYYY-MM-DD_audit.jsonl (appended)
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

OUTCOMES_DIR = ROOT / "data" / "learning" / "outcomes"
ANALYSIS_DIR = ROOT / "data" / "learning" / "analysis"
PROPOSALS_DIR = ROOT / "data" / "learning" / "proposals"
AUDIT_DIR = ROOT / "data" / "learning" / "audit"

for d in (ANALYSIS_DIR, PROPOSALS_DIR, AUDIT_DIR):
    d.mkdir(parents=True, exist_ok=True)

POSITIVE_OUTCOMES = {"reply", "meeting_booked"}
MIN_SAMPLE = 30
OUTPERFORM_THRESHOLD = 1.5   # segment meeting_rate / baseline >= this → hypothesis
UNDERPERFORM_THRESHOLD = 0.5  # segment meeting_rate / baseline <= this → hypothesis


# ── Metrics computation ───────────────────────────────────────────────────────

def compute_metrics(rows: list[dict]) -> dict:
    sends = len(rows)
    replies = sum(1 for r in rows if r["outcome"] == "reply")
    meetings = sum(1 for r in rows if r["outcome"] == "meeting_booked")
    bounces = sum(1 for r in rows if r["outcome"] == "bounced")
    disqualified = sum(1 for r in rows if r["outcome"] == "disqualified")
    return {
        "sends": sends,
        "replies": replies,
        "meetings": meetings,
        "bounced": bounces,
        "disqualified": disqualified,
        "reply_rate_pct": round(replies / sends * 100, 1) if sends else 0.0,
        "meeting_rate_pct": round(meetings / sends * 100, 1) if sends else 0.0,
        "positive_outcome_rate_pct": round((replies + meetings) / sends * 100, 1) if sends else 0.0,
        "bounce_rate_pct": round(bounces / sends * 100, 1) if sends else 0.0,
        "disqualification_rate_pct": round(disqualified / sends * 100, 1) if sends else 0.0,
        "min_sample_met": sends >= MIN_SAMPLE,
    }


def segment_rows(rows: list[dict]) -> dict:
    """Group rows by every dimension combination."""
    groups: dict[tuple, list] = defaultdict(list)
    for row in rows:
        v = row.get("vertical", "")
        t = row.get("account_tier_at_send", "")
        s = row.get("signal_type_at_send", "")
        p = row.get("contact_persona_role", "")
        a = row.get("adp_status_at_send", "")

        # All primary segmentations
        for key in [
            ("vertical", v),
            ("account_tier", t),
            (f"vertical={v}", "tier", t),
            (f"vertical={v}", "signal", s),
            (f"vertical={v}", "persona", p),
            (f"tier={t}", "signal", s),
            (f"vertical={v}", "tier", t, "signal", s),
        ]:
            groups[key].append(row)
    return dict(groups)


# ── Proposal generation ───────────────────────────────────────────────────────

def next_version(proposals_dir: Path = None) -> str:
    _dir = proposals_dir or PROPOSALS_DIR
    existing = list(_dir.glob("v*.yaml"))
    if not existing:
        return "001"
    nums = []
    for p in existing:
        try:
            nums.append(int(p.stem.split("_")[0].lstrip("v")))
        except ValueError:
            pass
    return str(max(nums) + 1).zfill(3) if nums else "001"


def write_proposal(version: str, description: str, hypothesis: dict,
                   evidence_segments: list, backtest_placeholder: dict) -> Path:
    slug = description.lower().replace(" ", "_")[:60]
    path = PROPOSALS_DIR / f"v{version}_{slug}.yaml"

    lines = [
        f'version: "{version}"',
        f'created_at: "{datetime.utcnow().isoformat()}Z"',
        'status: "pending_review"',
        f'description: "{description}"',
        "",
        "hypothesis:",
        f"  observation: >",
        f"    {hypothesis['observation']}",
        "  proposed_change:",
        f"    file: \"{hypothesis['file']}\"",
        f"    parameter: \"{hypothesis['parameter']}\"",
        f"    current_value: {hypothesis['current_value']}",
        f"    proposed_value: {hypothesis['proposed_value']}",
        f"    change_type: \"{hypothesis['change_type']}\"",
        "",
        "supporting_evidence:",
        "  segments:",
    ]
    for seg in evidence_segments:
        lines.append(f"    - dimensions: {json.dumps(seg.get('dimensions', {}))}")
        lines.append(f"      sends: {seg['sends']}")
        lines.append(f"      replies: {seg['replies']}")
        lines.append(f"      meetings: {seg['meetings']}")
        lines.append(f"      reply_rate_pct: {seg['reply_rate_pct']}")
        lines.append(f"      meeting_rate_pct: {seg['meeting_rate_pct']}")
    lines += [
        "",
        "backtest:",
        f"  historical_periods: {backtest_placeholder.get('historical_periods', 0)}",
        f"  estimated_lift_pct: null",
        f"  p_value: null",
        f"  sample_size: {backtest_placeholder.get('sample_size', 0)}",
        f"  confidence: \"pending\"",
        "",
        "canary:",
        "  status: \"not_started\"",
        "  canary_start_date: null",
        "  canary_pct: 20",
        "  min_cycles: 2",
        "  canary_meeting_rate: null",
        "  control_meeting_rate: null",
        "",
        "human_review:",
        "  reviewer: null",
        "  reviewed_at: null",
        "  decision: null",
        "  notes: null",
        "",
        "diff_file: null",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def generate_hypotheses(segments: dict, baseline: dict) -> list[dict]:
    """Generate hypothesis dicts from underperforming / outperforming segments."""
    hypotheses = []
    baseline_meeting = baseline.get("meeting_rate_pct", 0.0) or 0.001

    for key, rows in segments.items():
        m = compute_metrics(rows)
        if not m["min_sample_met"]:
            continue

        seg_meeting = m["meeting_rate_pct"]
        ratio = seg_meeting / baseline_meeting

        if ratio >= OUTPERFORM_THRESHOLD:
            # Segment outperforms — consider increasing signal weight or priority
            dimensions = _key_to_dict(key)
            signal = dimensions.get("signal", "")
            vertical = dimensions.get("vertical", "")

            if signal:
                hypotheses.append({
                    "description": f"Increase {signal} signal weight — {seg_meeting:.1f}% meeting rate",
                    "hypothesis": {
                        "observation": (
                            f"{vertical + ' ' if vertical else ''}{signal} accounts show "
                            f"{seg_meeting:.1f}% meeting rate vs {baseline['meeting_rate_pct']:.1f}% baseline "
                            f"(n={m['sends']}, ratio={ratio:.1f}x)."
                        ),
                        "file": "engine/signals.py",
                        "parameter": f"SIGNAL_BASE_SCORES['{signal}']",
                        "current_value": "see engine/signals.py",
                        "proposed_value": "increase by 5",
                        "change_type": "signal_weight",
                    },
                    "metrics": m,
                    "dimensions": dimensions,
                })

        elif ratio <= UNDERPERFORM_THRESHOLD:
            dimensions = _key_to_dict(key)
            signal = dimensions.get("signal", "")
            tier = dimensions.get("account_tier", "")
            vertical = dimensions.get("vertical", "")

            if signal:
                hypotheses.append({
                    "description": (
                        f"Review {signal} query coverage — "
                        f"{seg_meeting:.1f}% meeting rate ({vertical})"
                    ),
                    "hypothesis": {
                        "observation": (
                            f"{vertical + ' ' if vertical else ''}{signal} accounts "
                            f"underperform at {seg_meeting:.1f}% vs {baseline['meeting_rate_pct']:.1f}% baseline "
                            f"(n={m['sends']}, ratio={ratio:.1f}x). Review query relevance or ICP fit."
                        ),
                        "file": "pipeline/run.py",
                        "parameter": f"VERTICAL_QUERIES['{vertical}'] — {signal} entries",
                        "current_value": "current queries",
                        "proposed_value": "refine or remove low-quality queries",
                        "change_type": "query_addition",
                    },
                    "metrics": m,
                    "dimensions": dimensions,
                })

    return hypotheses


def _key_to_dict(key: tuple) -> dict:
    """Convert segment tuple key to a readable dict for display."""
    d = {}
    LABEL_MARKERS = {"tier", "signal", "persona", "adp"}
    items = list(key)
    i = 0
    while i < len(items):
        item = str(items[i])
        if "=" in item:
            k, v = item.split("=", 1)
            d[k] = v
            i += 1
        elif item in LABEL_MARKERS and i + 1 < len(items):
            d[item] = str(items[i + 1])
            i += 2
        else:
            i += 1
    return d


def append_audit(entry: dict):
    today = date.today().isoformat()
    audit_file = AUDIT_DIR / f"{today}_audit.jsonl"
    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def run(window_days: int = 180) -> Path:
    cutoff = date.today() - timedelta(days=window_days)

    all_rows: list[dict] = []
    files_read = []
    for outcome_file in sorted(OUTCOMES_DIR.glob("*.csv")):
        try:
            file_date = datetime.strptime(outcome_file.stem.split("_")[0], "%Y-%m-%d").date()
            if file_date < cutoff:
                continue
        except ValueError:
            pass

        with open(outcome_file, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            all_rows.extend(rows)
            files_read.append(outcome_file.name)

    if not all_rows:
        print(f"No outcome data found in {OUTCOMES_DIR} within the last {window_days} days.")
        print("Run ingest_outcomes.py first.")
        sys.exit(0)

    print(f"Loaded {len(all_rows)} outcome rows from {len(files_read)} file(s)")

    baseline = compute_metrics(all_rows)
    print(f"\nBaseline: {baseline['sends']} sends | "
          f"{baseline['reply_rate_pct']}% reply | "
          f"{baseline['meeting_rate_pct']}% meeting")

    segments = segment_rows(all_rows)
    print(f"Computed {len(segments)} segments")

    # Build segment summary for analysis output
    segment_summary = []
    for key, rows in sorted(segments.items(), key=lambda kv: -len(kv[1])):
        m = compute_metrics(rows)
        if m["sends"] < 10:
            continue
        dims = _key_to_dict(key)
        vs_reply = round(m["reply_rate_pct"] - baseline["reply_rate_pct"], 1)
        vs_meeting = round(m["meeting_rate_pct"] - baseline["meeting_rate_pct"], 1)
        signal = "above_baseline" if vs_meeting > 2 else ("below_baseline" if vs_meeting < -2 else "at_baseline")
        segment_summary.append({
            "dimensions": dims,
            **m,
            "vs_baseline_reply_pct": vs_reply,
            "vs_baseline_meeting_pct": vs_meeting,
            "signal": signal,
        })

    # Generate hypotheses
    hypotheses = generate_hypotheses(segments, baseline)
    proposal_paths = []
    for hyp in hypotheses:
        version = next_version()
        path = write_proposal(
            version=version,
            description=hyp["description"],
            hypothesis=hyp["hypothesis"],
            evidence_segments=[{
                "dimensions": hyp["dimensions"],
                **hyp["metrics"],
            }],
            backtest_placeholder={"sample_size": hyp["metrics"]["sends"], "historical_periods": len(files_read)},
        )
        proposal_paths.append(str(path))
        print(f"  → Proposal {version}: {path.name}")

    # Write analysis snapshot
    today = date.today().isoformat()
    analysis_path = ANALYSIS_DIR / f"{today}_analysis.json"
    analysis = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "window_days": window_days,
        "outcome_files": files_read,
        "total_sends": baseline["sends"],
        "total_replies": baseline["replies"],
        "total_meetings": baseline["meetings"],
        "overall_reply_rate_pct": baseline["reply_rate_pct"],
        "overall_meeting_rate_pct": baseline["meeting_rate_pct"],
        "segments": segment_summary,
        "hypotheses_generated": len(hypotheses),
        "proposal_files": proposal_paths,
    }
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    print(f"\nAnalysis complete")
    print(f"  Segments computed:    {len(segment_summary)}")
    print(f"  Proposals generated:  {len(hypotheses)}")
    print(f"  Analysis output:      {analysis_path}")

    if not hypotheses:
        print("\n  No anomalous segments found with ≥ 30 sends. Collect more data.")

    append_audit({
        "ts": datetime.utcnow().isoformat() + "Z",
        "script": "analyze_outcomes.py",
        "action": "analyse",
        "outcome_files": files_read,
        "total_sends": baseline["sends"],
        "segments_computed": len(segment_summary),
        "hypotheses_generated": len(hypotheses),
        "proposals_written": proposal_paths,
    })

    return analysis_path


def main():
    parser = argparse.ArgumentParser(description="Segment outcome data and generate proposals")
    parser.add_argument("--window-days", type=int, default=180,
                        help="Rolling window for outcome data (default: 180 days)")
    args = parser.parse_args()
    run(args.window_days)


if __name__ == "__main__":
    main()
