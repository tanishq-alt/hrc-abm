"""
Prompt 5: Workmates Frontline Communication Prospect Finder

Targets organizations with distributed/frontline workforces showing internal
communication and engagement pain — the ideal Workmates buyer profile.

Signals detected:
  - Internal comms manager job postings (multi-location, distributed)
  - Employee engagement roles for frontline/deskless workers
  - Employee app or intranet mentions for distributed workforce
  - ADP + multi-location + employee communication signals
  - Policy acknowledgment / mandatory-read pain
  - Senior care / home health / manufacturing comm roles

Output: data/workmates_leads.csv (canonical 25-column schema)

Run:
  python3 -u workmates_finder.py 2>&1 | tee /tmp/workmates_finder.log
"""

import csv
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scrapers.shared.ddg import ddg_search
from scrapers.shared.fetcher import fetch_text
from scrapers.shared.schema import CANONICAL_FIELDS, make_row_from_dict
from scrapers.shared.verifier import verify_domain

OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "workmates_leads.csv"
OUTPUT_FILE.parent.mkdir(exist_ok=True)

# ── Search queries aligned to Prompt 5 signal families ──────────────────────
QUERIES = [
    # Signal A: Internal communication initiative
    '"internal communications manager" job "multi-location" OR "distributed"',
    '"internal communications" "frontline" OR "deskless" job posting',
    '"employee communications" "multi-site" OR "multiple locations" HR job',
    '"director of internal communications" "operations" OR "frontline" job 2025',

    # Signal B: Communication breakdown evidence
    '"employee app" OR "intranet" "distributed workforce" site:.org OR site:.com',
    '"communication gap" "frontline employees" OR "hourly workers" company',
    '"employees don\'t have email" OR "no corporate email" "communication" company',
    '"deskless workers" "communication" "challenge" OR "problem" company',

    # Signal C: Change management pressure
    '"change management" "frontline" "communication" job OR initiative',
    '"policy rollout" "multiple locations" OR "distributed team" challenge',
    '"mandatory training" "distributed employees" "track completion" company',

    # Signal D: Recognition / retention signals
    '"employee recognition" "frontline" OR "hourly" program job OR initiative',
    '"retention" "frontline workers" "engagement" "communication" company',
    '"caregiver retention" "communication" OR "engagement" program 2025',

    # Signal E: Mandatory-read / safety acknowledgment
    '"policy acknowledgment" "distributed employees" filetype:pdf',
    '"mandatory read" "multi-location" OR "distributed" employees company',
    '"safety acknowledgment" "sign-off" "frontline" OR "hourly" employees',
    '"employee handbook" "acknowledgment" "multiple locations" HR coordinator',

    # Signal F: ADP cross-sell overlay
    '"ADP Workforce Now" "multi-location" "employee communication"',
    '"ADP" "internal communications" "frontline" OR "multi-site" job',

    # Industry: Senior care / home health
    '"caregiver" "communication" "engagement" site:.com',
    '"home health" "employee communication" OR "internal comms" challenge',
    '"assisted living" "employee engagement" "multi-site" OR "multiple communities"',

    # Industry: Manufacturing / industrial
    '"manufacturing" "plant" "employee communication" "frontline" OR "shop floor"',
    '"shift workers" "communication" "challenge" OR "gap" manufacturing',
    '"factory" "employee app" OR "digital signage" "communication" company',

    # Industry: Retail / hospitality / logistics
    '"retail" "frontline employee" "communication" "distributed" job OR initiative',
    '"distribution center" "employee communication" "app" OR "platform" company',
    '"hotel" OR "hospitality" "employee communication" "multi-property" challenge',

    # General Workmates pain signals
    '"employee engagement" "frontline" OR "deskless" job posting 2025',
    '"internal comms" "no corporate email" "hourly" OR "part-time" employees',
    '"digital workplace" "frontline" "engagement" "implementation" job 2025',
]

# ── Skip list ────────────────────────────────────────────────────────────────
SKIP_DOMAINS = {
    "linkedin", "indeed", "glassdoor", "ziprecruiter", "monster",
    "careerbuilder", "simplyhired", "reddit", "quora", "youtube",
    "bamboohr", "gusto", "rippling", "adp", "paychex", "workday",
    "shrm", "forbes", "businessinsider", "medium", "blogspot",
    "connecteam", "staffbase", "poppulo", "firstup", "simpplr",
    "workvivo", "beekeeper", "guild", "marginedge", "zinc",
    "hrcloud", "hrdive", "aihr", "chron",
}

# ── Signal patterns for Workmates intent ────────────────────────────────────
COMM_SIGNAL_PATTERNS = [
    (re.compile(r"internal\s+comm(unication)?s?\s+manager", re.I), "internal_comms_role"),
    (re.compile(r"employee\s+(app|application|platform|portal).*multi.loc", re.I), "employee_app_multilocation"),
    (re.compile(r"policy\s+acknowledgment.*distributed", re.I), "policy_acknowledgment"),
    (re.compile(r"mandatory\s+(read|training).*multi.loc", re.I), "mandatory_read"),
    (re.compile(r"no\s+corporate\s+email.*frontline|deskless.*no.*(email|device)", re.I), "no_email_frontline"),
    (re.compile(r"frontline\s+(employee\s+)?comm(unication)?", re.I), "frontline_comm"),
    (re.compile(r"deskless\s+worker.*comm|comm.*deskless\s+worker", re.I), "deskless_worker_comm"),
    (re.compile(r"employee\s+recognition.*frontline|frontline.*recognition", re.I), "frontline_recognition"),
    (re.compile(r"caregiver.*retention.*comm|comm.*caregiver.*retention", re.I), "caregiver_retention_comm"),
    (re.compile(r"shift\s+worker.*comm(unication)?|comm.*shift\s+worker", re.I), "shift_worker_comm"),
    (re.compile(r"multi.site\s+employee.*comm|employee.*multi.site.*comm", re.I), "multisite_comm"),
    (re.compile(r"ADP.*multi.loc.*comm|multi.loc.*ADP.*comm", re.I), "adp_multilocation_comm"),
    (re.compile(r"employee\s+engagement.*frontline|frontline.*engagement", re.I), "frontline_engagement"),
]

INDUSTRY_KEYWORDS = {
    "Senior Living / Home Health": ["senior living", "assisted living", "home health", "home care", "hospice", "caregiver"],
    "Manufacturing": ["manufacturing", "plant", "factory", "shop floor", "production"],
    "Retail": ["retail", "store", "grocery", "supermarket"],
    "Hospitality": ["hotel", "hospitality", "restaurant", "resort"],
    "Logistics / Distribution": ["distribution", "logistics", "warehouse", "fulfillment"],
    "Healthcare": ["hospital", "medical", "clinic", "health system"],
    "Construction": ["construction", "contractor", "trades"],
    "Staffing": ["staffing", "workforce", "temp agency"],
}


def should_skip(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return True
    return any(skip in host for skip in SKIP_DOMAINS)


def detect_industry(text: str) -> str:
    t = text.lower()
    for industry, kws in INDUSTRY_KEYWORDS.items():
        if any(kw in t for kw in kws):
            return industry
    return "General Business"


def detect_workmates_signal(text: str) -> tuple[str, str]:
    """Return (signal_type, excerpt) or ('', '') if no match."""
    for pattern, signal_type in COMM_SIGNAL_PATTERNS:
        m = pattern.search(text)
        if m:
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 150)
            excerpt = text[start:end].replace("\n", " ").strip()[:200]
            return signal_type, excerpt
    return "", ""


def score_lead(signal_type: str, has_adp: bool, has_multilocation: bool,
               industry: str, text: str) -> dict:
    """Simple scoring per Prompt 5 model."""
    frontline_fit = 0
    comm_signal = 0
    urgency = 0
    evidence = 0
    adp_multiplier = 0
    timing = 0

    # Frontline fit (0-25)
    frontline_kws = ["frontline", "deskless", "hourly", "shift", "caregiver",
                     "multi-location", "distributed", "no corporate email"]
    frontline_fit = min(25, sum(5 for kw in frontline_kws if kw in text.lower()))

    # Comm signal (0-25)
    comm_kws = ["internal communications", "employee app", "policy acknowledgment",
                "mandatory read", "engagement", "recognition program"]
    comm_signal = min(25, sum(5 for kw in comm_kws if kw in text.lower()))

    # Urgency (0-15)
    urgency_kws = ["now hiring", "immediately", "urgent", "critical", "2025"]
    urgency = min(15, sum(3 for kw in urgency_kws if kw in text.lower()))

    # Evidence quality (0-15)
    evidence = 10 if signal_type else 0

    # ADP multiplier (0-10)
    adp_multiplier = 10 if has_adp else 0

    # Timing (0-10)
    timing = 8 if "2025" in text else 5

    total = frontline_fit + comm_signal + urgency + evidence + adp_multiplier + timing

    return {
        "fit_score": frontline_fit,
        "intent_score": comm_signal,
        "evidence_score": evidence,
        "timing_score": timing,
        "uniqueness_score": adp_multiplier,
        "total_score": min(100, total),
        "confidence": "high" if total >= 60 else "medium",
    }


def extract_company_name(title: str, url: str) -> str:
    if title:
        m = re.search(r'\bat\s+([^|–\-]{3,60})', title, re.I)
        if m:
            name = m.group(1).strip()
            if 3 < len(name) < 60:
                return name
        parts = re.split(r'[|–\-]', title)
        if len(parts) >= 2:
            candidate = parts[-1].strip()
            if 3 < len(candidate) < 70:
                return candidate
    host = urlparse(url).netloc.replace("www.", "").split(".")[0]
    return host.replace("-", " ").title()


def outreach_angle(signal_type: str, industry: str) -> str:
    angles = {
        "internal_comms_role": "You're hiring an internal comms manager — HR Cloud Workmates gives your team the platform they'll need from day one.",
        "employee_app_multilocation": "Consolidate your multi-location employee communication into one mobile-first channel.",
        "policy_acknowledgment": "Replace scattered policy sign-offs with tracked mandatory-read flows across all your sites.",
        "mandatory_read": "Ensure every frontline employee completes mandatory training — with real-time completion tracking.",
        "no_email_frontline": "Reach your deskless workers where they are — no corporate email required.",
        "frontline_comm": "Close the communication gap between HQ and your frontline team.",
        "deskless_worker_comm": "Give your deskless workers a voice and keep them connected to the org.",
        "frontline_recognition": "Run peer and manager recognition programs that actually reach your frontline.",
        "caregiver_retention_comm": "Improve caregiver retention with consistent, two-way communication at scale.",
        "shift_worker_comm": "Keep every shift aligned — instant updates, no missed announcements.",
        "multisite_comm": "One platform, every site — streamline communications across all your locations.",
        "adp_multilocation_comm": "You're already on ADP — add Workmates to reach the frontline ADP doesn't touch.",
        "frontline_engagement": "Drive measurable engagement scores for the employees your surveys can't reach.",
    }
    return angles.get(signal_type, "Connect and engage your frontline workforce with HR Cloud Workmates.")


def main():
    print("Workmates Prospect Finder — Prompt 5", flush=True)
    print(f"Queries: {len(QUERIES)}", flush=True)
    print("=" * 70, flush=True)

    seen_domains: set = set()
    leads: list = []

    for i, query in enumerate(QUERIES, 1):
        print(f"\n[{i}/{len(QUERIES)}] {query[:80]}...", flush=True)
        results = ddg_search(query, max_results=10)
        print(f"  DDG: {len(results)} results", flush=True)

        for r in results[:5]:
            url = r.get("href", "")
            if not url or should_skip(url):
                continue

            canonical, domain_status = verify_domain(url)
            if not canonical or canonical in seen_domains:
                continue

            title = r.get("title", "")
            snippet = r.get("body", "")

            print(f"  Fetching: {url[:80]}...", flush=True)
            page_text = fetch_text(url)
            combined = snippet + " " + page_text

            signal_type, excerpt = detect_workmates_signal(combined)
            if not signal_type:
                continue

            has_adp = bool(re.search(r"ADP\s+(Workforce\s+Now|Run|TotalSource|payroll)", combined, re.I))
            has_multilocation = bool(re.search(r"multi.loc|multiple\s+location|multi.site|distributed", combined, re.I))
            industry = detect_industry(combined + " " + title)
            scores = score_lead(signal_type, has_adp, has_multilocation, industry, combined)

            company_name = extract_company_name(title, url)

            # Build canonical row
            row = make_row_from_dict({
                "company_name": company_name,
                "canonical_domain": canonical,
                "country": "US",
                "industry": industry,
                "primary_signal_category": signal_type,
                "strongest_signal_summary": excerpt[:150],
                "strongest_signal_url": url,
                "adp_status": "confirmed" if has_adp else "not_checked",
                "best_hr_cloud_product": "Onboard+Workmates" if has_adp else "Workmates",
                "outreach_angle": outreach_angle(signal_type, industry),
                "recommended_buyer_titles": "VP HR, Director of Internal Communications, Chief People Officer, HR Director",
                "disqualifiers_or_risks": "Verify company operates multiple locations with frontline/hourly workforce",
                **scores,
            })

            seen_domains.add(canonical)
            leads.append(row)
            print(f"  ✓ {company_name} [{canonical}] score={scores['total_score']} — {signal_type}", flush=True)

        if i % 10 == 0 and leads:
            _save(leads)
            print(f"  ── checkpoint: {len(leads)} leads ──", flush=True)

        time.sleep(3)

    _save(leads)
    print(f"\n{'='*70}", flush=True)
    print(f"Total Workmates prospects: {len(leads)} → {OUTPUT_FILE}", flush=True)


def _save(leads: list):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()
        writer.writerows(leads)


if __name__ == "__main__":
    main()
