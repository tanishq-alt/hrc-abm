"""
Promotion script — generates a human-readable diff for an approved proposal.

NEVER edits source files directly. Produces a diff and prints instructions.

Usage:
  python3 .claude/skills/improving-gtm-outbound/scripts/promote_learning.py \
      --proposal data/learning/proposals/v001_healthcare_icp_floor.yaml \
      --decision approve \
      --reviewer "Your Name" \
      [--notes "Approved after 2-cycle canary"]

  python3 .claude/skills/improving-gtm-outbound/scripts/promote_learning.py \
      --proposal data/learning/proposals/v001_healthcare_icp_floor.yaml \
      --decision reject \
      --reviewer "Your Name" \
      --notes "Canary rollback — meeting rate dropped"
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

PROPOSALS_DIR = ROOT / "data" / "learning" / "proposals"
AUDIT_DIR = ROOT / "data" / "learning" / "audit"
APPROVED_LEARNINGS = ROOT / ".claude" / "skills" / "improving-gtm-outbound" / "APPROVED_LEARNINGS.md"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

HARD_GATE_CHANGE_TYPES = {"hard_gate"}
REQUIRES_CANARY = {"signal_weight", "tier_floor_adjustment", "icp_score_boundary"}


def run_tests() -> bool:
    print("Running test suite...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(result.stdout[-1000:] if result.stdout else "")
    if result.returncode != 0:
        print("STDERR:", result.stderr[-500:] if result.stderr else "")
        return False
    return True


def load_proposal(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        content = f.read()

    proposal = {"_raw": content, "_path": path}

    for key in ["version", "status", "description"]:
        m = re.search(rf'^{key}:\s*["\']?(.*?)["\']?\s*$', content, re.M)
        proposal[key] = m.group(1).strip() if m else ""

    m = re.search(r'change_type:\s*["\']?(\w+)["\']?', content)
    proposal["change_type"] = m.group(1) if m else "unknown"

    m = re.search(r'file:\s*["\']?(.*?)["\']?\s*$', content, re.M)
    proposal["target_file"] = m.group(1).strip() if m else ""

    m = re.search(r'parameter:\s*["\']?(.*?)["\']?\s*$', content, re.M)
    proposal["parameter"] = m.group(1).strip() if m else ""

    m = re.search(r'current_value:\s*(.*?)\s*$', content, re.M)
    proposal["current_value"] = m.group(1).strip() if m else ""

    m = re.search(r'proposed_value:\s*(.*?)\s*$', content, re.M)
    proposal["proposed_value"] = m.group(1).strip() if m else ""

    m = re.search(r'confidence:\s*["\']?(\w+)["\']?', content)
    proposal["confidence"] = m.group(1) if m else "low"

    m = re.search(r'estimated_lift_pct:\s*([\d.]+|null)', content)
    lift_raw = m.group(1) if m else "null"
    proposal["estimated_lift_pct"] = float(lift_raw) if lift_raw != "null" else None

    return proposal


def update_proposal_review(path: Path, reviewer: str, decision: str, notes: str):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    now = datetime.utcnow().isoformat() + "Z"
    content = re.sub(r'(  reviewer:\s*).*', rf'\g<1>"{reviewer}"', content, count=1)
    content = re.sub(r'(  reviewed_at:\s*).*', rf'\g<1>"{now}"', content, count=1)
    content = re.sub(r'(  decision:\s*).*', rf'\g<1>"{decision}"', content, count=1)
    content = re.sub(r'(  notes:\s*).*', rf'\g<1>"{notes}"', content, count=1)
    content = re.sub(r'^status:.*', f'status: "{decision}d"', content, count=1, flags=re.M)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_diff_guidance(proposal: dict) -> str:
    """Generate a human-readable diff comment (not an actual git diff — no source edits)."""
    target_file = proposal["target_file"]
    parameter = proposal["parameter"]
    current = proposal["current_value"]
    proposed = proposal["proposed_value"]
    lift = proposal["estimated_lift_pct"]

    lines = [
        "─" * 70,
        f"PROPOSED CHANGE — {proposal['description']}",
        "─" * 70,
        f"File:      {target_file}",
        f"Parameter: {parameter}",
        f"Before:    {current}",
        f"After:     {proposed}",
        f"Est. lift: {lift:+.1f}pp meeting rate" if lift is not None else "Est. lift: not computed",
        f"Confidence: {proposal['confidence']}",
        "",
        "HOW TO APPLY THIS CHANGE:",
        f"  1. Open {target_file}",
        f"  2. Find: {parameter}",
        f"  3. Change value from {current} to {proposed}",
        "  4. Run: python3 -m pytest tests/ -q",
        "  5. Fix any failing tests",
        f"  6. Commit: git add {target_file} && git commit -m \"learning: {proposal['description'][:60]} (v{proposal['version']})\"",
        "  7. This APPROVED_LEARNINGS.md has already been updated.",
        "─" * 70,
    ]
    return "\n".join(lines)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def append_to_approved_learnings(proposal: dict, reviewer: str, notes: str):
    version = proposal["version"]
    today = date.today().isoformat()
    lift = proposal["estimated_lift_pct"]
    lift_str = f"{lift:+.1f}%" if lift is not None else "TBD"

    entry = f"""
## v{version} — {proposal['description']}
- **Date**: {today}
- **Reviewer**: {reviewer}
- **Proposal file**: {_rel(proposal['_path'])}
- **File changed**: {proposal['target_file']}
- **Parameter**: {proposal['parameter']}
- **Before**: {proposal['current_value']}
- **After**: {proposal['proposed_value']}
- **Estimated lift**: {lift_str} meeting rate improvement
- **Actual lift** (if measured): TBD
- **Notes**: {notes}
"""
    with open(APPROVED_LEARNINGS, "a", encoding="utf-8") as f:
        f.write(entry)


def append_audit(entry: dict):
    today = date.today().isoformat()
    audit_file = AUDIT_DIR / f"{today}_audit.jsonl"
    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run(proposal_path: Path, decision: str, reviewer: str, notes: str):
    if not proposal_path.exists():
        print(f"ERROR: Proposal not found: {proposal_path}")
        sys.exit(1)

    proposal = load_proposal(proposal_path)
    print(f"\nProposal: v{proposal['version']} — {proposal['description']}")
    print(f"Decision: {decision.upper()} by {reviewer}")

    # Block hard gate changes from automated promotion
    if proposal["change_type"] in HARD_GATE_CHANGE_TYPES and decision == "approve":
        print("\nERROR: Hard gate changes require explicit user sign-off.")
        print("This proposal cannot be processed by promote_learning.py.")
        print("Contact your team lead directly to discuss this change.")
        sys.exit(1)

    # Check confidence for approvals
    if decision == "approve" and proposal["confidence"] == "low":
        print(f"\nWARNING: Proposal confidence is 'low'. Run evaluate_proposal.py first.")
        print("Proceeding anyway — you acknowledged this risk by choosing --decision approve.")

    # Always run tests first
    if not run_tests():
        print("\nERROR: Test suite failed. Fix failing tests before promoting this learning.")
        print("No changes were made.")
        sys.exit(1)

    print("\nTest suite passed.")

    update_proposal_review(proposal_path, reviewer, decision, notes)

    if decision == "approve":
        diff_guidance = generate_diff_guidance(proposal)
        diff_path = proposal_path.with_suffix(".diff_guidance.txt")
        with open(diff_path, "w", encoding="utf-8") as f:
            f.write(diff_guidance)

        proposal["_path"] = proposal_path
        append_to_approved_learnings(proposal, reviewer, notes)

        print("\n" + diff_guidance)
        print(f"\nDiff guidance written to: {diff_path}")
        print(f"APPROVED_LEARNINGS.md updated.")

    else:
        print(f"\nProposal rejected. Reason: {notes}")
        print("No changes made to any source file.")
        print(f"Proposal status updated to 'rejected' in: {proposal_path.name}")

    append_audit({
        "ts": datetime.utcnow().isoformat() + "Z",
        "script": "promote_learning.py",
        "action": "promote",
        "proposal": proposal_path.name,
        "version": proposal["version"],
        "decision": decision,
        "reviewer": reviewer,
        "notes": notes,
        "change_type": proposal["change_type"],
        "target_file": proposal["target_file"],
        "current_value": proposal["current_value"],
        "proposed_value": proposal["proposed_value"],
        "estimated_lift_pct": proposal["estimated_lift_pct"],
    })


def main():
    parser = argparse.ArgumentParser(description="Generate diff guidance for an approved proposal")
    parser.add_argument("--proposal", required=True, help="Path to proposal YAML file")
    parser.add_argument("--decision", required=True, choices=["approve", "reject"],
                        help="Approval decision")
    parser.add_argument("--reviewer", required=True, help="Reviewer name")
    parser.add_argument("--notes", default="", help="Optional review notes")
    args = parser.parse_args()
    run(Path(args.proposal), args.decision, args.reviewer, args.notes)


if __name__ == "__main__":
    main()
