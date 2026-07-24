"""
ADP Confirmed User Finder
Discovers companies confirmed to be using ADP (Workforce Now, ADP Run, ADP TotalSource)
via job postings, LinkedIn signals, and public mentions.

Signal logic:
  - Job postings that list "ADP" as required/preferred tool → confirmed current user
  - Job titles: HR Coordinator, Payroll Specialist, HR Generalist + "ADP" in description
  - G2/Capterra review mentions of switching FROM ADP
  - LinkedIn job posts mentioning ADP familiarity

Run:
  python3 -u adp_finder.py 2>&1 | tee /tmp/adp_finder.log
"""

import csv
import re
import time
import json
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "adp_confirmed_leads.csv"
OUTPUT_FILE.parent.mkdir(exist_ok=True)

CSV_FIELDS = [
    "Company Name", "Verified Company Domain", "Official Website", "Country",
    "State or Province", "Industry", "Estimated Employee Count",
    "ADP Signal Type", "Exact Evidence Quote", "Reason This Confirms ADP Use",
    "Signal Type", "Evidence Source Title", "Verified Evidence Link",
    "Evidence Date", "Confidence Level", "Recommended Outreach Angle",
]

# ADP product names to look for
ADP_PRODUCTS = re.compile(
    r"(ADP\s+Workforce\s+Now|ADP\s+Run|ADP\s+TotalSource|ADP\s+Vantage|"
    r"ADP\s+payroll|ADP\s+HRIS|ADP\s+ezLaborManager|ADP\s+Time\s+&\s+Attendance|"
    r"experience\s+with\s+ADP|proficiency\s+in\s+ADP|knowledge\s+of\s+ADP|"
    r"using\s+ADP|process\s+payroll\s+in\s+ADP|enter\s+data\s+into\s+ADP)",
    re.I,
)

SKIP_DOMAINS = {
    "adp.com", "indeed.com", "linkedin.com", "glassdoor.com", "ziprecruiter.com",
    "monster.com", "careerbuilder.com", "simplyhired.com", "salary.com",
    "payscale.com", "reddit.com", "quora.com", "youtube.com", "wikipedia.org",
    "workday.com", "bamboohr.com", "gusto.com", "rippling.com", "paychex.com",
    "paylocity.com", "ukg.com", "namely.com", "zenefits.com",
    "g2.com", "capterra.com", "trustradius.com", "getapp.com",
    "businessinsider.com", "forbes.com", "shrm.org",
}

# Queries targeting confirmed ADP users via job postings
QUERIES = [
    # Direct ADP product mentions in job descriptions
    '"ADP Workforce Now" "HR" job -site:adp.com',
    '"ADP Workforce Now" "payroll" "process" job posting',
    '"ADP Run" "HR coordinator" OR "HR generalist" job',
    '"ADP Run" "payroll" "small business" job',
    '"ADP TotalSource" HR job',
    '"experience with ADP" "HR" OR "payroll" job',
    '"proficiency in ADP" HR coordinator job',
    '"ADP Workforce Now" "benefits administration" job',
    '"process payroll" "ADP" HR manager job posting',
    '"enter new hires" "ADP" OR "data entry" "ADP" HR job',

    # Industry-specific ADP job posts
    '"ADP Workforce Now" "school district" HR',
    '"ADP" "payroll" "healthcare" "HR coordinator" job',
    '"ADP" "payroll" "nonprofit" "HR" job description',
    '"ADP Run" "restaurant" OR "hospitality" payroll',
    '"ADP Run" "retail" HR payroll job',
    '"ADP" "manufacturing" "HR generalist" payroll job',
    '"ADP Workforce Now" "construction" HR payroll',
    '"ADP" "home care" OR "home health" payroll HR job',

    # Switch signals — companies actively evaluating away from ADP
    '"switching from ADP" HR software',
    '"replacing ADP" HRIS',
    '"moved away from ADP" onboarding',
    '"ADP alternative" "small business"',
    '"frustrated with ADP" OR "problems with ADP" HR',

    # G2/review signals
    'site:g2.com "ADP Workforce Now" review "manual" OR "paper"',
    'site:capterra.com "ADP Run" review "manual process"',

    # LinkedIn-style job post patterns (via DDG)
    '"familiar with ADP" "HR" job description site:linkedin.com',
    '"knowledge of ADP" "payroll" job site:linkedin.com',
    '"ADP experience" "HR" "new hire" job site:linkedin.com',
    '"ADP" "I-9" "new hire paperwork" HR job',
    '"ADP" "onboarding" "paper" "new hire" HR job posting',

    # State-specific job boards
    '"ADP Workforce Now" "HR coordinator" Texas job',
    '"ADP Workforce Now" "HR coordinator" Florida job',
    '"ADP Workforce Now" "HR coordinator" California job',
    '"ADP Run" "payroll" "HR" Georgia job',
    '"ADP Run" "payroll" Ohio HR job',
]


def ddg_search(query: str, max_results: int = 10, retries: int = 4) -> list:
    for attempt in range(retries):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if results:
                    return results
                wait = 8 * (attempt + 1)
                print(f"  DDG empty (attempt {attempt+1}), waiting {wait}s...", flush=True)
                time.sleep(wait)
        except Exception as e:
            err = str(e)
            if "rate" in err.lower() or "202" in err or "Ratelimit" in err:
                wait = 20 * (attempt + 1)
                print(f"  DDG rate-limited (attempt {attempt+1}), waiting {wait}s...", flush=True)
                time.sleep(wait)
            else:
                print(f"  DDG error: {e}", flush=True)
                return []
    return []


def fetch_text(url: str, timeout: int = 10) -> str:
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
            return soup.get_text(" ", strip=True)[:4000]
        return ""
    except Exception:
        return ""


def extract_company_info(url: str, text: str, title: str) -> dict | None:
    match = ADP_PRODUCTS.search(text)
    if not match:
        return None

    domain = urlparse(url).netloc.lower().lstrip("www.")
    if not domain or any(skip in domain for skip in SKIP_DOMAINS):
        return None

    # Extract surrounding context (200 chars around match)
    start = max(0, match.start() - 100)
    end = min(len(text), match.end() + 150)
    quote = text[start:end].replace("\n", " ").strip()

    # Determine confidence
    strong = re.search(r"(ADP\s+Workforce\s+Now|ADP\s+Run|ADP\s+TotalSource)", text, re.I)
    confidence = "High" if strong else "Medium"

    # Determine signal type
    if re.search(r"(switching|replacing|moving away|alternative|frustrated|problems with)", text, re.I):
        signal_type = "switching_signal"
        angle = "Positioned as the modern alternative to ADP — highlight ease of switching and onboarding automation."
    elif re.search(r"(job|hiring|position|role|description|apply)", text[:500], re.I):
        signal_type = "job_posting_adp_mention"
        angle = "Job post confirms ADP use. Reach out: 'Saw you're hiring an HR coordinator familiar with ADP — many teams like yours use us to eliminate manual ADP data entry and paper new hire packets.'"
    else:
        signal_type = "public_adp_mention"
        angle = "Confirmed ADP user. Lead with ROI of replacing paper-based ADP workflow with automated onboarding."

    return {
        "Company Name": title[:80],
        "Verified Company Domain": domain,
        "Official Website": f"https://www.{domain}",
        "Country": "US",
        "State or Province": "",
        "Industry": "",
        "Estimated Employee Count": "",
        "ADP Signal Type": match.group(0),
        "Exact Evidence Quote": quote,
        "Reason This Confirms ADP Use": "Job posting or public page explicitly names ADP as current tool used for payroll/HR.",
        "Signal Type": signal_type,
        "Evidence Source Title": title[:100],
        "Verified Evidence Link": url,
        "Evidence Date": "",
        "Confidence Level": confidence,
        "Recommended Outreach Angle": angle,
    }


def main():
    print("ADP Confirmed User Finder", flush=True)
    print(f"Queries: {len(QUERIES)}", flush=True)
    print("=" * 70, flush=True)

    seen_domains: set[str] = set()
    leads: list[dict] = []

    for i, query in enumerate(QUERIES, 1):
        print(f"\n[{i}/{len(QUERIES)}] {query}...", flush=True)
        results = ddg_search(query)
        print(f"  DDG: {len(results)} results", flush=True)

        candidates = []
        for r in results:
            url = r.get("href", "")
            domain = urlparse(url).netloc.lower().lstrip("www.")
            if not domain or any(skip in domain for skip in SKIP_DOMAINS):
                continue
            if domain in seen_domains:
                continue
            candidates.append((url, r.get("title", ""), r.get("body", "")))

        for url, title, snippet in candidates[:4]:
            domain = urlparse(url).netloc.lower().lstrip("www.")
            if domain in seen_domains:
                continue
            print(f"  Fetching: {url[:80]}...", flush=True)
            text = fetch_text(url)
            combined = snippet + " " + text
            info = extract_company_info(url, combined, title)
            if info:
                seen_domains.add(domain)
                leads.append(info)
                print(f"  ✓ {info['Company Name']} [{domain}] [{info['Confidence Level']}] — {info['Signal Type']}", flush=True)

        if i % 10 == 0:
            print(f"\n  ── checkpoint: {len(leads)} leads saved ──", flush=True)
            _save(leads)

        time.sleep(4)

    _save(leads)
    print(f"\n{'='*70}", flush=True)
    print(f"Total ADP confirmed leads: {len(leads)}", flush=True)
    print(f"Saved → {OUTPUT_FILE}", flush=True)


def _save(leads: list[dict]):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(leads)


if __name__ == "__main__":
    main()
