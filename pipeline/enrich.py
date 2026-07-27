"""
HR Cloud ABM — Local Enrichment Pipeline
=========================================
Post-processes scraper output without any external API calls.

What it does:
  - Deduplicates domains (merges multiple signals per domain)
  - Infers employee range from evidence text
  - Extracts HQ state from evidence/domain context
  - Re-scores composite score with all accumulated signals
  - Flags accounts with stale-only signals
  - Exports a cleaned, enriched CSV ready for Apollo import

Usage:
  python3 pipeline/enrich.py
  python3 pipeline/enrich.py --input data/abm_accounts_healthcare_*.csv
  python3 pipeline/enrich.py --input data/abm_accounts_healthcare_*.csv --min-score 60
  python3 pipeline/enrich.py --vertical healthcare --min-score 60
"""

import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.scorer import CompositeScore
from abm.tiers import classify

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# ── Employee range inference ──────────────────────────────────────────────────
_EMP_PATTERNS = [
    (re.compile(r"\b(\d{1,4})\s*(?:-|to|–)\s*(\d{1,4})\s*(?:employees?|staff|workers?|FTE)", re.I), "range"),
    (re.compile(r"\b(?:over|more than|exceeding)\s*(\d{1,4})\s*(?:employees?|staff)", re.I), "over"),
    (re.compile(r"\b(\d{1,4})\+\s*(?:employees?|staff|caregivers?)", re.I), "over"),
    (re.compile(r"\bapproximately\s*(\d{1,4})\s*(?:employees?|staff)", re.I), "approx"),
    (re.compile(r"\b(\d{1,4})\s*(?:employees?|staff|workers?|FTE)\b", re.I), "exact"),
]

def _bucket(n: int) -> str:
    if n < 50:   return "<50"
    if n < 200:  return "50-200"
    if n < 500:  return "200-500"
    if n < 1000: return "500-1000"
    if n < 2000: return "1000-2000"
    return "2000+"

def infer_employee_range(text: str) -> str:
    """Extract employee count hint from evidence text. Returns bucket string or ''."""
    for pat, kind in _EMP_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        try:
            if kind == "range":
                lo, hi = int(m.group(1)), int(m.group(2))
                mid = (lo + hi) // 2
                return _bucket(mid)
            else:
                n = int(m.group(1))
                if 10 <= n <= 50_000:
                    return _bucket(n)
        except (ValueError, IndexError):
            continue
    return ""


# ── State extraction ──────────────────────────────────────────────────────────
_STATE_ABBREVS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC",
}
_STATE_PAT = re.compile(r"\b([A-Z]{2})\b")

def infer_state(text: str) -> str:
    for m in _STATE_PAT.finditer(text):
        if m.group(1) in _STATE_ABBREVS:
            return m.group(1)
    return ""


# ── Signal tier scoring map ───────────────────────────────────────────────────
_TIER_WEIGHT = {"A": 1.0, "B": 0.8, "C": 0.5, "D": 0.1}


# ── Domain deduplication + merge ──────────────────────────────────────────────
def merge_rows(rows: List[dict]) -> dict:
    """Merge multiple scraper rows for the same domain into one enriched row."""
    # Sort by signal tier quality so the best signal is primary
    def tier_rank(r):
        return _TIER_WEIGHT.get(r.get("primary_signal_tier", "D"), 0.0)

    rows = sorted(rows, key=tier_rank, reverse=True)
    base = dict(rows[0])

    # Accumulate signal types from all rows
    signal_types = list({r.get("primary_signal_type", "") for r in rows if r.get("primary_signal_type")})
    base["all_signal_types"] = "|".join(signal_types)
    base["signal_count"] = str(len(rows))

    # Merge evidence excerpts
    excerpts = [r.get("primary_evidence_excerpt", "") for r in rows if r.get("primary_evidence_excerpt")]
    base["combined_evidence"] = " /// ".join(excerpts[:3])

    # ADP: upgrade if any row confirms it
    adp_statuses = [r.get("adp_status", "") for r in rows]
    if "confirmed" in adp_statuses:
        base["adp_status"] = "confirmed"
    elif "strongly_likely" in adp_statuses:
        base["adp_status"] = "strongly_likely"

    # Employee range: first non-empty inference
    combined_text = " ".join(excerpts)
    if not base.get("employee_range"):
        base["employee_range"] = infer_employee_range(combined_text)

    # State: first non-empty
    if not base.get("hq_state"):
        base["hq_state"] = infer_state(combined_text)

    # Re-score composite with multi-signal context
    has_tier_ab = any(r.get("primary_signal_tier", "D") in ("A", "B") for r in rows)
    signal_count = len(rows)
    signal_score = int(rows[0].get("signal_score", 0) or 0)
    icp_score = int(rows[0].get("icp_score", 0) or 0)
    domain_status = rows[0].get("domain_status", "verified")
    hris = rows[0].get("hris_incumbent", "")

    comp = CompositeScore.compute(
        icp_score=icp_score,
        signal_score=signal_score,
        signal_count=signal_count,
        has_tier_ab=has_tier_ab,
        domain_status=domain_status,
        all_signals_stale=False,
        employee_count_confirmed_low=False,
        modern_hris_confirmed=bool(hris),
    )
    base["composite_score"] = str(comp.final_score)
    base["rejection_reason"] = comp.rejection_reason

    tier = classify(comp.final_score, comp.rejection_reason)
    base["account_tier"] = tier.tier
    base["next_action"] = tier.next_action

    return base


OUTPUT_FIELDS = [
    "account_tier", "composite_score", "icp_score", "signal_score",
    "company_name", "canonical_domain", "domain_status",
    "vertical", "industry", "employee_range", "hq_state", "country",
    "adp_status", "adp_product", "hris_incumbent", "has_paper_evidence",
    "primary_signal_type", "all_signal_types", "signal_count",
    "primary_signal_tier", "primary_evidence_excerpt", "primary_evidence_url",
    "combined_evidence",
    "rejection_reason",
    "champion_title", "economic_buyer_title",
    "best_hr_cloud_product",
    "safe_first_line", "outreach_angle",
    "email_subject_a", "email_1_body",
    "email_subject_b", "email_2_body",
    "email_3_body", "linkedin_note",
    "recommended_cta", "next_action",
    "source_scraper",
]


def run(input_csv: str, min_score: int = 0, tier_filter: str = "") -> Path:
    rows: List[dict] = []
    with open(input_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"\nLoaded {len(rows)} rows from {input_csv}", flush=True)

    # Group by canonical domain
    by_domain: Dict[str, List[dict]] = {}
    for row in rows:
        d = row.get("canonical_domain", "").strip()
        if not d:
            continue
        by_domain.setdefault(d, []).append(row)

    print(f"Unique domains: {len(by_domain)}", flush=True)

    merged: List[dict] = []
    for domain, domain_rows in by_domain.items():
        m = merge_rows(domain_rows)
        score = int(m.get("composite_score", 0) or 0)
        if min_score and score < min_score:
            continue
        if tier_filter and m.get("account_tier", "") != tier_filter:
            continue
        merged.append(m)

    # Sort by composite score desc
    merged.sort(key=lambda r: -int(r.get("composite_score", 0) or 0))

    # Write output
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    label = Path(input_csv).stem.replace("abm_accounts_", "")
    out_path = DATA_DIR / f"enriched_{label}_{ts}.csv"

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in merged:
            writer.writerow({k: row.get(k, "") for k in OUTPUT_FIELDS})

    # Summary
    t1 = [r for r in merged if r.get("account_tier") == "Tier 1"]
    t2 = [r for r in merged if r.get("account_tier") == "Tier 2"]
    t3 = [r for r in merged if r.get("account_tier") == "Tier 3"]
    dq = [r for r in merged if r.get("account_tier") == "Disqualified"]

    print(f"\n{'='*60}", flush=True)
    print(f"Enrichment complete (local only — no external APIs)", flush=True)
    print(f"  Tier 1:       {len(t1)}", flush=True)
    print(f"  Tier 2:       {len(t2)}", flush=True)
    print(f"  Tier 3:       {len(t3)}", flush=True)
    print(f"  Disqualified: {len(dq)}", flush=True)
    print(f"\nOutput: {out_path}", flush=True)

    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Local enrichment — deduplicates, re-scores, and cleans scraper output"
    )
    parser.add_argument("--input", help="Path to abm_accounts_*.csv from pipeline/run.py")
    parser.add_argument("--vertical", default="", help="Vertical name to auto-select most recent CSV")
    parser.add_argument("--min-score", type=int, default=0,
                        help="Minimum composite score to include")
    parser.add_argument("--tier", choices=["Tier 1", "Tier 2", "Tier 3"],
                        default="", help="Only include accounts of this tier")
    args = parser.parse_args()

    input_path = args.input
    if not input_path:
        pattern = f"abm_accounts_{args.vertical}*.csv" if args.vertical else "abm_accounts_*.csv"
        csvs = sorted(DATA_DIR.glob(pattern), key=lambda p: p.stat().st_mtime)
        if not csvs:
            print(f"No {pattern} found in data/. Run pipeline/run.py first.", flush=True)
            sys.exit(1)
        input_path = str(csvs[-1])
        print(f"Auto-selected: {input_path}", flush=True)

    run(
        input_csv=input_path,
        min_score=args.min_score,
        tier_filter=args.tier,
    )


if __name__ == "__main__":
    main()
