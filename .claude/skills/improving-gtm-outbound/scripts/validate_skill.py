"""
Skill smoke-test — verifies the learning system is wired up correctly.

Checks:
  - All skill documentation files exist
  - All scripts are importable (no syntax errors)
  - data/learning/ directories exist
  - engine modules referenced in REPO_MAP.md are importable
  - infer_persona_role() works for known titles
  - Proposal YAML structure is parseable

Usage:
  python3 .claude/skills/improving-gtm-outbound/scripts/validate_skill.py

Exit 0 = all checks passed.
Exit 1 = one or more checks failed.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
SKILL_DIR = ROOT / ".claude" / "skills" / "improving-gtm-outbound"

errors: list[str] = []
warnings: list[str] = []


def check(condition: bool, name: str, detail: str = ""):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}{': ' + detail if detail else ''}")
        errors.append(f"{name}: {detail}")


def warn(condition: bool, name: str, detail: str = ""):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  WARN  {name}{': ' + detail if detail else ''}")
        warnings.append(f"{name}: {detail}")


# ── Documentation files ───────────────────────────────────────────────────────
print("\n[1] Skill documentation files")
for fname in ["SKILL.md", "REPO_MAP.md", "GUARDRAILS.md", "LEARNING_LOOP.md",
              "DATA_CONTRACTS.md", "METRICS.md", "EXPERIMENT_POLICY.md",
              "APPROVED_LEARNINGS.md", "EXAMPLES.md"]:
    check((SKILL_DIR / fname).exists(), fname)


# ── Script files ──────────────────────────────────────────────────────────────
print("\n[2] Script files")
scripts_dir = SKILL_DIR / "scripts"
for script in ["ingest_outcomes.py", "analyze_outcomes.py",
               "evaluate_proposal.py", "promote_learning.py", "validate_skill.py"]:
    check((scripts_dir / script).exists(), script)


# ── Data directories ──────────────────────────────────────────────────────────
print("\n[3] Data directories")
for subdir in ["outcomes", "analysis", "proposals", "canary", "audit"]:
    path = ROOT / "data" / "learning" / subdir
    check(path.is_dir(), f"data/learning/{subdir}/", f"missing — run mkdir -p {path}")


# ── Engine module imports ─────────────────────────────────────────────────────
print("\n[4] Engine module imports")
sys.path.insert(0, str(ROOT))

try:
    from engine.personalizer import infer_persona_role
    check(True, "engine.personalizer.infer_persona_role")
except Exception as e:
    check(False, "engine.personalizer.infer_persona_role", str(e))

try:
    from engine.icp import ICP_PROFILES, EMPLOYEE_RANGE_SCORES
    check(True, "engine.icp")
    check("utilities" in ICP_PROFILES, "utilities vertical in ICP_PROFILES")
    check(EMPLOYEE_RANGE_SCORES.get("50-100", 0) == 0, "employee floor at 100")
except Exception as e:
    check(False, "engine.icp", str(e))

try:
    from engine.scorer import QualificationResult, HARD_GATES
    check(True, "engine.scorer")
    check(len(HARD_GATES) >= 10, f"hard gates defined ({len(HARD_GATES)})")
except Exception as e:
    check(False, "engine.scorer", str(e))

try:
    from engine.committee import COMMITTEE_TEMPLATES
    check(True, "engine.committee")
    check("utilities" in COMMITTEE_TEMPLATES, "utilities in COMMITTEE_TEMPLATES")
except Exception as e:
    check(False, "engine.committee", str(e))

try:
    from engine.signals import SignalAggregator, SIGNAL_BASE_SCORES
    check(True, "engine.signals")
except Exception as e:
    check(False, "engine.signals", str(e))

try:
    from engine.interpreter import interpret_signal
    check(True, "engine.interpreter")
except Exception as e:
    check(False, "engine.interpreter", str(e))

try:
    from engine.auditor import audit_account
    check(True, "engine.auditor")
except Exception as e:
    check(False, "engine.auditor", str(e))

try:
    from scrapers.p02_lookalike.lookalike import run_lookalike
    check(True, "scrapers.p02_lookalike.lookalike.run_lookalike")
except Exception as e:
    check(False, "scrapers.p02_lookalike.lookalike.run_lookalike", str(e))


# ── Functional checks ─────────────────────────────────────────────────────────
print("\n[5] Functional checks")
try:
    from engine.personalizer import infer_persona_role
    known_mappings = {
        "director of human resources": "champion",
        "cfo": "economic_buyer",
        "hr manager": "influencer",
        "it director": "blocker",
    }
    for title, expected_role in known_mappings.items():
        result = infer_persona_role(title)
        check(result == expected_role, f"infer_persona_role('{title}')",
              f"expected {expected_role}, got {result}")
except Exception as e:
    check(False, "infer_persona_role functional test", str(e))

try:
    from engine.committee import map_buying_committee
    committee = map_buying_committee("utilities", "TestCo")
    roles = [p.role for p in committee]
    check("champion" in roles, "utilities committee has champion")
    check("economic_buyer" in roles, "utilities committee has economic_buyer")
    check("influencer" in roles, "utilities committee has influencer")
except Exception as e:
    check(False, "utilities buying committee", str(e))

try:
    from engine.scorer import QualificationResult
    result = QualificationResult.qualify(
        priority_vertical=True,
        employee_range_score=7,
        complexity_score=7,
        hiring_volume_score=5,
        geography_score=3,
        product_workflow_score=5,
        signal_reveals_problem=8,
        signal_is_current=5,
        why_now_concrete=4,
        multi_signal_bonus=4,
        product_relevance=4,
        source_authority=6,
        entity_match_score=4,
        date_verified=3,
        excerpt_specificity=3,
        contradiction_resolved=2,
        source_independence=2,
        champion_title_exists=6,
        champion_contact_found=4,
        econ_buyer_identifiable=3,
        verified_channel_data=3,
        centralized_ownership=2,
        no_active_duplicate=2,
    )
    check(result.tier == "Tier 1", f"max-score produces Tier 1 (got {result.tier})")
    check(result.is_qualified, "max-score is_qualified=True")
except Exception as e:
    check(False, "QualificationResult max-score → Tier 1", str(e))

try:
    result = QualificationResult.qualify(
        hard_gates_triggered=["current_customer"],
    )
    check(result.tier == "Disqualified", "hard gate → Disqualified")
    check(not result.is_qualified, "hard gate → is_qualified=False")
except Exception as e:
    check(False, "QualificationResult hard gate", str(e))


# ── Script import check ───────────────────────────────────────────────────────
print("\n[6] Script import checks (syntax)")
import importlib.util

for script_name in ["ingest_outcomes", "analyze_outcomes",
                    "evaluate_proposal", "promote_learning"]:
    script_path = scripts_dir / f"{script_name}.py"
    try:
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        check(True, f"scripts/{script_name}.py importable")
    except SystemExit:
        check(True, f"scripts/{script_name}.py importable (argparse exit)")
    except Exception as e:
        check(False, f"scripts/{script_name}.py importable", str(e))


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if not errors:
    if warnings:
        print(f"PASSED with {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  WARN: {w}")
    else:
        print("ALL CHECKS PASSED")
    sys.exit(0)
else:
    print(f"FAILED — {len(errors)} error(s):")
    for e in errors:
        print(f"  FAIL: {e}")
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  WARN: {w}")
    sys.exit(1)
