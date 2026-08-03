"""
RFP/RFQ Scanner for HR Software Opportunities
Finds active government and enterprise Requests for Proposal/Quote
for HR software, onboarding systems, HRIS, and payroll platforms.

Sources:
  - SAM.gov (federal)
  - State procurement portals (via DDG)
  - BidNet / DemandStar mentions
  - School district and county RFPs
  - Hospital/healthcare system RFPs

Run:
  python3 -u rfp_finder.py 2>&1 | tee /tmp/rfp_finder.log
"""

import csv
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "rfp_rfq_leads.csv"
OUTPUT_FILE.parent.mkdir(exist_ok=True)

CSV_FIELDS = [
    "Organization Name", "Verified Domain", "Official Website",
    "State", "Industry / Sector",
    "RFP Title", "RFP Number", "Exact Quote",
    "Signal Type", "Submission Deadline", "Posted Date",
    "Evidence Link", "Confidence Level", "Recommended Outreach Angle",
]

RFP_SIGNALS = re.compile(
    r"(request\s+for\s+proposal|request\s+for\s+quote|RFP|RFQ|ITB|IFB|"
    r"invitation\s+to\s+bid|solicitation|procurement\s+notice|"
    r"competitive\s+bid|vendor\s+selection)",
    re.I,
)

HR_SOFTWARE_SIGNALS = re.compile(
    r"(human\s+resources\s+(information\s+)?(system|software|platform)|HRIS|HCM|"
    r"payroll\s+(system|software|platform|solution)|"
    r"onboarding\s+(system|software|platform|solution)|"
    r"workforce\s+management|talent\s+management|"
    r"employee\s+(self.service|portal|management)|"
    r"applicant\s+tracking|ATS|recruiting\s+(system|software)|"
    r"benefits\s+administration\s+(system|software)|"
    r"time\s+and\s+attendance\s+(system|software)|"
    r"HR\s+(software|system|platform|technology|solution|automation))",
    re.I,
)

DEADLINE_PATTERN = re.compile(
    r"(due\s+date|deadline|submit\s+by|proposals?\s+due|closing\s+date)[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    re.I,
)

SKIP_DOMAINS = {
    # Social / general web
    "linkedin.com", "reddit.com", "youtube.com", "wikipedia.org",
    "quora.com", "twitter.com", "facebook.com", "instagram.com",
    # HRIS vendors (not buyers)
    "workday.com", "bamboohr.com", "gusto.com", "rippling.com",
    "adp.com", "paychex.com", "paylocity.com", "ultipro.com",
    "ukg.com", "ceridian.com", "kronos.com", "successfactors.com",
    "namely.com", "zenefits.com", "leapsome.com", "lattice.com",
    "rippling.com", "hibob.com", "personio.com", "sage.com",
    # RFP template / comparison / consultant sites (not buyers)
    "comparehris.com", "hrtechsaas.com", "hrisconsultants.co.uk",
    "starbridge.ai", "tendersontime.com", "rfpmart.com",
    "instantmarkets.com", "govly.com", "highergov.com",
    "neogov.com", "rfp360.com", "loopio.com", "ombud.com",
    # Media / editorial
    "shrm.org", "businessinsider.com", "forbes.com", "techraynews.com",
    "hrdive.com", "hrexecutive.com", "zdnet.com", "techrepublic.com",
    "gartner.com", "g2.com", "capterra.com", "softwareadvice.com",
}

QUERIES = [
    # Procurement portals — direct domain targeting (no site: operator, use domain in query)
    '"human resources information system" RFP 2026 bidnet',
    '"HRIS" RFP 2026 demandstar',
    '"HR software" OR "HRIS" RFP 2026 opengov procurement',
    '"human resources" RFP 2026 bonfirehub',
    '"HRIS" OR "payroll system" RFP 2026 publicpurchase',
    '"HR software" RFP 2026 ionwave OR periscope OR biddingo',

    # SAM.gov federal
    '"human resources information system" "request for proposal" sam.gov 2026',
    '"HRIS" OR "HCM" "request for proposal" sam.gov 2026',

    # School districts
    '"request for proposal" "HRIS" "school district" 2026',
    '"request for proposal" "HR software" "school district" 2026',
    '"RFP" "human resources" "school district" "onboarding" 2026',
    '"request for proposal" "payroll services" "school district" 2026',
    '"competitive bid" "HRIS" OR "HR system" "ISD" OR "USD" OR "CUSD" 2026',

    # Counties and municipalities
    '"request for proposal" "human resources information system" county 2026',
    '"RFP" "HRIS" "city of" 2026',
    '"RFP" "HRIS" "county of" OR "town of" 2026',
    '"request for proposal" "payroll" municipality 2026',
    '"request for proposal" "HR software" county government 2026',

    # State agencies
    '"request for proposal" "HRIS" "state of" 2026',
    '"request for proposal" "human resources system" "state agency" 2026',
    '"competitive solicitation" "HRIS" OR "HR software" 2026',
    '"request for proposal" "payroll system" "state of" 2026',

    # Healthcare
    '"request for proposal" "HRIS" hospital 2026',
    '"request for proposal" "HR software" "health system" 2026',
    '"RFP" "human resources" "healthcare" onboarding 2026',
    '"request for proposal" "workforce management" hospital 2026',

    # Utilities
    '"request for proposal" "HRIS" OR "HR software" utility 2026',
    '"RFP" "human resources system" "electric" OR "water" OR "gas" utility 2026',

    # Nonprofits
    '"request for proposal" "HRIS" nonprofit 2026',
    '"RFP" "human resources system" nonprofit 2026',
    '"request for proposal" "payroll" "nonprofit" OR "foundation" 2026',

    # State-specific (no site: operator)
    '"request for proposal" "HRIS" Texas 2026',
    '"request for proposal" "HRIS" Florida 2026',
    '"request for proposal" "HRIS" California 2026',
    '"request for proposal" "HRIS" Georgia 2026',
    '"request for proposal" "HRIS" Ohio 2026',
    '"request for proposal" "HRIS" Tennessee 2026',
    '"request for proposal" "HRIS" North Carolina 2026',

    # Onboarding / ATS
    '"request for proposal" "employee onboarding" software 2026',
    '"request for proposal" "applicant tracking system" 2026',
    '"RFP" "talent management system" 2026',
    '"request for proposal" "new hire" onboarding system 2026',
]


def ddg_search(query: str, max_results: int = 10, retries: int = 4) -> list:
    for attempt in range(retries):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if results:
                    return results
                wait = 8 * (attempt + 1)
                time.sleep(wait)
        except Exception as e:
            err = str(e)
            if "rate" in err.lower() or "202" in err:
                wait = 20 * (attempt + 1)
                print(f"  DDG rate-limited (attempt {attempt+1}), waiting {wait}s...", flush=True)
                time.sleep(wait)
            else:
                print(f"  DDG error: {e}", flush=True)
                return []
    return []


def fetch_text(url: str, timeout: int = 12) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; LeadIntel/1.0)"}
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return ""
        ct = r.headers.get("content-type", "")
        if "html" in ct:
            soup = BeautifulSoup(r.text, "lxml")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            return soup.get_text(" ", strip=True)[:5000]
        return ""
    except Exception:
        return ""


def extract_rfp_info(url: str, text: str, title: str, snippet: str) -> dict | None:
    combined = snippet + " " + text

    if not RFP_SIGNALS.search(combined):
        return None
    if not HR_SOFTWARE_SIGNALS.search(combined):
        return None

    domain = urlparse(url).netloc.lower().lstrip("www.")
    if not domain or any(skip in domain for skip in SKIP_DOMAINS):
        return None

    # Extract RFP title
    rfp_title_match = re.search(
        r"(RFP|RFQ|Request\s+for\s+Proposal)[:\s#\-]+([^\n\.]{10,80})",
        combined, re.I
    )
    rfp_title = rfp_title_match.group(0)[:100] if rfp_title_match else title[:80]

    # Extract RFP number
    rfp_num_match = re.search(r"(RFP|RFQ|Solicitation|Bid)[:\s#\-]+([A-Z0-9\-]{4,20})", combined, re.I)
    rfp_num = rfp_num_match.group(0) if rfp_num_match else ""

    # Extract deadline
    deadline_match = DEADLINE_PATTERN.search(combined)
    deadline = deadline_match.group(2) if deadline_match else ""

    # Extract evidence quote
    hr_match = HR_SOFTWARE_SIGNALS.search(combined)
    if hr_match:
        start = max(0, hr_match.start() - 80)
        end = min(len(combined), hr_match.end() + 120)
        quote = combined[start:end].replace("\n", " ").strip()
    else:
        quote = snippet[:300]

    # Detect org type
    if re.search(r"(school\s+district|ISD|USD|CUSD|k12)", combined, re.I):
        industry = "Education / K12"
    elif re.search(r"(hospital|health\s+system|medical\s+center|clinic)", combined, re.I):
        industry = "Healthcare"
    elif re.search(r"(county|municipality|township|city\s+of|town\s+of)", combined, re.I):
        industry = "Government / Municipal"
    elif re.search(r"(state\s+of|department\s+of|agency|bureau)", combined, re.I):
        industry = "Government / State"
    elif re.search(r"(nonprofit|foundation|association|charity)", combined, re.I):
        industry = "Nonprofit"
    else:
        industry = "Unknown"

    # State extraction
    state_match = re.search(
        r"\b(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|"
        r"Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|"
        r"Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|"
        r"Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|"
        r"North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|"
        r"South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|"
        r"Wisconsin|Wyoming)\b", combined, re.I
    )
    state = state_match.group(1)[:2].upper() if state_match else ""

    angle = (
        f"Active RFP confirms {industry} org is evaluating HR software NOW. "
        "Submit a vendor response or reach out directly to the procurement contact listed in the RFP. "
        "Lead with compliance, ease of implementation, and cost vs. paper-based status quo."
    )

    return {
        "Organization Name": title[:80],
        "Verified Domain": domain,
        "Official Website": f"https://www.{domain}",
        "State": state,
        "Industry / Sector": industry,
        "RFP Title": rfp_title,
        "RFP Number": rfp_num,
        "Exact Quote": quote[:400],
        "Signal Type": "active_rfp",
        "Submission Deadline": deadline,
        "Posted Date": "",
        "Evidence Link": url,
        "Confidence Level": "High",
        "Recommended Outreach Angle": angle,
    }


def main():
    print("RFP/RFQ Scanner — HR Software Opportunities", flush=True)
    print(f"Queries: {len(QUERIES)}", flush=True)
    print("=" * 70, flush=True)

    seen_domains: set[str] = set()
    leads: list[dict] = []

    for i, query in enumerate(QUERIES, 1):
        print(f"\n[{i}/{len(QUERIES)}] {query[:80]}...", flush=True)
        results = ddg_search(query)
        print(f"  DDG: {len(results)} results", flush=True)

        for r in results[:5]:
            url = r.get("href", "")
            domain = urlparse(url).netloc.lower().lstrip("www.")
            if not domain or any(skip in domain for skip in SKIP_DOMAINS):
                continue
            if domain in seen_domains:
                continue

            snippet = r.get("body", "")
            title = r.get("title", "")

            # Quick snippet check first
            combined_quick = snippet + " " + title
            if not (RFP_SIGNALS.search(combined_quick) and HR_SOFTWARE_SIGNALS.search(combined_quick)):
                continue

            print(f"  Fetching: {url[:80]}...", flush=True)
            text = fetch_text(url)
            info = extract_rfp_info(url, text, title, snippet)
            if info:
                seen_domains.add(domain)
                leads.append(info)
                print(f"  ✓ {info['Organization Name'][:50]} [{domain}] — {info['Industry / Sector']}", flush=True)

        if i % 10 == 0:
            print(f"\n  ── checkpoint: {len(leads)} RFPs found ──", flush=True)
            _save(leads)

        time.sleep(4)

    _save(leads)
    print(f"\n{'='*70}", flush=True)
    print(f"Total RFP/RFQ leads: {len(leads)}", flush=True)
    print(f"Saved → {OUTPUT_FILE}", flush=True)


def _save(leads):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(leads)


if __name__ == "__main__":
    main()
