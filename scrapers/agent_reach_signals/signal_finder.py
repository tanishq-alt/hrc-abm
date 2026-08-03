"""
HR Cloud signal finder using Agent-Reach channels.

Searches Reddit, GitHub, RSS, and web (via Jina Reader) for:
  - Active HRIS/HRMS RFPs and procurement notices
  - Companies evaluating HR software (buying intent)
  - ADP partner signals
  - New hire onboarding signals

Run:
  python3 -u scrapers/agent_reach_signals/signal_finder.py [--channel web|reddit|github|rss|all]

Output: data/agent_reach_leads.csv
"""

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

OUTPUT_FILE = ROOT / "data" / "agent_reach_leads.csv"
OUTPUT_FILE.parent.mkdir(exist_ok=True)

CSV_FIELDS = [
    "source_channel", "organization_name", "domain", "state",
    "industry", "signal_type", "rfp_number", "deadline",
    "evidence_quote", "evidence_url", "confidence", "outreach_angle",
    "found_at",
]

# --- HR signal patterns ---
RFP_PATTERN = re.compile(
    r"(request\s+for\s+proposal|RFP|RFQ|ITB|solicitation|competitive\s+bid"
    r"|invitation\s+to\s+bid|procurement\s+notice)",
    re.I,
)
HRIS_PATTERN = re.compile(
    r"(HRIS|HRMS|HCM|human\s+resource[s]?\s+(information\s+)?(system|software|platform)"
    r"|onboarding\s+(system|software|platform)"
    r"|HR\s+(software|system|platform|technology|solution)"
    r"|workforce\s+management|talent\s+management"
    r"|employee\s+(self.service|portal|onboarding)"
    r"|applicant\s+tracking|ATS)",
    re.I,
)
DEADLINE_PATTERN = re.compile(
    r"(due\s+date|deadline|submit\s+by|proposals?\s+due|closing\s+date)"
    r"[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    re.I,
)
INTENT_PATTERN = re.compile(
    r"(evaluating\s+HRIS|looking\s+for\s+HR\s+software|replacing\s+(our\s+)?HRIS"
    r"|HR\s+system\s+(migration|replacement|evaluation|selection)"
    r"|switching\s+(from\s+)?ADP|leaving\s+ADP|ADP\s+replacement"
    r"|new\s+HRIS|HRIS\s+vendor|HR\s+software\s+vendor)",
    re.I,
)
ADP_PATTERN = re.compile(
    r"(ADP\s+Workforce\s+Now|ADP\s+Run|ADP\s+partner|ADP\s+marketplace"
    r"|ADP\s+integration|switching\s+from\s+ADP|ADP\s+replacement)",
    re.I,
)

SKIP_DOMAINS = {
    "linkedin.com", "reddit.com", "youtube.com", "wikipedia.org",
    "workday.com", "bamboohr.com", "gusto.com", "rippling.com",
    "adp.com", "paychex.com", "paylocity.com", "lattice.com",
    "leapsome.com", "comparehris.com", "hrtechsaas.com",
    "starbridge.ai", "tendersontime.com", "rfpmart.com",
    "instantmarkets.com", "govly.com", "highergov.com",
}

REDDIT_QUERIES = [
    "HRIS evaluation 2026",
    "replacing ADP Workforce Now",
    "HR software RFP government",
    "HRIS selection process",
    "switching from ADP to",
    "best HRIS for healthcare 2026",
    "HRIS for manufacturing company",
    "onboarding software RFP",
    "HR system RFP county",
    "HRIS for school district",
]

GITHUB_QUERIES = [
    "HRIS RFP 2026",
    "HR software evaluation requirements",
    "onboarding system RFP template",
]

WEB_URLS = [
    "https://www.rfpmart.com/hr-services-rfp-government-contract.html",
    "https://www.instantmarkets.com/q/hris",
    "https://www.tendersinfo.com/global-human-resource-management-information-systems-(hrmis)-tenders.php",
    "https://procurement.opengov.com/portal/pittsburghpa/projects/131688/document",
    "https://www.bidnetdirect.com/new-york/solicitations/open-bids/statewide/Human-Resources-Information-System-HRIS/444101967368",
    "https://resources.uta.edu/business-affairs/procurement/rfp-files/uta2026-012/UTA2026-012+REQSL1337783+RFP.pdf",
]

RSS_FEEDS = [
    "https://sam.gov/api/prod/sgs/v1/search/?index=opp&q=HRIS&is_active=true&format=rss",
    "https://www.rfpmart.com/hr-services-rfp-government-contract.html",
]


def classify_signal(text: str) -> str:
    if RFP_PATTERN.search(text) and HRIS_PATTERN.search(text):
        return "active_rfp"
    if INTENT_PATTERN.search(text):
        return "buying_intent"
    if ADP_PATTERN.search(text):
        return "adp_signal"
    if HRIS_PATTERN.search(text):
        return "hris_mention"
    return "general"


def extract_deadline(text: str) -> str:
    m = DEADLINE_PATTERN.search(text)
    return m.group(2) if m else ""


def extract_industry(text: str) -> str:
    if re.search(r"(school\s+district|ISD|USD|k12|university|college)", text, re.I):
        return "Education"
    if re.search(r"(hospital|health\s+system|medical|clinic|healthcare)", text, re.I):
        return "Healthcare"
    if re.search(r"(county|municipality|city\s+of|town\s+of|government|state\s+of)", text, re.I):
        return "Government"
    if re.search(r"(nonprofit|foundation|association)", text, re.I):
        return "Nonprofit"
    if re.search(r"(manufacturing|construction|utility|utilities)", text, re.I):
        return "Manufacturing/Utilities"
    return "Unknown"


def extract_state(text: str) -> str:
    states = (
        "Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|"
        "Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|"
        "Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|"
        "Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|"
        "North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|"
        "South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|"
        "Wisconsin|Wyoming"
    )
    m = re.search(rf"\b({states})\b", text, re.I)
    return m.group(1) if m else ""


def make_lead(channel: str, url: str, text: str, title: str = "") -> dict | None:
    combined = (title + " " + text).strip()
    signal = classify_signal(combined)
    if signal not in ("active_rfp", "buying_intent", "adp_signal"):
        return None

    domain = urlparse(url).netloc.lower().lstrip("www.")
    if not domain or any(s in domain for s in SKIP_DOMAINS):
        return None

    rfp_m = re.search(r"(RFP|RFQ|Solicitation|Bid)[:\s#\-]+([A-Z0-9\-]{4,20})", combined, re.I)
    rfp_number = rfp_m.group(0) if rfp_m else ""

    hr_m = HRIS_PATTERN.search(combined)
    if hr_m:
        start = max(0, hr_m.start() - 80)
        end = min(len(combined), hr_m.end() + 150)
        quote = combined[start:end].replace("\n", " ").strip()
    else:
        quote = combined[:300]

    angle = (
        f"[{signal.upper()}] via {channel} — "
        + ("Active HRIS/HRMS procurement. Lead with cloud-native onboarding and compliance."
           if signal == "active_rfp" else
           "Company is evaluating HR software. Reach out with ROI framing and a demo."
           if signal == "buying_intent" else
           "ADP user signal. Lead with HR Cloud's ADP integration and migration story.")
    )

    return {
        "source_channel": channel,
        "organization_name": title[:80] or domain,
        "domain": domain,
        "state": extract_state(combined),
        "industry": extract_industry(combined),
        "signal_type": signal,
        "rfp_number": rfp_number,
        "deadline": extract_deadline(combined),
        "evidence_quote": quote[:400],
        "evidence_url": url,
        "confidence": "High" if signal == "active_rfp" else "Medium",
        "outreach_angle": angle,
        "found_at": datetime.utcnow().isoformat() + "Z",
    }


# --- Channel runners ---

def run_web(urls: list[str]) -> list[dict]:
    """Read URLs via Jina Reader (Agent-Reach WebChannel)."""
    from agent_reach.channels.web import WebChannel

    ch = WebChannel()
    leads = []
    for url in urls:
        try:
            print(f"  [web] Reading: {url[:80]}...", flush=True)
            text = ch.read(url)
            lead = make_lead("web", url, text, title=url.split("/")[-1])
            if lead:
                leads.append(lead)
                print(f"  ✓ {lead['signal_type']} — {lead['domain']}", flush=True)
            time.sleep(2)
        except Exception as e:
            print(f"  [web] Error {url[:60]}: {e}", flush=True)
    return leads


def run_reddit(queries: list[str]) -> list[dict]:
    """Search Reddit via rdt-cli or OpenCLI (Agent-Reach RedditChannel)."""
    import subprocess

    leads = []
    for query in queries:
        print(f"  [reddit] Searching: {query}", flush=True)
        try:
            result = subprocess.run(
                ["rdt", "search", query, "--limit", "10", "--format", "json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                print(f"  [reddit] rdt not available or failed, trying opencli...", flush=True)
                result = subprocess.run(
                    ["opencli", "reddit", "search", query, "--limit", "10", "-f", "json"],
                    capture_output=True, text=True, timeout=30,
                )
            if result.returncode != 0:
                print(f"  [reddit] No backend available for: {query}", flush=True)
                continue

            try:
                data = json.loads(result.stdout)
                posts = data if isinstance(data, list) else data.get("posts", data.get("results", []))
            except json.JSONDecodeError:
                posts = []

            for post in posts[:10]:
                url = post.get("url", post.get("permalink", ""))
                if url and not url.startswith("http"):
                    url = "https://reddit.com" + url
                text = post.get("selftext", post.get("body", post.get("content", "")))
                title = post.get("title", "")
                combined = title + " " + text
                lead = make_lead("reddit", url, combined, title=title)
                if lead:
                    leads.append(lead)
                    print(f"  ✓ {lead['signal_type']} — {title[:50]}", flush=True)

        except Exception as e:
            print(f"  [reddit] Error: {e}", flush=True)
        time.sleep(3)
    return leads


def run_github(queries: list[str]) -> list[dict]:
    """Search GitHub via gh CLI (Agent-Reach GitHubChannel)."""
    import subprocess

    leads = []
    for query in queries:
        print(f"  [github] Searching: {query}", flush=True)
        try:
            result = subprocess.run(
                ["gh", "search", "repos", query, "--limit", "10", "--json",
                 "name,description,url,topics"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                print(f"  [github] gh CLI failed: {result.stderr[:100]}", flush=True)
                continue

            repos = json.loads(result.stdout)
            for repo in repos:
                url = repo.get("url", "")
                text = repo.get("description", "") + " " + " ".join(repo.get("topics", []))
                title = repo.get("name", "")
                lead = make_lead("github", url, text, title=title)
                if lead:
                    leads.append(lead)
                    print(f"  ✓ {lead['signal_type']} — {title[:50]}", flush=True)

        except Exception as e:
            print(f"  [github] Error: {e}", flush=True)
        time.sleep(2)
    return leads


def run_rss(feeds: list[str]) -> list[dict]:
    """Read RSS/Atom feeds (Agent-Reach RSSChannel)."""
    try:
        import feedparser
    except ImportError:
        print("  [rss] feedparser not installed: pip install feedparser", flush=True)
        return []

    leads = []
    for feed_url in feeds:
        print(f"  [rss] Reading feed: {feed_url[:80]}...", flush=True)
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                url = entry.get("link", "")
                text = entry.get("summary", "") + " " + entry.get("content", [{}])[0].get("value", "")
                title = entry.get("title", "")
                lead = make_lead("rss", url, text, title=title)
                if lead:
                    leads.append(lead)
                    print(f"  ✓ {lead['signal_type']} — {title[:50]}", flush=True)
            time.sleep(2)
        except Exception as e:
            print(f"  [rss] Error {feed_url[:60]}: {e}", flush=True)
    return leads


def save(leads: list[dict]):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(leads)


def main():
    parser = argparse.ArgumentParser(description="HR signal finder using Agent-Reach channels")
    parser.add_argument(
        "--channel", choices=["web", "reddit", "github", "rss", "all"],
        default="all", help="Which channel(s) to run (default: all)",
    )
    args = parser.parse_args()

    print("HR Cloud Signal Finder — Agent-Reach Edition", flush=True)
    print("=" * 60, flush=True)

    all_leads = []
    ch = args.channel

    if ch in ("web", "all"):
        print("\n[WEB] Jina Reader scan...", flush=True)
        all_leads.extend(run_web(WEB_URLS))

    if ch in ("rss", "all"):
        print("\n[RSS] Feed scan...", flush=True)
        all_leads.extend(run_rss(RSS_FEEDS))

    if ch in ("reddit", "all"):
        print("\n[REDDIT] Signal search...", flush=True)
        all_leads.extend(run_reddit(REDDIT_QUERIES))

    if ch in ("github", "all"):
        print("\n[GITHUB] Repo search...", flush=True)
        all_leads.extend(run_github(GITHUB_QUERIES))

    # Deduplicate by domain
    seen = set()
    unique = []
    for lead in all_leads:
        if lead["domain"] not in seen:
            seen.add(lead["domain"])
            unique.append(lead)

    save(unique)
    print(f"\n{'=' * 60}", flush=True)
    print(f"Total signals found: {len(unique)}", flush=True)
    by_type = {}
    for lead in unique:
        by_type[lead["signal_type"]] = by_type.get(lead["signal_type"], 0) + 1
    for t, n in sorted(by_type.items()):
        print(f"  {t}: {n}", flush=True)
    print(f"Saved → {OUTPUT_FILE}", flush=True)


if __name__ == "__main__":
    main()
