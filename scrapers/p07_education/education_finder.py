"""
Prompt 7: Education Intent Prospect Finder

Priority segments (ranked):
  1. Public K-12 school districts
  2. Charter school networks
  3. Private K-12 schools
  4. Early childhood / Head Start programs
  5. Community colleges
  6. Education nonprofits / ed service agencies

10 education intent signals from the playbook:
  1. Seasonal hiring / reopening
  2. Manual employment forms
  3. HRIS / onboarding procurement
  4. ADP confirmation
  5. Background check / fingerprint / licensure complexity
  6. Multi-campus communication
  7. Board / audit evidence
  8. Grants / contracts
  9. Leadership change
  10. Repeated friction evidence

Timing rules:
  120-60 days before term start = planning opportunity
  60-21 days = urgency
  After term start = retrospective

Output: data/education_leads.csv (canonical 25-column schema)

Run:
  python3 -u education_finder.py 2>&1 | tee /tmp/education_finder.log
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

OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "education_leads.csv"
OUTPUT_FILE.parent.mkdir(exist_ok=True)

# ── Search queries per 10 signal types ──────────────────────────────────────
QUERIES = [
    # Signal 1: Seasonal hiring / reopening
    '"school district" "new hire" "back to school" hiring 2025',
    '"substitute teacher" "new hire" "hiring" school district 2025',
    '"charter school" "teacher hiring" "new staff" 2025',
    '"Head Start" "hiring" "new staff" 2025',

    # Signal 2: Manual employment forms (highest signal)
    '"new employee packet" site:.k12.tx.us filetype:pdf',
    '"new hire packet" "school district" filetype:pdf',
    '"substitute teacher" "new hire packet" filetype:pdf',
    '"new hire packet" site:.k12.fl.us filetype:pdf',
    '"new hire packet" site:.k12.ga.us filetype:pdf',
    '"new hire packet" site:.k12.ca.us filetype:pdf',
    '"employee packet" "charter school" filetype:pdf',
    '"new hire packet" "community college" filetype:pdf',
    '"new hire forms" "school district" "complete and return" HR',
    '"Head Start" "new employee packet" filetype:pdf',
    '"employment application" "school district" "bring to" OR "return to" HR',
    '"new hire packet" "early childhood" OR "daycare" filetype:pdf',

    # Signal 3: HRIS / onboarding procurement
    '"HRIS" "school district" RFP 2025',
    '"onboarding software" "school district" bid OR RFP 2025',
    '"HR software" "school district" "board approved" 2025',
    '"human resources information system" "school district" "proposal" 2025',

    # Signal 4: ADP confirmation
    '"ADP Workforce Now" "school district" HR',
    '"ADP Run" "school district" payroll HR coordinator',
    '"ADP" "school district" "payroll specialist" job',

    # Signal 5: Background check / fingerprint / licensure complexity
    '"fingerprinting" "new employee" "district" packet',
    '"background check" "new hire" "school district" "complete before"',
    '"teacher certification" "new hire" "verification" process district',
    '"fingerprint clearance" "new hire" school OR district',
    '"FBI background check" "new employee" school district',

    # Signal 6: Multi-campus communication
    '"multi-campus" OR "multiple campuses" "employee communication" school OR district',
    '"district-wide" "communication" "all staff" "announcement" challenge',
    '"charter network" "communication" "campuses" "frontline" OR "teachers"',

    # Signal 7: Board / audit evidence
    '"board approved" "HR software" OR "HRIS" school district',
    '"board meeting" "HR" "onboarding" OR "HRIS" school district 2025',
    '"audit finding" "HR" "documentation" "school district"',
    '"payroll audit" "school district" "manual" OR "paper records"',

    # Signal 8: Grants / contracts
    '"Title I" "HR" "hiring" school district 2025',
    '"ESSER" OR "ESSER III" "staffing" "hire" school district 2025',
    '"Head Start" "grant" "expansion" "hiring" 2025',
    'site:grants.gov "school district" "workforce" OR "HR" 2025',

    # Signal 9: Leadership change
    '"new superintendent" "school district" 2025',
    '"new principal" "HR" "initiative" "school" 2025',
    '"new HR director" "school district" 2025',
    '"new chief human resources officer" "school district" 2025',

    # Signal 10: Repeated friction evidence
    '"new campus" "school" hiring 2025',
    '"school expansion" "hiring" "new staff" 2025',
    '"new school opening" "hire" "staff" district 2025',
]

# ── Skip list ─────────────────────────────────────────────────────────────────
SKIP_DOMAINS = {
    "linkedin", "indeed", "glassdoor", "ziprecruiter", "monster",
    "careerbuilder", "simplyhired", "reddit", "quora", "youtube",
    "bamboohr", "gusto", "rippling", "adp", "paychex", "workday",
    "shrm", "forbes", "businessinsider", "medium", "blogspot",
    "hrcloud", "hrdive", "aihr",
    "edweek", "chalkbeat", "k12insight", "eschoolnews",
}

# ── Signal patterns for education intent ────────────────────────────────────
EDU_SIGNAL_PATTERNS = [
    (re.compile(r"new\s+(hire|employee)\s+packet|employee\s+packet|new\s+hire\s+forms?", re.I), "manual_onboarding"),
    (re.compile(r"employment\s+application.*bring|complete.*before\s+first\s+day", re.I), "manual_onboarding"),
    (re.compile(r"substitute\s+teacher.*new\s+hire\s+packet|new\s+hire.*substitute", re.I), "manual_onboarding"),
    (re.compile(r"(HRIS|HR\s+software|onboarding\s+software).*RFP|RFP.*(HRIS|HR\s+software)", re.I), "hris_procurement"),
    (re.compile(r"board\s+approved.*HR\s+software|board\s+meeting.*HRIS", re.I), "board_approved"),
    (re.compile(r"ADP\s+(Workforce\s+Now|Run|TotalSource|payroll)", re.I), "adp_confirmed"),
    (re.compile(r"fingerprint(ing)?\s+(clearance|check).*new\s+(hire|employee)|background\s+check.*new\s+hire.*school", re.I), "background_fingerprint"),
    (re.compile(r"teacher\s+certification.*verification|license.*verification.*district", re.I), "licensure_complexity"),
    (re.compile(r"multi.campus|multiple\s+campuses.*employee\s+communication", re.I), "multi_campus_comm"),
    (re.compile(r"(ESSER|Title\s+I|Head\s+Start).*staffing|grant.*hiring.*school", re.I), "grant_funding"),
    (re.compile(r"new\s+superintendent|new\s+HR\s+director|new\s+CHRO.*school|new\s+principal.*initiative", re.I), "leadership_change"),
    (re.compile(r"new\s+(campus|school|location)\s+(opening|hire)|school\s+expansion.*hiring", re.I), "expansion_hiring"),
    (re.compile(r"seasonal\s+hiring.*school|back.to.school.*hiring|substitute.*hiring\s+surge", re.I), "seasonal_hiring"),
]

# Priority segment classification
SEGMENT_KEYWORDS = {
    "Public K-12 District": ["school district", "k12", "isd", "cisd", "usd", "public school"],
    "Charter Network": ["charter school", "charter network"],
    "Private K-12": ["private school", "parochial", "christian school", "catholic school"],
    "Head Start / Early Childhood": ["head start", "early childhood", "preschool", "daycare", "childcare"],
    "Community College": ["community college", "technical college", "vocational"],
    "Education Nonprofit": ["education nonprofit", "education foundation", "ed service agency"],
}


def should_skip(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return True
    return any(skip in host for skip in SKIP_DOMAINS)


def detect_segment(text: str) -> str:
    t = text.lower()
    for segment, kws in SEGMENT_KEYWORDS.items():
        if any(kw in t for kw in kws):
            return segment
    return "Education (General)"


def detect_edu_signal(text: str) -> tuple[str, str]:
    for pattern, signal_type in EDU_SIGNAL_PATTERNS:
        m = pattern.search(text)
        if m:
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 150)
            excerpt = text[start:end].replace("\n", " ").strip()[:200]
            return signal_type, excerpt
    return "", ""


def score_education_lead(signal_type: str, has_adp: bool, segment: str, text: str) -> dict:
    """Scoring per Prompt 7: seasonal hiring 0-20, manual onboarding 0-20,
    procurement/leadership/expansion 0-20, evidence 0-20, ADP 0-10, timing 0-10."""
    seasonal_hiring = 0
    manual_onboarding = 0
    trigger_score = 0
    evidence_quality = 0
    adp_crosssell = 0
    timing = 0

    # Seasonal hiring (0-20)
    if signal_type == "seasonal_hiring":
        seasonal_hiring = 18
    elif signal_type == "expansion_hiring":
        seasonal_hiring = 14
    elif any(kw in text.lower() for kw in ["now hiring", "immediately", "2025"]):
        seasonal_hiring = 8

    # Manual onboarding (0-20)
    if signal_type == "manual_onboarding":
        manual_onboarding = 18
    elif signal_type in ("background_fingerprint", "licensure_complexity"):
        manual_onboarding = 12

    # Procurement / leadership / expansion trigger (0-20)
    if signal_type == "hris_procurement":
        trigger_score = 20
    elif signal_type == "board_approved":
        trigger_score = 18
    elif signal_type == "leadership_change":
        trigger_score = 15
    elif signal_type == "grant_funding":
        trigger_score = 12

    # Evidence quality (0-20)
    is_pdf = ".pdf" in text.lower()
    is_gov_edu = any(d in text.lower() for d in [".gov", ".edu", ".k12"])
    evidence_quality = 18 if (is_pdf and is_gov_edu) else (14 if is_pdf else 8)

    # ADP cross-sell (0-10)
    adp_crosssell = 10 if has_adp else 0

    # Timing (0-10)
    if "2025" in text:
        timing = 9
    elif any(m in text.lower() for m in ["spring 2025", "fall 2025", "summer 2025"]):
        timing = 10
    else:
        timing = 5

    total = seasonal_hiring + manual_onboarding + trigger_score + evidence_quality + adp_crosssell + timing

    return {
        "fit_score": seasonal_hiring,
        "intent_score": manual_onboarding,
        "evidence_score": evidence_quality,
        "timing_score": trigger_score,
        "uniqueness_score": timing,
        "total_score": min(100, total),
        "confidence": "high" if total >= 65 else "medium",
    }


def outreach_angle(signal_type: str, segment: str) -> str:
    angles = {
        "manual_onboarding": f"Replace paper new-hire packets for your {segment} staff — teachers and aides complete everything digitally before day one.",
        "seasonal_hiring": f"Back-to-school hiring season is your highest-volume onboarding period. HR Cloud makes it manageable at scale.",
        "hris_procurement": f"You're evaluating HRIS solutions — HR Cloud Onboard is purpose-built for {segment} hiring complexity.",
        "board_approved": "The board has budget for HR modernization. Position HR Cloud as the implementation-fast alternative to enterprise systems.",
        "adp_confirmed": "You're already on ADP — HR Cloud Onboard fills the onboarding workflow and I-9 compliance gap.",
        "background_fingerprint": "Automate fingerprint clearance and background check tracking as part of your new hire workflow.",
        "licensure_complexity": "Verify teacher certifications and credentials automatically at hire — before the first day of class.",
        "multi_campus_comm": "Keep every campus aligned with consistent staff communication through HR Cloud Workmates.",
        "grant_funding": "Federal grant funding is available — now is the time to modernize your HR and onboarding systems.",
        "leadership_change": "New district leadership often drives HR modernization. Early outreach positions you as the solution.",
        "expansion_hiring": "New campus openings require scalable onboarding. Get it right from day one.",
    }
    return angles.get(signal_type, f"Streamline teacher and staff onboarding for your {segment} with HR Cloud.")


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
    # For k12 domains, extract district name from netloc
    host = urlparse(url).netloc.lower().replace("www.", "")
    parts = host.split(".")
    if len(parts) >= 4 and "k12" in parts:
        return parts[0].replace("-", " ").title() + " School District"
    return parts[0].replace("-", " ").title()


def main():
    print("Education Intent Prospect Finder — Prompt 7", flush=True)
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

            signal_type, excerpt = detect_edu_signal(combined)
            if not signal_type:
                continue

            has_adp = bool(re.search(r"ADP\s+(Workforce\s+Now|Run|TotalSource|payroll)", combined, re.I))
            segment = detect_segment(combined + " " + title)
            scores = score_education_lead(signal_type, has_adp, segment, combined)

            company_name = extract_company_name(title, url)

            row = make_row_from_dict({
                "company_name": company_name,
                "canonical_domain": canonical,
                "country": "US",
                "industry": "Education",
                "primary_signal_category": signal_type,
                "strongest_signal_summary": excerpt[:150],
                "strongest_signal_url": url,
                "adp_status": "confirmed" if has_adp else "not_checked",
                "best_hr_cloud_product": "Onboard+Workmates" if has_adp else "Onboard",
                "outreach_angle": outreach_angle(signal_type, segment),
                "recommended_buyer_titles": "Superintendent, HR Director, Chief of Staff, Director of Human Capital, Business Administrator",
                "disqualifiers_or_risks": f"Verify {segment} classification. Check buying authority (district vs individual school). Confirm 50+ employees.",
                **scores,
            })

            seen_domains.add(canonical)
            leads.append(row)
            print(f"  ✓ {company_name} [{canonical}] [{segment}] score={scores['total_score']} — {signal_type}", flush=True)

        if i % 10 == 0 and leads:
            _save(leads)
            print(f"  ── checkpoint: {len(leads)} leads ──", flush=True)

        time.sleep(3)

    _save(leads)
    print(f"\n{'='*70}", flush=True)
    print(f"Total education leads: {len(leads)} → {OUTPUT_FILE}", flush=True)


def _save(leads: list):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()
        writer.writerows(leads)


if __name__ == "__main__":
    main()
