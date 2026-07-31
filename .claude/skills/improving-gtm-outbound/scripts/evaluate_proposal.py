"""
Proposal evaluation — backtests a YAML proposal against historical outcome data.

Usage:
  python3 .claude/skills/improving-gtm-outbound/scripts/evaluate_proposal.py \
      --proposal data/learning/proposals/v001_healthcare_icp_floor.yaml

Updates the proposal YAML's backtest section in-place.
Appends to audit trail.
"""

import argparse
import csv
import json
import math
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

OUTCOMES_DIR = ROOT / "data" / "learning" / "outcomes"
AUDIT_DIR = ROOT / "data" / "learning" / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

MIN_SAMPLE = 30


def load_proposal(path: Path) -> dict:
    """Parse minimal YAML-like proposal file into a dict."""
    proposal = {}
    with open(path, encoding="utf-8") as f:
        content = f.read()

    for key in ["version", "status", "description"]:
        m = re.search(rf'^{key}:\s*["\']?(.*?)["\']?\s*$', content, re.M)
        if m:
            proposal[key] = m.group(1).strip()

    # Extract change_type
    m = re.search(r'change_type:\s*["\']?(\w+)["\']?', content)
    proposal["change_type"] = m.group(1) if m else "unknown"

    # Extract sample size from supporting_evidence
    m = re.search(r'sends:\s*(\d+)', content)
    proposal["sample_size"] = int(m.group(1)) if m else 0

    # Extract vertical if present
    m = re.search(r'vertical[=:]\s*["\']?(\w+)["\']?', content)
    proposal["vertical"] = m.group(1) if m else ""

    proposal["_raw"] = content
    return proposal


def load_all_outcomes() -> list[dict]:
    rows = []
    for f in sorted(OUTCOMES_DIR.glob("*.csv")):
        with open(f, newline="", encoding="utf-8") as fh:
            rows.extend(csv.DictReader(fh))
    return rows


def two_proportion_z_test(n1: int, k1: int, n2: int, k2: int) -> float:
    """Two-proportion z-test. Returns p-value (two-tailed, approximated)."""
    if n1 == 0 or n2 == 0:
        return 1.0
    p1 = k1 / n1
    p2 = k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    if p_pool in (0, 1):
        return 1.0
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = abs(p1 - p2) / se
    # Approximate p-value using normal CDF approximation
    # p ≈ 2 * (1 - Φ(|z|)); use Horner's approximation
    t = 1 / (1 + 0.2316419 * z)
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    phi = 1 - (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * z * z) * poly
    return round(2 * (1 - phi), 4)


def compute_confidence(p_value: float, sample_size: int) -> str:
    if p_value < 0.01 and sample_size >= 100:
        return "high"
    if p_value < 0.05 and sample_size >= MIN_SAMPLE:
        return "medium"
    return "low"


def update_proposal_backtest(path: Path, backtest: dict):
    """Update the backtest section in the YAML file."""
    with open(path, encoding="utf-8") as f:
        content = f.read()

    def replace_field(text: str, field: str, value) -> str:
        if value is None:
            new_val = "null"
        elif isinstance(value, str):
            new_val = f'"{value}"'
        else:
            new_val = str(value)
        pattern = rf"(  {field}:\s*).*"
        replacement = rf"\g<1>{new_val}"
        return re.sub(pattern, replacement, text, count=1)

    content = replace_field(content, "estimated_lift_pct",
                            backtest.get("estimated_lift_pct"))
    content = replace_field(content, "p_value", backtest.get("p_value"))
    content = replace_field(content, "sample_size", backtest.get("sample_size"))
    content = replace_field(content, "confidence",
                            backtest.get("confidence", "low"))

    # Update status
    new_status = "pending_review" if backtest.get("confidence") in ("medium", "high") else "needs_more_data"
    content = re.sub(r'^status:.*', f'status: "{new_status}"', content, count=1, flags=re.M)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def append_audit(entry: dict):
    today = date.today().isoformat()
    audit_file = AUDIT_DIR / f"{today}_audit.jsonl"
    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run(proposal_path: Path) -> dict:
    if not proposal_path.exists():
        print(f"ERROR: Proposal not found: {proposal_path}")
        sys.exit(1)

    proposal = load_proposal(proposal_path)
    print(f"Evaluating: {proposal.get('description', proposal_path.name)}")
    print(f"  Change type: {proposal['change_type']}")
    print(f"  Sample in proposal: {proposal['sample_size']}")

    if proposal["sample_size"] < MIN_SAMPLE:
        print(f"\nERROR: Insufficient data — {proposal['sample_size']} sends in proposal segment.")
        print(f"Minimum required: {MIN_SAMPLE}. Collect more data before re-evaluating.")
        update_proposal_backtest(proposal_path, {
            "estimated_lift_pct": None,
            "p_value": None,
            "sample_size": proposal["sample_size"],
            "confidence": "low",
        })
        return {"status": "needs_more_data"}

    all_outcomes = load_all_outcomes()
    if not all_outcomes:
        print("ERROR: No outcome data found. Run ingest_outcomes.py first.")
        sys.exit(1)

    vertical = proposal.get("vertical", "")

    # Split outcomes into matched (proposal segment) and control
    matched = []
    control = []
    for row in all_outcomes:
        row_vertical = row.get("vertical", "")
        if vertical and row_vertical != vertical:
            control.append(row)
            continue
        matched.append(row)

    n_matched = len(matched)
    n_control = len(control) or 1

    k_matched_meetings = sum(1 for r in matched if r.get("outcome") == "meeting_booked")
    k_control_meetings = sum(1 for r in control if r.get("outcome") == "meeting_booked")

    matched_rate = round(k_matched_meetings / n_matched * 100, 1) if n_matched else 0
    control_rate = round(k_control_meetings / n_control * 100, 1) if n_control else 0
    lift_pct = round(matched_rate - control_rate, 1)

    p_value = two_proportion_z_test(n_matched, k_matched_meetings, n_control, k_control_meetings)
    confidence = compute_confidence(p_value, n_matched)

    print(f"\nBacktest results:")
    print(f"  Matched segment:  {n_matched} sends, {matched_rate}% meeting rate")
    print(f"  Control segment:  {n_control} sends, {control_rate}% meeting rate")
    print(f"  Estimated lift:   {lift_pct:+.1f}pp")
    print(f"  p-value:          {p_value}")
    print(f"  Confidence:       {confidence}")

    backtest = {
        "estimated_lift_pct": lift_pct,
        "p_value": p_value,
        "sample_size": n_matched,
        "confidence": confidence,
    }

    update_proposal_backtest(proposal_path, backtest)
    print(f"\nProposal updated: {proposal_path.name}")

    if confidence == "low" or p_value >= 0.05:
        print("STATUS: needs_more_data — p-value too high or sample too small.")
    else:
        print(f"STATUS: pending_review — {confidence} confidence. Ready for human review.")

    append_audit({
        "ts": datetime.utcnow().isoformat() + "Z",
        "script": "evaluate_proposal.py",
        "action": "evaluate",
        "proposal": proposal_path.name,
        "change_type": proposal["change_type"],
        "backtest": backtest,
        "outcome": "pending_review" if confidence != "low" else "needs_more_data",
    })

    return backtest


def main():
    parser = argparse.ArgumentParser(description="Backtest a proposal against historical outcome data")
    parser.add_argument("--proposal", required=True, help="Path to proposal YAML file")
    args = parser.parse_args()
    run(Path(args.proposal))


if __name__ == "__main__":
    main()
