"""
HR Cloud ABM Intelligence Engine — Main Pipeline
================================================
Discovers, scores, and prioritizes accounts across all verticals.
Outputs Apollo-ready CSV with ICP scores, buying committee, and personalized outreach.

Usage:
  python3 pipeline/run.py --vertical healthcare --state TX
  python3 pipeline/run.py --vertical education --state FL --min-score 60
  python3 pipeline/run.py --vertical all --max-accounts 200 --output apollo
  python3 pipeline/run.py --vertical manufacturing --output sequences
"""

import argparse
import csv
import sys
import time
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.shared.ddg import ddg_search
from scrapers.shared.fetcher import fetch_text
from scrapers.shared.verifier import verify_domain

from engine.signals import Signal, SignalAggregator
from engine.icp import compute_icp_score, ICP_PROFILES
from engine.scorer import CompositeScore
from engine.committee import map_buying_committee, champion_title, economic_buyer_title
from engine.personalizer import generate_outreach, build_first_line, SOCIAL_PROOF
from engine.interpreter import interpret_signal
from engine.evidence import Evidence, EvidenceLedger
from engine.auditor import audit_account

from abm.account import Account, ACCOUNT_CSV_FIELDS
from abm.tiers import classify
from abm.apollo_export import export_to_apollo, export_sequences

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── Query banks per vertical ──────────────────────────────────────────────────
VERTICAL_QUERIES = {
    "healthcare": [
        ('"home health" "new hire packet" filetype:pdf site:.com', "pdf_new_hire_packet", "A"),
        ('"caregiver" "new hire packet" filetype:pdf site:.com', "pdf_new_hire_packet", "A"),
        ('"assisted living" "new hire packet" filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"hospice" "new hire packet" OR "employment application" filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"behavioral health" "new employee packet" filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"ADP Workforce Now" "home health" OR "senior living" HR job', "adp_confirmed", "B"),
        ('"ADP Run" "home care" OR "caregiver" payroll HR job', "adp_confirmed", "B"),
        ('"credentialing coordinator" "home health" OR "assisted living" job 2025', "credential_complexity", "C"),
        ('"CMS deficiency" "staffing" OR "staff training" "nursing home" 2025', "cms_deficiency", "A"),
        ('"caregiver" "now hiring" "multiple locations" site:.com', "caregiver_hiring_surge", "C"),
        ('"home health" HR coordinator "process new hire" job 2025', "job_manual_task", "B"),
        ('"senior living" "acquired" OR "merger" "HR" 2025', "acquisition", "C"),
        ('"new HR director" "home health" OR "senior care" 2025', "new_hr_leader", "C"),
        ('"HRSA grant" "home health" OR "home care" "hiring" 2025', "grant_award", "B"),
        ('"behavioral health" "new facility" OR "new location" "hiring" 2025', "facility_expansion", "C"),
    ],
    "education": [
        ('"new hire packet" site:.k12.tx.us filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"new hire packet" site:.k12.fl.us filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"new hire packet" site:.k12.ga.us filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"new hire packet" site:.k12.ca.us filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"new employee packet" "school district" filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"Head Start" "new employee packet" filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"substitute teacher" "new hire packet" filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"HRIS" "school district" RFP 2025', "rfp_hris", "B"),
        ('"ADP Workforce Now" "school district" HR job', "adp_confirmed", "B"),
        ('"new superintendent" "school district" 2025', "new_hr_leader", "C"),
        ('"ESSER" "staffing" "hire" school district 2025', "grant_award", "B"),
        ('"new school opening" OR "new campus" "hiring" district 2025', "facility_expansion", "C"),
        ('"charter school" "new hire" "orientation" "paperwork" 2025', "job_manual_task", "C"),
        ('"school district" "HR coordinator" "new hire paperwork" "process" job 2025', "job_manual_task", "B"),
        ('"community college" "new hire packet" OR "new employee packet" filetype:pdf', "pdf_new_hire_packet", "A"),
    ],
    "manufacturing": [
        ('"manufacturing" "new hire packet" filetype:pdf site:.com', "pdf_new_hire_packet", "A"),
        ('"ADP Workforce Now" "manufacturing" OR "plant" HR coordinator job', "adp_confirmed", "B"),
        ('"OSHA" "willful" OR "repeat" violation manufacturing 2025', "osha_citation", "A"),
        ('"manufacturing" "HR generalist" "ADP" "payroll" job 2025', "adp_confirmed", "C"),
        ('"plant" "HR coordinator" "new hire" "onboarding" "paper" OR "manual" job 2025', "job_manual_task", "B"),
        ('"manufacturing" "acquired" "HR" "standardize" "onboarding" 2025', "acquisition", "C"),
        ('"logistics" "distribution" "HR coordinator" "ADP" job 2025', "adp_confirmed", "C"),
        ('"manufacturing" "new facility" "hiring" "HR" 2025', "facility_expansion", "C"),
        ('"construction" "ADP Workforce Now" "HR" "certified payroll" job', "adp_confirmed", "B"),
        ('"manufacturing" "employee communication" "frontline" OR "shop floor" job 2025', "frontline_comm_gap", "C"),
        ('"private equity" "manufacturing" "portfolio" "HR" standardize 2025', "acquisition", "C"),
        ('"new HR director" "manufacturing" OR "plant" 2025', "new_hr_leader", "C"),
    ],
    "nonprofit": [
        ('"nonprofit" "new hire packet" filetype:pdf site:.org', "pdf_new_hire_packet", "A"),
        ('"501c3" "new employee" "please complete" "return to HR" filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"nonprofit" "HR coordinator" "ADP" "payroll" job 2025', "adp_confirmed", "C"),
        ('"social services" "new hire" "orientation" "packet" job 2025', "job_manual_task", "C"),
        ('"nonprofit" "first HR hire" OR "building HR" job 2025', "new_hr_leader", "C"),
        ('"grant award" "workforce" "nonprofit" "hiring" 2025', "grant_award", "B"),
        ('"faith-based" "nonprofit" "new hire packet" filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"community organization" "HR coordinator" "onboarding" "manual" job 2025', "job_manual_task", "C"),
        ('"ADP Run" "nonprofit" "payroll" HR job 2025', "adp_confirmed", "C"),
    ],
    "government": [
        ('"county" "new hire packet" filetype:pdf site:.gov', "pdf_new_hire_packet", "A"),
        ('"municipality" "new employee" "complete and return" HR filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"HRIS" "county" OR "city" RFP 2025', "rfp_hris", "A"),
        ('"ADP Workforce Now" "county" OR "municipality" HR job', "adp_confirmed", "B"),
        ('"new HR director" "county" OR "city" 2025', "new_hr_leader", "C"),
        ('site:sam.gov "human resources" "HRIS" OR "onboarding" contract award 2025', "sam_contract_award", "A"),
        ('"transit authority" "new hire" "onboarding" "forms" filetype:pdf', "pdf_new_hire_packet", "A"),
        ('"special district" "HR coordinator" "ADP" job 2025', "adp_confirmed", "C"),
    ],
}

SKIP_DOMAINS = {
    "linkedin", "indeed", "glassdoor", "ziprecruiter", "monster", "careerbuilder",
    "simplyhired", "reddit", "quora", "youtube", "wikipedia", "bamboohr", "gusto",
    "rippling", "adp", "paychex", "workday", "ukg", "shrm", "forbes",
    "businessinsider", "medium", "blogspot", "hrcloud", "hrdive",
}

MODERN_HRIS_SIGNALS = ["workday", "successfactors", "ceridian", "infor hcm",
                        "ukg pro", "paycom", "paycor", "kronos", "oracle hcm"]


def should_skip(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return True
    return any(skip in host for skip in SKIP_DOMAINS)


def detect_adp(text: str) -> tuple[str, str]:
    import re
    if re.search(r"ADP\s+Workforce\s+Now", text, re.I):
        return "confirmed", "ADP Workforce Now"
    if re.search(r"ADP\s+Run\b", text, re.I):
        return "confirmed", "ADP Run"
    if re.search(r"ADP\s+TotalSource", text, re.I):
        return "confirmed", "ADP TotalSource"
    if re.search(r"(experience|proficiency|familiar|knowledge)\s+with\s+ADP", text, re.I):
        return "strongly_likely", "ADP (product unspecified)"
    if re.search(r"process\s+payroll\s+(in|using|with)\s+ADP", text, re.I):
        return "strongly_likely", "ADP (payroll confirmed)"
    return "not_found", ""


def detect_modern_hris(text: str) -> str:
    t = text.lower()
    for hris in MODERN_HRIS_SIGNALS:
        if hris in t:
            return hris
    return ""


def find_negative_evidence(domain: str, combined_text: str, signal_type: str) -> list:
    """
    Adversarial pass: look for reasons NOT to qualify this account.
    Returns list of dicts describing each negative signal found.
    """
    negatives = []
    text_lower = combined_text.lower()

    DISQUALIFIERS = {
        "workday":          ("exact_workflow_already_solved", "Workday detected"),
        "successfactors":   ("exact_workflow_already_solved", "SAP SuccessFactors detected"),
        "dayforce":         ("exact_workflow_already_solved", "Ceridian Dayforce detected"),
        "ukg pro":          ("exact_workflow_already_solved", "UKG Pro detected"),
        "oracle hcm":       ("exact_workflow_already_solved", "Oracle HCM detected"),
    }
    for kw, (category, label) in DISQUALIFIERS.items():
        if kw in text_lower:
            negatives.append({
                "type": "modern_hris_full_suite",
                "hris_fit_category": category,
                "label": label,
                "severity": "warning",  # not a hard gate — classify, don't disqualify
            })

    # Contractor/volunteer only
    if any(kw in text_lower for kw in ["volunteer only", "contractors only", "not for employees"]):
        negatives.append({
            "type": "wrong_audience",
            "label": "Content appears to be for volunteers or contractors only",
            "severity": "fatal",
        })

    # Staffing agency (they place workers, not buyers)
    if any(kw in text_lower for kw in ["staffing agency", "temporary staffing", "we staff"]):
        negatives.append({
            "type": "staffing_agency",
            "label": "Company appears to be a staffing agency, not an employer",
            "severity": "warning",
        })

    # Archived/old content
    if any(kw in text_lower for kw in ["archived", "this page is no longer", "outdated policy"]):
        negatives.append({
            "type": "stale_content",
            "label": "Content may be archived or outdated",
            "severity": "warning",
        })

    return negatives


def run_vertical(vertical: str, state: str = "", min_score: int = 50,
                  max_accounts: int = 500) -> list[Account]:
    queries = VERTICAL_QUERIES.get(vertical, [])
    if state:
        queries = [(q.replace("[state]", state), st, tier) for q, st, tier in queries]

    print(f"\n{'='*70}", flush=True)
    print(f"Running vertical: {vertical.upper()} | Queries: {len(queries)}", flush=True)
    if state:
        print(f"State filter: {state}", flush=True)
    print(f"Min composite score: {min_score}", flush=True)

    seen_domains: set = set()
    raw_accounts: list[Account] = []

    for i, (query, signal_type, tier) in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] {query[:80]}", flush=True)
        results = ddg_search(query, max_results=10)
        print(f"  DDG: {len(results)} results", flush=True)

        for r in results[:5]:
            url = r.get("href", "")
            if not url or should_skip(url):
                continue

            canonical, domain_status = verify_domain(url)
            if not canonical or canonical in seen_domains:
                continue

            snippet = r.get("body", "")
            title = r.get("title", "")

            # Fetch page
            page_text = fetch_text(url)
            combined = snippet + " " + page_text

            # Detect technographic signals
            adp_status, adp_product = detect_adp(combined)
            hris_incumbent = detect_modern_hris(combined)
            has_paper = bool(any(kw in combined.lower() for kw in [
                "new hire packet", "complete and return", "bring paperwork",
                "fax completed", "mail completed", "paper forms", "print and sign",
            ]))

            # Build excerpt early (needed for interpretation and signal building)
            excerpt = snippet[:200] if snippet else combined[:200]

            # Negative evidence pass (before scoring)
            neg_evidence = find_negative_evidence(canonical, combined, signal_type)
            has_fatal_negative = any(n["severity"] == "fatal" for n in neg_evidence)
            if has_fatal_negative:
                print(f"  ✗ NEGATIVE EVIDENCE: {neg_evidence[0]['label'][:60]}", flush=True)
                continue

            # Signal interpretation (pure layer)
            interp = interpret_signal(
                signal_type=signal_type,
                evidence_tier=tier,
                evidence_excerpt=excerpt,
                signal_date="",
                freshness_score=75 if tier in ("A","B") else 50,
                hris_incumbent=hris_incumbent,
                adp_status=adp_status,
                vertical=vertical,
                signal_count=1,
                has_contradiction=bool(neg_evidence),
                entity_confirmed=(domain_status == "verified"),
            )

            # Build primary signal
            signal = Signal(
                signal_type=signal_type,
                tier=tier,
                source_url=url,
                source_domain=canonical,
                evidence_excerpt=excerpt[:200],
                signal_date="",
                what_it_proves=f"Evidence of {signal_type.replace('_', ' ')} at {canonical}",
            )

            agg = SignalAggregator([signal])
            signal_score = agg.signal_score()
            has_tier_ab = agg.has_tier_a_or_b()

            # ICP scoring
            icp = compute_icp_score(
                employee_range="",
                industry=ICP_PROFILES.get(vertical, {}).get("description", vertical),
                vertical=vertical,
                is_multi_location=any(kw in combined.lower() for kw in
                    ["multiple locations", "multi-location", "multi-site"]),
                is_frontline=any(kw in combined.lower() for kw in
                    ["frontline", "hourly", "caregiver", "aide", "shift"]),
                adp_status=adp_status,
                hris_incumbent=hris_incumbent,
                has_paper_evidence=has_paper,
                signal_score=signal_score,
                has_tier_ab=has_tier_ab,
                signal_count=1,
                trigger_signal_types=[signal_type],
            )

            # Composite score
            comp = CompositeScore.compute(
                icp_score=icp.total,
                signal_score=signal_score,
                signal_count=1,
                has_tier_ab=has_tier_ab,
                domain_status=domain_status,
                all_signals_stale=False,
                employee_count_confirmed_low=False,
                modern_hris_confirmed=bool(hris_incumbent),
            )

            if comp.final_score < min_score:
                continue

            # Tier + actions
            tier_decision = classify(comp.final_score, comp.rejection_reason)

            # Buying committee
            committee = map_buying_committee(vertical, title[:60])
            champ = champion_title(vertical)
            econ = economic_buyer_title(vertical)
            champ_persona = next((p for p in committee if p.role == "champion"), None)

            # Personalization
            first_line = build_first_line(signal_type, excerpt, title[:60], url)
            proof = SOCIAL_PROOF.get(vertical, SOCIAL_PROOF["default"])

            # Determine product
            product = "Onboard"
            if any(kw in combined.lower() for kw in ["frontline", "caregiver communication",
                "employee app", "deskless"]):
                product = "Onboard+Workmates"

            outreach_pkg = generate_outreach(
                company_name=title[:60],
                vertical=vertical,
                account_tier=tier_decision.tier,
                persona_role="champion",
                persona_title=champ,
                persona_hook=champ_persona.best_hook if champ_persona else "",
                persona_linkedin_note=champ_persona.linkedin_note if champ_persona else "",
                best_signal_type=signal_type,
                evidence_excerpt=excerpt,
                source_url=url,
                adp_status=adp_status,
                best_hr_cloud_product=product,
            )

            account = Account(
                company_name=title[:80],
                canonical_domain=canonical,
                domain_status=domain_status,
                industry=ICP_PROFILES.get(vertical, {}).get("description", vertical),
                vertical=vertical,
                adp_status=adp_status,
                adp_product=adp_product,
                hris_incumbent=hris_incumbent,
                has_paper_evidence=has_paper,
                primary_signal_type=signal_type,
                primary_signal_tier=tier,
                primary_evidence_excerpt=excerpt[:200],
                primary_evidence_url=url,
                signal_count=1,
                trigger_signal_types=[signal_type],
                icp_firmographic=icp.firmographic,
                icp_technographic=icp.technographic,
                icp_behavioral=icp.behavioral,
                icp_buying_trigger=icp.buying_trigger,
                icp_score=icp.total,
                signal_score=signal_score,
                composite_score=comp.final_score,
                account_tier=tier_decision.tier,
                is_qualified=tier_decision.tier not in ("Disqualified",),
                rejection_reason=comp.rejection_reason,
                champion_title=champ,
                economic_buyer_title=econ,
                best_hr_cloud_product=product,
                safe_first_line=first_line,
                outreach_angle=champ_persona.best_hook if champ_persona else "",
                proof_point=proof,
                recommended_cta=outreach_pkg.cta,
                email_subject_a=outreach_pkg.subject_line_a,
                email_subject_b=outreach_pkg.subject_line_b,
                email_1_body=outreach_pkg.email_1_body,
                email_2_body=outreach_pkg.email_2_body,
                email_3_body=outreach_pkg.email_3_body,
                linkedin_note=outreach_pkg.linkedin_connection_note,
                next_action=tier_decision.next_action,
                source_scraper=f"pipeline/run.py:{vertical}",
                # New fields from skills package
                intent_score=0,      # computed by QualificationResult in enrich.py
                confidence_score=0,
                contactability_score=0,
                hard_gate_status=bool(comp.rejection_reason and "gate" in comp.rejection_reason.lower()),
                hard_gate_reason=comp.rejection_reason if "gate" in comp.rejection_reason.lower() else "",
                signal_strength=interp.signal_strength,
                signal_confidence=interp.confidence,
                signal_safe_to_mention=interp.safe_to_mention,
                why_now=interp.why_now or "",
                negative_evidence=neg_evidence,
                false_positive_reason="; ".join(n["label"] for n in neg_evidence) if neg_evidence else "",
                entity_type="employer",
                hris_fit_category=interp.hris_fit_category,
                next_research_action=tier_decision.next_action,
            )

            seen_domains.add(canonical)
            raw_accounts.append(account)
            print(f"  ✓ [{tier_decision.tier}] {title[:50]} [{canonical}] score={comp.final_score}", flush=True)

            if len(raw_accounts) >= max_accounts:
                break

        time.sleep(3)

    return raw_accounts


def save_accounts_csv(accounts: list[Account], label: str = "") -> Path:
    from abm.account import ACCOUNT_CSV_FIELDS
    from dataclasses import asdict
    ts = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M")
    suffix = f"_{label}" if label else ""
    path = DATA_DIR / f"abm_accounts{suffix}_{ts}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ACCOUNT_CSV_FIELDS)
        writer.writeheader()
        for a in sorted(accounts, key=lambda x: -x.composite_score):
            row = {k: getattr(a, k, "") for k in ACCOUNT_CSV_FIELDS}
            writer.writerow(row)
    return path


def print_summary(accounts: list[Account], vertical: str):
    t1 = [a for a in accounts if a.account_tier == "Tier 1"]
    t2 = [a for a in accounts if a.account_tier == "Tier 2"]
    t3 = [a for a in accounts if a.account_tier == "Tier 3"]
    dq = [a for a in accounts if a.account_tier == "Disqualified"]

    print(f"\n{'='*70}", flush=True)
    print(f"ABM Pipeline Complete — {vertical.upper()}", flush=True)
    print(f"  Tier 1 (outreach-ready): {len(t1)}", flush=True)
    print(f"  Tier 2 (semi-personalized): {len(t2)}", flush=True)
    print(f"  Tier 3 (nurture): {len(t3)}", flush=True)
    print(f"  Disqualified: {len(dq)}", flush=True)
    print(f"  Total qualified: {len(t1) + len(t2)}", flush=True)
    if t1:
        print(f"\n  Top Tier 1 accounts:", flush=True)
        for a in sorted(t1, key=lambda x: -x.composite_score)[:5]:
            print(f"    {a.composite_score:3d} | {a.company_name[:40]} [{a.canonical_domain}]", flush=True)


def main():
    parser = argparse.ArgumentParser(description="HR Cloud ABM Intelligence Pipeline")
    parser.add_argument("--vertical", default="healthcare",
                        choices=list(VERTICAL_QUERIES.keys()) + ["all"],
                        help="Target vertical (or 'all')")
    parser.add_argument("--state", default="", help="Two-letter state code filter")
    parser.add_argument("--min-score", type=int, default=50,
                        help="Minimum composite score to include (default: 50)")
    parser.add_argument("--max-accounts", type=int, default=500,
                        help="Max accounts per vertical (default: 500)")
    parser.add_argument("--output", choices=["csv", "apollo", "sequences", "all"],
                        default="apollo", help="Output format")
    parser.add_argument("--min-icp-score", type=int, default=0)
    parser.add_argument("--min-intent-score", type=int, default=0)
    parser.add_argument("--min-confidence-score", type=int, default=0)
    parser.add_argument("--max-signal-age-days", type=int, default=180)
    parser.add_argument("--require-primary-evidence", action="store_true")
    parser.add_argument("--require-corroboration", action="store_true")
    parser.add_argument("--audit-only", action="store_true",
                        help="Load most recent CSV and run audit pass only")
    parser.add_argument("--research-only", action="store_true")
    parser.add_argument("--no-contact-enrichment", action="store_true")
    parser.add_argument("--include-rejected", action="store_true")
    args = parser.parse_args()

    if args.audit_only:
        csvs = sorted(DATA_DIR.glob("abm_accounts_*.csv"), key=lambda p: p.stat().st_mtime)
        if not csvs:
            print("No abm_accounts_*.csv found. Run pipeline first.", flush=True)
            sys.exit(1)
        import csv as _csv
        from engine.auditor import audit_accounts
        with open(csvs[-1], newline="", encoding="utf-8") as f:
            rows = list(_csv.DictReader(f))
        audit_results = audit_accounts(rows)
        pass_count = sum(1 for r in audit_results.values() if r.audit_status in ("pass","pass_with_warning"))
        reject_count = sum(1 for r in audit_results.values() if r.audit_status == "reject")
        print(f"\nAudit complete: {len(rows)} accounts")
        print(f"  Pass: {pass_count} | Reject: {reject_count}")
        for domain, ar in audit_results.items():
            if ar.audit_status in ("reject", "return_to_research"):
                print(f"  [{ar.audit_status.upper()}] {domain}: {ar.rejection_reason or ar.required_fix}")
        sys.exit(0)

    verticals = list(VERTICAL_QUERIES.keys()) if args.vertical == "all" else [args.vertical]
    all_accounts: list[Account] = []

    for vertical in verticals:
        accounts = run_vertical(
            vertical=vertical,
            state=args.state,
            min_score=args.min_score,
            max_accounts=args.max_accounts,
        )
        all_accounts.extend(accounts)
        print_summary(accounts, vertical)

    label = args.vertical + (f"_{args.state}" if args.state else "")

    if args.output in ("csv", "all"):
        path = save_accounts_csv(all_accounts, label)
        print(f"\nCSV: {path}", flush=True)

    if args.output in ("apollo", "all"):
        export_to_apollo(all_accounts, label)

    if args.output in ("sequences", "all"):
        export_sequences(all_accounts, label)

    print(f"\nDone. {len(all_accounts)} total accounts processed.", flush=True)


if __name__ == "__main__":
    main()
