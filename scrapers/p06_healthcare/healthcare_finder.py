"""
Prompt 6: Healthcare and Senior Care Prospect Finder

Priority segments (ranked):
  1. Home health agencies
  2. Hospice providers
  3. Senior living / assisted living / memory care
  4. Behavioral health / substance abuse
  5. Multi-site clinics and medical groups

Targets 10 healthcare intent signals from the playbook:
  1. Caregiver hiring surge
  2. Manual onboarding / doc collection (paper packets)
  3. License / credential complexity
  4. CMS survey / deficiency pressure
  5. Ownership change / PE roll-up
  6. New licenses / facilities
  7. Exclusions screening
  8. ADP fit
  9. Frontline communication / retention
  10. RFP / grant / funding

Output: data/healthcare_leads.csv (canonical 25-column schema)

Run:
  python3 -u healthcare_finder.py 2>&1 | tee /tmp/healthcare_finder.log
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

OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "healthcare_leads.csv"
OUTPUT_FILE.parent.mkdir(exist_ok=True)

# ── Search queries per 10 signal types ──────────────────────────────────────
QUERIES = [
    # Signal 1: Caregiver hiring surge
    '"caregiver" "now hiring" "multiple locations" site:.com',
    '"home health aide" "immediately hiring" "new hire" site:.com',
    '"hospice" "caregiver" "hiring surge" OR "mass hiring" 2025',
    '"assisted living" "now hiring" "CNAs" OR "caregivers" site:.com 2025',

    # Signal 2: Manual onboarding / new hire packet (highest priority signal)
    '"home health" "new hire packet" filetype:pdf site:.com',
    '"caregiver" "new hire packet" filetype:pdf site:.com',
    '"hospice" "employment application" filetype:pdf',
    '"assisted living" "new hire packet" OR "employment application" filetype:pdf',
    '"behavioral health" "new employee packet" filetype:pdf',
    '"senior living" "new hire packet" filetype:pdf site:.com',
    '"home care" "new hire forms" "complete and return"',
    '"nursing home" "employee packet" filetype:pdf',

    # Signal 3: License / credential complexity
    '"credentialing coordinator" "home health" job',
    '"license verification" "caregiver" "manual" OR "paper" tracking',
    '"credential tracking" "home health" OR "senior living" job',
    '"nurse aide" "registry" "verification" "process" home health',

    # Signal 4: CMS survey / deficiency pressure
    '"CMS" "deficiency" "staffing documentation" healthcare',
    '"CMS survey" "documentation" "deficiency" "nursing home" OR "skilled nursing"',
    '"state survey" "staffing" "documentation" "home health" OR "assisted living"',
    '"OSHA" "recordkeeping" "home health" OR "senior care" compliance',

    # Signal 5: Ownership change / PE roll-up
    '"senior living" acquisition "HR" "standardize" OR "onboard" 2025',
    '"home health" "acquired" OR "merger" "HR integration" 2025',
    '"private equity" "senior care" "portfolio" "HR" standardize',
    '"hospice" "acquisition" "onboarding" standardize 2025',

    # Signal 6: New licenses / facilities opening
    '"new home health agency" "license" OR "certification" 2025',
    '"new assisted living" "opening" "staff" OR "hiring" 2025',
    '"hospice" "new program" "hiring" OR "staff" 2025',
    '"behavioral health" "new facility" OR "new location" hiring 2025',

    # Signal 7: Exclusions screening
    '"OIG exclusion" "screening" "new hire" "home health" OR "senior care"',
    '"LEIE" "exclusion check" "caregiver" OR "home health"',

    # Signal 8: ADP fit
    '"ADP Workforce Now" "home health" OR "senior living" HR',
    '"ADP Run" "home care" OR "hospice" payroll',
    '"ADP" "caregiver" "payroll" HR coordinator job',

    # Signal 9: Frontline comm / retention
    '"caregiver" "turnover" "communication" "retention" program site:.com',
    '"home health" "employee engagement" "frontline" OR "field staff"',
    '"assisted living" "caregiver retention" "communication" initiative',

    # Signal 10: RFP / grant / funding
    'site:sam.gov "home health" OR "hospice" contract award hiring',
    'site:grants.gov "senior care" OR "home health" workforce',
    '"HRSA" "health workforce" "grant" "hiring" home health',
    '"Medicaid waiver" "home care" "expansion" "hiring" 2025',
]

# ── Skip list ─────────────────────────────────────────────────────────────────
SKIP_DOMAINS = {
    "linkedin", "indeed", "glassdoor", "ziprecruiter", "monster",
    "careerbuilder", "simplyhired", "reddit", "quora", "youtube",
    "bamboohr", "gusto", "rippling", "adp", "paychex", "workday",
    "shrm", "forbes", "businessinsider", "medium", "blogspot",
    "hrcloud", "hrdive", "aihr", "healthgrades", "vitals",
    "caregiving.com", "seniorliving.com", "caring.com",
}

# ── Signal patterns for healthcare intent ────────────────────────────────────
HC_SIGNAL_PATTERNS = [
    (re.compile(r"new\s+hire\s+packet|new\s+employee\s+packet|employee\s+packet", re.I), "manual_onboarding"),
    (re.compile(r"employment\s+application.*filetype|bring.*paperwork.*first\s+day", re.I), "manual_onboarding"),
    (re.compile(r"caregiver.*now\s+hiring|hiring.*caregiver|mass\s+hiring.*caregiver", re.I), "caregiver_hiring_surge"),
    (re.compile(r"credentialing\s+coordinator|license\s+verification.*caregiver|credential\s+tracking", re.I), "credential_complexity"),
    (re.compile(r"CMS\s+(survey|deficiency|deficiency\s+report)|state\s+survey.*staffing", re.I), "cms_survey_pressure"),
    (re.compile(r"(acquired|acquisition|merger).*HR\s+(integration|standardize)|PE\s+(roll.up|portfolio)", re.I), "ownership_change"),
    (re.compile(r"(new|opening)\s+(facility|location|program|campus).*hiring", re.I), "new_facility"),
    (re.compile(r"OIG\s+exclusion|LEIE|exclusion\s+(check|screening).*new\s+hire", re.I), "exclusions_screening"),
    (re.compile(r"ADP\s+(Workforce\s+Now|Run|TotalSource|payroll)", re.I), "adp_confirmed"),
    (re.compile(r"caregiver\s+turnover|caregiver\s+retention|employee\s+engagement.*caregiver", re.I), "frontline_retention"),
]

# Priority segment classification
SEGMENT_KEYWORDS = {
    "Home Health": ["home health", "home care", "private duty", "personal care attendant"],
    "Hospice": ["hospice", "palliative care"],
    "Senior Living": ["senior living", "assisted living", "memory care", "skilled nursing", "nursing home", "long-term care"],
    "Behavioral Health": ["behavioral health", "substance abuse", "mental health", "addiction", "recovery"],
    "Multi-Site Clinic": ["medical group", "multi-site clinic", "ambulatory", "physician group"],
    "Hospital": ["hospital", "health system", "medical center"],
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
    return "Healthcare (General)"


def detect_hc_signal(text: str) -> tuple[str, str]:
    for pattern, signal_type in HC_SIGNAL_PATTERNS:
        m = pattern.search(text)
        if m:
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 150)
            excerpt = text[start:end].replace("\n", " ").strip()[:200]
            return signal_type, excerpt
    return "", ""


def score_healthcare_lead(signal_type: str, has_adp: bool, segment: str, text: str) -> dict:
    """Scoring per Prompt 6: workforce/hiring 0-20, onboarding pain 0-25,
    compliance/expansion 0-20, evidence quality 0-20, ADP/Workmates 0-10, uniqueness 0-5."""
    workforce_hiring = 0
    onboarding_pain = 0
    compliance_urgency = 0
    evidence_quality = 0
    adp_crosssell = 0
    uniqueness = 5  # base

    # Workforce / hiring (0-20)
    if signal_type == "caregiver_hiring_surge":
        workforce_hiring = 18
    elif any(kw in text.lower() for kw in ["now hiring", "immediately", "mass hire", "hiring surge"]):
        workforce_hiring = 10

    # Manual onboarding / credential pain (0-25)
    if signal_type == "manual_onboarding":
        onboarding_pain = 22
    elif signal_type == "credential_complexity":
        onboarding_pain = 18
    elif signal_type == "exclusions_screening":
        onboarding_pain = 12

    # Compliance / expansion urgency (0-20)
    if signal_type == "cms_survey_pressure":
        compliance_urgency = 18
    elif signal_type == "ownership_change":
        compliance_urgency = 15
    elif signal_type == "new_facility":
        compliance_urgency = 14

    # Evidence quality (0-20)
    is_pdf = ".pdf" in text.lower() or "filetype:pdf" in text.lower()
    evidence_quality = 16 if is_pdf else 10

    # ADP / Workmates cross-sell (0-10)
    adp_crosssell = 10 if has_adp else 0

    total = workforce_hiring + onboarding_pain + compliance_urgency + evidence_quality + adp_crosssell + uniqueness

    return {
        "fit_score": workforce_hiring,
        "intent_score": onboarding_pain,
        "evidence_score": evidence_quality,
        "timing_score": compliance_urgency,
        "uniqueness_score": uniqueness,
        "total_score": min(100, total),
        "confidence": "high" if total >= 65 else "medium",
    }


def outreach_angle(signal_type: str, segment: str) -> str:
    angles = {
        "manual_onboarding": f"Replace your paper new-hire packets with mobile-first digital onboarding — {segment} aides complete everything before day one.",
        "caregiver_hiring_surge": "With caregivers joining at scale, digital onboarding cuts your day-one paperwork from hours to minutes.",
        "credential_complexity": "Automate credential verification and license tracking so your compliance team spends time on care — not paperwork.",
        "cms_survey_pressure": "CMS surveys increasingly flag staffing documentation. HR Cloud Onboard creates a defensible audit trail for every new hire.",
        "ownership_change": "Post-acquisition HR standardization starts with onboarding — get every site on one consistent process in days.",
        "new_facility": "New location opening? Get new hires onboarded before day one with no paper and no delays.",
        "exclusions_screening": "Automate OIG/LEIE exclusion screening as part of your new hire workflow — not an afterthought.",
        "adp_confirmed": "You're already on ADP — HR Cloud fills the onboarding and frontline communication gap ADP doesn't cover.",
        "frontline_retention": "Reduce caregiver turnover by keeping them connected, informed, and recognized from day one.",
    }
    return angles.get(signal_type, f"Streamline hiring and onboarding for your {segment} workforce with HR Cloud.")


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


def main():
    print("Healthcare & Senior Care Prospect Finder — Prompt 6", flush=True)
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

            signal_type, excerpt = detect_hc_signal(combined)
            if not signal_type:
                continue

            has_adp = bool(re.search(r"ADP\s+(Workforce\s+Now|Run|TotalSource|payroll)", combined, re.I))
            segment = detect_segment(combined + " " + title)
            scores = score_healthcare_lead(signal_type, has_adp, segment, combined)

            company_name = extract_company_name(title, url)

            row = make_row_from_dict({
                "company_name": company_name,
                "canonical_domain": canonical,
                "country": "US",
                "industry": "Healthcare / Senior Care",
                "location_count_or_range": "",
                "primary_signal_category": signal_type,
                "strongest_signal_summary": excerpt[:150],
                "strongest_signal_url": url,
                "adp_status": "confirmed" if has_adp else "not_checked",
                "best_hr_cloud_product": "Onboard+Workmates" if has_adp else "Onboard",
                "outreach_angle": outreach_angle(signal_type, segment),
                "recommended_buyer_titles": "VP of HR, Director of Human Resources, Chief Nursing Officer, COO, Administrator",
                "disqualifiers_or_risks": f"Verify segment is {segment}. Confirm 50+ employees with hiring activity.",
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
    print(f"Total healthcare leads: {len(leads)} → {OUTPUT_FILE}", flush=True)


def _save(leads: list):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()
        writer.writerows(leads)


if __name__ == "__main__":
    main()
