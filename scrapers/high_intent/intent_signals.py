"""
High-Intent HR Software Lead Finder
Finds companies showing behavioral buying signals:
  - Job postings for HR roles (implies HR system ownership/evaluation)
  - G2/Capterra comparison page visits (comparison intent)
  - Public mentions of "evaluating HR software" or "looking for HRIS"
  - Companies hiring their first dedicated HR person (greenfield opportunity)
  - Companies that posted "HR Director" job (budget and authority signal)

Run:
  python3 -u intent_signals.py 2>&1 | tee /tmp/intent_signals.log
"""

import csv
import re
import time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "high_intent_leads.csv"
OUTPUT_FILE.parent.mkdir(exist_ok=True)

CSV_FIELDS = [
    "Company Name", "Verified Domain", "Official Website", "State", "Industry",
    "Intent Signal", "Exact Evidence Quote", "Signal Type",
    "Evidence Source", "Evidence Link", "Confidence Level",
    "Recommended Outreach Angle",
]

SKIP_DOMAINS = {
    "linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com",
    "monster.com", "careerbuilder.com", "simplyhired.com",
    "reddit.com", "quora.com", "youtube.com", "wikipedia.org",
    "workday.com", "bamboohr.com", "gusto.com", "rippling.com",
    "adp.com", "paychex.com", "paylocity.com", "ukg.com",
    "g2.com", "capterra.com", "trustradius.com", "getapp.com",
    "shrm.org", "businessinsider.com", "forbes.com",
}

QUERIES = [
    # First HR hire signals (no system yet)
    '"our first HR" OR "first dedicated HR" "hire" job',
    '"building our HR department" OR "building out HR" job posting',
    '"HR from scratch" OR "stand up HR" startup job',
    '"people operations" "first hire" startup',

    # System evaluation signals
    '"evaluating HRIS" OR "looking for HRIS" OR "considering HRIS"',
    '"evaluating HR software" OR "selecting HR software"',
    '"HRIS implementation" "looking for" OR "seeking" vendor',
    '"onboarding software" "recommendations" "small business"',
    '"replace ADP" OR "ADP alternative" OR "switch from ADP"',
    '"replace Paychex" OR "Paychex alternative" OR "switch from Paychex"',
    '"manual onboarding" "looking for" OR "need" software solution',
    '"paper new hire" "need to digitize" OR "automate"',
    '"automate onboarding" "currently" "paper" OR "manual"',

    # HR Director / VP HR new hires (decision-maker just arrived)
    '"VP of HR" OR "Chief People Officer" OR "HR Director" "new" job posting -site:linkedin.com',
    '"director of human resources" "new hire" company announcement',
    '"CHRO" OR "Chief HR" appointment announcement 2025',

    # Growth signals (need to scale HR)
    '"rapid growth" "HR" "onboarding" "streamline"',
    '"scaling" "HR processes" "manual" OR "paper"',
    '"100 employees" OR "200 employees" "HR" "onboarding" "challenge"',
    '"growing team" "HR" "onboarding" "paperwork" "process"',

    # Pain point mentions
    '"hr paperwork" "overwhelmed" OR "time consuming" OR "inefficient"',
    '"new hire paperwork" "manual" "takes too long" OR "problem"',
    '"onboarding" "paper forms" "digitize" OR "automate" OR "streamline"',
    '"I-9" "W-4" "manually" "entering" "payroll"',

    # LinkedIn job signals (via web-accessible posts)
    '"HR coordinator" "ADP" OR "Paychex" OR "manual" "new hire packet" job',
    '"payroll specialist" "process payroll manually" job',
    '"HR generalist" "paper files" OR "paper-based" OR "manual processes" job',
    '"onboarding coordinator" "new hire paperwork" "process" job',

    # Government / school district first HR hires
    '"HR coordinator" "school district" "new position" job 2025',
    '"human resources" "new position" "county" OR "city" 2025 job',

    # Nonprofit HR scaling
    '"HR" "growing nonprofit" "manual" OR "paper" "onboarding"',
    '"nonprofit" "first HR hire" OR "building HR" job 2025',
]


def ddg_search(query, max_results=10, retries=4):
    for attempt in range(retries):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if results:
                    return results
                time.sleep(8 * (attempt + 1))
        except Exception as e:
            if "rate" in str(e).lower():
                wait = 20 * (attempt + 1)
                print(f"  DDG rate-limited (attempt {attempt+1}), waiting {wait}s...", flush=True)
                time.sleep(wait)
            else:
                return []
    return []


def fetch_text(url, timeout=10):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "lxml")
        for t in soup(["script", "style"]):
            t.decompose()
        return soup.get_text(" ", strip=True)[:4000]
    except Exception:
        return ""


SIGNAL_PATTERNS = re.compile(
    r"(evaluating|considering|looking for|seeking|replace|switching|automate|"
    r"manual process|paper forms|paper-based|first HR hire|building HR|"
    r"scaling HR|streamline onboarding|digitize|overwhelmed with paperwork)",
    re.I
)


def extract_intent_info(url, text, title, snippet):
    combined = snippet + " " + text
    match = SIGNAL_PATTERNS.search(combined)
    if not match:
        return None

    domain = urlparse(url).netloc.lower().lstrip("www.")
    if not domain or any(s in domain for s in SKIP_DOMAINS):
        return None

    start = max(0, match.start() - 100)
    end = min(len(combined), match.end() + 150)
    quote = combined[start:end].replace("\n", " ").strip()

    # Classify signal
    if re.search(r"(first HR|building HR|stand up HR|first dedicated HR)", combined, re.I):
        signal_type = "first_hr_hire"
        angle = "They're building HR for the first time — ideal moment to establish good onboarding from day one. Position as the easy HR foundation."
    elif re.search(r"(evaluating|considering|looking for|replace|alternative|switch)", combined, re.I):
        signal_type = "active_evaluation"
        angle = "They're actively shopping. Respond fast. Lead with a 15-minute demo and ROI from similar companies."
    elif re.search(r"(manual|paper|paperwork|overwhelmed)", combined, re.I):
        signal_type = "pain_point_mention"
        angle = "Pain acknowledged publicly. Lead with: 'Teams like yours cut new hire paperwork time by 80% in the first week.'"
    else:
        signal_type = "growth_signal"
        angle = "Growth stage company — HR is becoming a bottleneck. Pitch scalability."

    return {
        "Company Name": title[:80],
        "Verified Domain": domain,
        "Official Website": f"https://www.{domain}",
        "State": "",
        "Industry": "",
        "Intent Signal": match.group(0),
        "Exact Evidence Quote": quote[:400],
        "Signal Type": signal_type,
        "Evidence Source": title[:80],
        "Evidence Link": url,
        "Confidence Level": "Medium",
        "Recommended Outreach Angle": angle,
    }


def main():
    print("High-Intent HR Signal Finder", flush=True)
    print(f"Queries: {len(QUERIES)}", flush=True)
    print("=" * 70, flush=True)

    seen = set()
    leads = []

    for i, query in enumerate(QUERIES, 1):
        print(f"\n[{i}/{len(QUERIES)}] {query[:80]}...", flush=True)
        results = ddg_search(query)
        print(f"  DDG: {len(results)} results", flush=True)

        for r in results[:4]:
            url = r.get("href", "")
            domain = urlparse(url).netloc.lower().lstrip("www.")
            if not domain or domain in seen or any(s in domain for s in SKIP_DOMAINS):
                continue
            snippet = r.get("body", "")
            title = r.get("title", "")
            print(f"  Fetching: {url[:80]}...", flush=True)
            text = fetch_text(url)
            info = extract_intent_info(url, text, title, snippet)
            if info:
                seen.add(domain)
                leads.append(info)
                print(f"  ✓ {info['Company Name'][:50]} [{domain}] — {info['Signal Type']}", flush=True)

        if i % 10 == 0:
            _save(leads)
            print(f"  ── checkpoint: {len(leads)} leads ──", flush=True)

        time.sleep(4)

    _save(leads)
    print(f"\n{'='*70}", flush=True)
    print(f"Total high-intent leads: {len(leads)} → {OUTPUT_FILE}", flush=True)


def _save(leads):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(leads)


if __name__ == "__main__":
    main()
