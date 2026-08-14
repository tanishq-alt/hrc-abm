"""
P08 LinkedIn Engagement Lead Finder — HR Cloud ICP
Uses your real Chrome browser via CDP (no LinkedIn bot detection, no API key needed).

SETUP (one time):
  1. Quit Chrome completely: pkill -x "Google Chrome"
  2. Restart Chrome with remote debug port:
       open -a "Google Chrome" --args --remote-debugging-port=9222
  3. In Chrome, go to linkedin.com and log in if not already
  4. Run this script:
       python3 scrapers/p08_linkedin_engagers/linkedin_engager_finder.py --cdp

Workflow:
  1. Connects to your real Chrome (already logged into LinkedIn)
  2. Scrapes posts from ASHHRA, HR Healthcare, HHRAM, CUPA-HR (last 30 days)
  3. Filters posts by ICP-relevant topics
  4. Extracts commenters + reactors from each qualifying post
  5. Visits each person's profile → extracts title, company, size, industry
  6. Scores + tiers against HR Cloud ICP
  7. Writes data/linkedin_leads.csv
"""

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── CONFIG ────────────────────────────────────────────────────────────────────

SOURCES = [
    {"slug": "ashhra",        "url": "https://www.linkedin.com/company/ashhra/posts/?feedView=all",        "vertical": "healthcare"},
    {"slug": "hr-healthcare", "url": "https://www.linkedin.com/company/hr-healthcare/posts/?feedView=all", "vertical": "healthcare"},
    {"slug": "hhram",         "url": "https://www.linkedin.com/company/hhram/posts/?feedView=all",         "vertical": "healthcare"},
    {"slug": "cupa-hr",       "url": "https://www.linkedin.com/company/cupa-hr/posts/?feedView=all",       "vertical": "education"},
]

TOPIC_KEYWORDS = [
    "onboarding", "offboarding", "hr automation", "hr operations",
    "employee engagement", "employee retention", "healthcare staffing",
    "caregiver", "credential", "license", "frontline workforce",
    "school hr", "teacher", "staff onboarding", "hr technology",
    "workforce", "new hire", "hris", "people operations",
    "human resources", "hr tech", "compliance", "i-9",
]

SKIP_KEYWORDS = [
    "resume tip", "salary advice", "job search tip", "cover letter",
    "interview tip", "how to get hired", "linkedin algorithm",
]

PRIORITY_TITLES = {
    "chro": 30, "chief human resources": 30, "chief people officer": 30,
    "vp human resources": 28, "vp of human resources": 28, "vp people": 28,
    "head of hr": 27, "head of people": 27, "svp hr": 27,
    "hr director": 25, "director of human resources": 25, "director of people": 25,
    "director of hr": 25, "hris director": 25, "people operations director": 25,
    "hr operations director": 25,
    "hr manager": 20, "human resources manager": 20, "hris manager": 20,
    "people operations manager": 20, "employee experience director": 20,
    "coo": 22, "chief operating officer": 22,
    "associate vp": 22, "avp hr": 22,
    "hr generalist": 8, "hr business partner": 10, "hr specialist": 8,
    "hr coordinator": 3,
}

EXCLUDE_TITLE_SIGNALS = [
    "talent acquisition", "recruiter", "sourcer", "headhunter",
    "intern", "student", "consultant", "freelance",
    "account executive", "business development", "bdr", "sdr",
    "sales director", "sales manager", "marketing",
    "vendor", "software company", "hr platform", "hr tech company",
]

PRIORITY_INDUSTRIES = {
    "hospital": 22, "health system": 22, "medical center": 22,
    "home health": 22, "home care": 22, "hospice": 20,
    "senior living": 20, "assisted living": 20, "memory care": 20,
    "behavioral health": 18, "addiction": 18, "mental health": 18,
    "healthcare": 18, "clinic": 16, "medical": 16,
    "university": 18, "college": 18, "higher education": 18,
    "community college": 18, "school district": 18, "k-12": 18,
    "education": 15,
    "nonprofit": 10,
}

OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "linkedin_leads.csv"
OUTPUT_FIELDS = [
    "first_name", "last_name", "linkedin_url", "job_title", "company_name",
    "company_size", "industry", "location", "source_page", "source_post_url",
    "post_topic", "engagement_type", "comment_text", "engagement_date",
    "engagement_count", "lead_score", "lead_tier", "qualification_reason",
    "outreach_angle", "email", "email_status",
]

COOKIES_PATH = Path("/tmp/linkedin_session_cookies.json")

# ── BROWSER HELPERS ───────────────────────────────────────────────────────────

def wait_for_linkedin_feed(page, timeout=60_000):
    """Wait until the LinkedIn feed is loaded (not the login wall)."""
    try:
        page.wait_for_selector(
            "div.feed-shared-update-v2, div[data-urn], article.social-feed-container",
            timeout=timeout,
        )
        return True
    except PlaywrightTimeout:
        return False


def is_logged_in(page) -> bool:
    return "feed" in page.url or page.query_selector("div.global-nav__me") is not None


def login_flow(page, cookies_path: Path):
    """Open LinkedIn login, auto-detect when user logs in, save cookies."""
    page.goto("https://www.linkedin.com/login", wait_until="networkidle")
    if is_logged_in(page):
        print("  Already logged in.", flush=True)
        return

    print("\n" + "=" * 60, flush=True)
    print("  ACTION REQUIRED: Log into LinkedIn in the browser window.", flush=True)
    print("  This script will auto-continue once your feed is detected.", flush=True)
    print("=" * 60, flush=True)

    # Poll every 3 seconds for up to 3 minutes for successful login
    deadline = time.time() + 180
    while time.time() < deadline:
        try:
            page.wait_for_selector(
                "div.global-nav__me, div.feed-shared-update-v2, "
                "div[data-urn], .scaffold-layout__main",
                timeout=3000,
            )
            if is_logged_in(page):
                break
        except PlaywrightTimeout:
            pass
        time.sleep(1)
    else:
        print("  Timeout waiting for login. Exiting.", flush=True)
        sys.exit(1)

    print("  Login detected — continuing.", flush=True)
    cookies = page.context.cookies()
    li_cookies = [c for c in cookies if "linkedin" in c.get("domain", "")]
    cookies_path.write_text(json.dumps(li_cookies, indent=2))
    print(f"  Session saved ({len(li_cookies)} cookies).", flush=True)


def load_cookies(context, cookies_path: Path):
    if cookies_path.exists():
        cookies = json.loads(cookies_path.read_text())
        context.add_cookies(cookies)
        print(f"  Loaded {len(cookies)} saved cookies.", flush=True)
        return True
    return False


def scroll_to_load(page, times=4, pause=2.0):
    """Scroll down to trigger lazy-loaded content."""
    for _ in range(times):
        page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
        time.sleep(pause)

# ── POST EXTRACTION ───────────────────────────────────────────────────────────

def classify_topic(text: str) -> str:
    t = text.lower()
    if any(s in t for s in SKIP_KEYWORDS):
        return ""
    topic_map = [
        (["onboarding automation", "automate onboarding", "digital onboarding", "paperless"], "onboarding_automation"),
        (["caregiver onboarding", "caregiver hiring", "home health", "home care"], "caregiver_onboarding"),
        (["credential", "license track", "license verif", "certif"], "credential_tracking"),
        (["frontline workforce", "frontline worker", "frontline staff"], "frontline_workforce"),
        (["healthcare staffing", "nursing staffing", "clinical staff"], "healthcare_staffing"),
        (["employee retention", "retain employee", "turnover", "attrition"], "employee_retention"),
        (["employee engagement", "engagement survey", "culture"], "employee_engagement"),
        (["offboarding", "off-boarding", "separation"], "offboarding"),
        (["hr automation", "hr technology", "hr tech", "hris", "hrms"], "hr_automation"),
        (["new hire", "new employee", "orientation", "day one", "first day", "onboarding"], "employee_onboarding"),
        (["hr operations", "people operations", "hr ops"], "hr_operations"),
        (["teacher", "school hr", "higher education hr", "university hr", "district hr"], "education_hr"),
        (["workforce", "staffing", "hiring", "talent"], "workforce_management"),
    ]
    for kws, topic in topic_map:
        if any(kw in t for kw in kws):
            return topic
    return "hr_general"


def extract_posts_from_feed(page, source: dict) -> list:
    """Extract post URLs + text from a company's LinkedIn posts feed."""
    print(f"\n  Loading feed: {source['url']}", flush=True)
    try:
        page.goto(source["url"], wait_until="domcontentloaded", timeout=30_000)
    except PlaywrightTimeout:
        print("  Timeout loading feed, continuing...", flush=True)

    scroll_to_load(page, times=6, pause=2.5)

    posts = []
    seen_urns = set()

    # Find all post containers
    post_els = page.query_selector_all(
        "div.feed-shared-update-v2, div[data-urn*='activity'], article[data-id]"
    )
    print(f"  Found {len(post_els)} post elements", flush=True)

    for el in post_els[:30]:
        try:
            # Get post URN / URL
            urn = el.get_attribute("data-urn") or el.get_attribute("data-id") or ""
            if not urn or urn in seen_urns:
                continue
            seen_urns.add(urn)

            # Extract activity ID from urn like "urn:li:activity:12345"
            activity_match = re.search(r"activity[:\-](\d+)", urn)
            if not activity_match:
                continue
            activity_id = activity_match.group(1)
            post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}/"

            # Extract post text
            text_el = el.query_selector(
                "span.break-words, div.feed-shared-text, div.update-components-text"
            )
            text = text_el.inner_text() if text_el else ""

            # Reaction + comment count
            reaction_el = el.query_selector("span.social-counts-reactions__count, span[aria-label*='reaction']")
            comment_el = el.query_selector("button[aria-label*='comment'], span[aria-label*='comment']")

            reactions = 0
            comments = 0
            if reaction_el:
                m = re.search(r"(\d[\d,]*)", reaction_el.inner_text())
                if m:
                    reactions = int(m.group(1).replace(",", ""))
            if comment_el:
                m = re.search(r"(\d[\d,]*)", comment_el.get_attribute("aria-label") or comment_el.inner_text())
                if m:
                    comments = int(m.group(1).replace(",", ""))

            # Date (approximate)
            date_el = el.query_selector("span[aria-label*='ago'], time, abbr[title]")
            post_date = ""
            if date_el:
                post_date = date_el.get_attribute("aria-label") or date_el.get_attribute("title") or date_el.inner_text()
                post_date = post_date.strip()[:30]

            topic = classify_topic(text)

            posts.append({
                "url": post_url,
                "source_slug": source["slug"],
                "source_page": source["url"],
                "text": text[:500],
                "topic": topic,
                "reactions": reactions,
                "comments": comments,
                "post_date": post_date,
            })

        except Exception as e:
            continue

    return posts

# ── COMMENTER EXTRACTION ──────────────────────────────────────────────────────

def extract_engagers_from_post(page, post: dict) -> list:
    """Visit a post page and extract all visible commenters + their comments."""
    try:
        page.goto(post["url"], wait_until="domcontentloaded", timeout=25_000)
    except PlaywrightTimeout:
        return []

    time.sleep(2)

    # Click "Load more comments" repeatedly
    for _ in range(5):
        load_more = page.query_selector("button[aria-label*='Load more comments'], button.comments-comments-list__load-more-comments-button")
        if load_more:
            try:
                load_more.click()
                time.sleep(1.5)
            except Exception:
                break
        else:
            break

    engagers = []
    seen_slugs = set()

    # Extract commenters
    comment_els = page.query_selector_all(
        "article.comments-comment-item, div.comments-comment-item, li.comments-comment-item"
    )

    for el in comment_els:
        try:
            # Name + profile link
            name_el = el.query_selector("span.comments-post-meta__name, a.comments-post-meta__actor-link span, span.hoverable-link-text")
            link_el = el.query_selector("a.comments-post-meta__actor-link, a[href*='/in/']")

            if not name_el or not link_el:
                continue

            name = name_el.inner_text().strip()
            href = link_el.get_attribute("href") or ""
            slug_m = re.search(r"/in/([a-zA-Z0-9\-]+)", href)
            if not slug_m:
                continue
            slug = slug_m.group(1)
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            # Comment text
            text_el = el.query_selector(
                "span.comments-comment-item__main-content, div.comments-comment-item__main-content, span.break-words"
            )
            comment_text = text_el.inner_text().strip()[:300] if text_el else ""

            profile_url = f"https://www.linkedin.com/in/{slug}"
            engagers.append({
                "name": name,
                "slug": slug,
                "profile_url": profile_url,
                "comment_text": comment_text,
                "engagement_type": "comment",
            })
        except Exception:
            continue

    # Also extract reactors (reaction list modal)
    try:
        reaction_btn = page.query_selector("button[aria-label*='reaction'], span.social-counts-reactions__count")
        if reaction_btn and post.get("reactions", 0) > 0:
            reaction_btn.click()
            time.sleep(2)
            # Scroll the modal
            modal = page.query_selector("div.social-details-social-activity, div[aria-label*='Reactions']")
            if modal:
                for _ in range(3):
                    modal.evaluate("el => el.scrollTop += 400")
                    time.sleep(1)
                # Extract reactor names
                reactor_els = page.query_selector_all(
                    "div.social-details-social-counts__reaction-count a, li.social-details-reactors-facepile__item a[href*='/in/']"
                )
                for el in reactor_els:
                    href = el.get_attribute("href") or ""
                    slug_m = re.search(r"/in/([a-zA-Z0-9\-]+)", href)
                    if not slug_m:
                        continue
                    slug = slug_m.group(1)
                    if slug in seen_slugs:
                        continue
                    seen_slugs.add(slug)
                    name_el = el.query_selector("span, div")
                    name = name_el.inner_text().strip() if name_el else slug
                    engagers.append({
                        "name": name,
                        "slug": slug,
                        "profile_url": f"https://www.linkedin.com/in/{slug}",
                        "comment_text": "",
                        "engagement_type": "reaction",
                    })
            # Close modal
            close_btn = page.query_selector("button[aria-label*='Dismiss'], button.artdeco-modal__dismiss")
            if close_btn:
                close_btn.click()
    except Exception:
        pass

    return engagers

# ── PROFILE ENRICHMENT ────────────────────────────────────────────────────────

def extract_profile(page, profile_url: str) -> dict:
    """Visit a LinkedIn profile and extract structured data from the DOM."""
    try:
        page.goto(profile_url, wait_until="domcontentloaded", timeout=25_000)
    except PlaywrightTimeout:
        return {}

    time.sleep(1.5)

    profile = {"job_title": "", "company_name": "", "company_size": "", "industry": "", "location": ""}

    # Headline (job title)
    headline_sel = [
        "div.text-body-medium.break-words",
        "div[data-generated-suggestion-target] div.text-body-medium",
        "h2.mt1.t-18.t-black.t-normal",
        "span.pv-text-details__right-panel-item-text",
    ]
    for sel in headline_sel:
        el = page.query_selector(sel)
        if el:
            txt = el.inner_text().strip()
            if txt and len(txt) > 5:
                profile["job_title"] = txt[:100]
                break

    # Location
    loc_sel = [
        "span.text-body-small.inline.t-black--light.break-words",
        "span[aria-label*='Location']",
        "div.pv-text-details__left-panel span:nth-child(2)",
    ]
    for sel in loc_sel:
        el = page.query_selector(sel)
        if el:
            txt = el.inner_text().strip()
            if txt and len(txt) > 3 and "connection" not in txt.lower():
                profile["location"] = txt[:80]
                break

    # Current company from experience section
    exp_sel = [
        "section[data-view-name*='profile-card'] li.artdeco-list__item:first-child span.t-bold span",
        "div#experience-section li:first-child h3",
        "li.experience-item:first-child span.pv-entity__secondary-title",
    ]
    for sel in exp_sel:
        el = page.query_selector(sel)
        if el:
            txt = el.inner_text().strip()
            if txt and len(txt) > 2:
                profile["company_name"] = txt[:80]
                break

    # Also try to get company from "at Company" in headline
    if not profile["company_name"] and profile["job_title"]:
        at_m = re.search(r"\bat\s+([A-Z][A-Za-z0-9\s\&\-\.]{3,50})$", profile["job_title"])
        if at_m:
            profile["company_name"] = at_m.group(1).strip()

    # Industry from About section or profile page
    about_el = page.query_selector("section.pv-about-section, div#about, div.pv-profile-section.pv-about-section")
    if about_el:
        about_text = about_el.inner_text().lower()
        for kw in ["hospital", "health system", "home health", "senior living", "behavioral health",
                   "university", "college", "school district", "k-12", "education"]:
            if kw in about_text:
                profile["industry"] = kw.title()
                break

    # Company size — often in the company sidebar or experience section
    size_el = page.query_selector("span[aria-label*='employees'], div.org-about-module__description")
    if size_el:
        m = re.search(r"(\d[\d,]+\s*[–-]\s*\d[\d,]+|\d[\d,]+\+?)\s*employees?", size_el.inner_text(), re.I)
        if m:
            profile["company_size"] = m.group(0)

    return profile

# ── ICP SCORING ───────────────────────────────────────────────────────────────

def score_lead(name: str, profile: dict, post: dict, comment: str, post_count: int) -> dict:
    title = (profile.get("job_title") or "").lower()
    company = (profile.get("company_name") or "").lower()
    industry = (profile.get("industry") or "").lower()
    score = 0
    reasons = []

    # Hard excludes
    combined = title + " " + company
    for ex in EXCLUDE_TITLE_SIGNALS:
        if ex in combined:
            return {"score": 0, "tier": "EXCLUDED", "reason": f"Excluded: {ex}"}

    # Title (0–30)
    title_pts = 0
    matched = ""
    for t_key, t_pts in PRIORITY_TITLES.items():
        if t_key in title:
            title_pts = t_pts
            matched = t_key
            break
    if title_pts == 0:
        if not title:
            title_pts = 5
            reasons.append("Title unknown — needs verification")
        else:
            return {"score": 0, "tier": "SKIP", "reason": f"Non-ICP title: {title[:50]}"}
    else:
        reasons.append(f"Title match: {matched} (+{title_pts})")
    score += title_pts

    # Industry (0–22)
    ind_pts = 0
    ind_text = industry + " " + company
    for kw, pts in PRIORITY_INDUSTRIES.items():
        if kw in ind_text:
            ind_pts = max(ind_pts, pts)
    if ind_pts:
        reasons.append(f"Industry match (+{ind_pts})")
    score += ind_pts

    # Engagement quality (0–20)
    if comment and len(comment) > 30:
        score += 20
        reasons.append("Substantive comment (+20)")
    elif comment and len(comment) > 10:
        score += 12
        reasons.append("Short comment (+12)")
    else:
        score += 4

    # Comment content relevance (0–10)
    c_lower = comment.lower()
    if any(kw in c_lower for kw in ["onboard", "staffing", "hire", "hr", "workforce", "compliance", "credential", "retention", "process", "automate"]):
        score += 10
        reasons.append("Comment mentions HR ops topic (+10)")

    # Post topic (0–10)
    topic = post.get("topic", "")
    high_val = ["onboarding_automation", "caregiver_onboarding", "credential_tracking", "hr_automation", "frontline_workforce", "healthcare_staffing"]
    mid_val = ["employee_onboarding", "hr_operations", "employee_retention", "education_hr"]
    if topic in high_val:
        score += 10
        reasons.append(f"High-value topic: {topic} (+10)")
    elif topic in mid_val:
        score += 7
    elif topic:
        score += 3

    # Multi-post engagement
    if post_count >= 2:
        score += 8
        reasons.append(f"Engaged {post_count} posts (+8)")

    # Location US
    loc = profile.get("location", "")
    us_signals = [", CA", ", NY", ", TX", ", FL", ", IL", ", PA", ", OH", ", GA", ", NC", ", VA",
                  ", WA", ", MA", ", AZ", ", TN", ", CO", ", MD", ", MI", ", MN", ", OR",
                  "United States", "Greater", "Metro"]
    if any(s in loc for s in us_signals):
        score += 5
        reasons.append("US-based (+5)")

    score = min(100, score)
    if score >= 65:
        tier = "A"
    elif score >= 45:
        tier = "B"
    elif score >= 25:
        tier = "C"
    else:
        tier = "SKIP"

    return {"score": score, "tier": tier, "reason": "; ".join(reasons)}


def build_outreach_angle(profile: dict, post: dict, comment: str) -> str:
    company = profile.get("company_name") or "your organization"
    topic = post.get("topic", "")
    angles = {
        "onboarding_automation": f"Ask how {company} handles new hire paperwork — whether staff complete I-9s and compliance docs before day one.",
        "caregiver_onboarding": f"Ask how they manage caregiver onboarding across locations — whether credential verification is still paper-based.",
        "credential_tracking": f"Ask how they currently verify and track licenses at hire — spreadsheets or integrated into HRIS.",
        "healthcare_staffing": f"Ask what slows onboarding when ramping healthcare staff quickly — paperwork or background/credential bottlenecks.",
        "employee_retention": f"Ask how much of the retention problem they believe is tied to a poor first-30-day experience.",
        "hr_automation": f"Ask which HR workflows {company} has already automated and which are still manual.",
        "employee_onboarding": f"Ask how many new hires they process monthly and whether current onboarding creates day-one delays.",
        "education_hr": f"Ask how they handle seasonal hiring surges and whether staff onboarding creates a bottleneck.",
        "frontline_workforce": f"Ask how they communicate with frontline staff without work email — and if that affects onboarding completion rates.",
        "employee_engagement": f"Ask whether their engagement data shows a first-90-day dip and how they connect that to the onboarding experience.",
    }
    base = angles.get(topic, f"Ask how {company} manages new employee onboarding and HR documentation.")
    if comment and len(comment) > 20:
        return f"They commented: '{comment[:100]}'. {base}"
    return base


def build_qual_reason(profile: dict, post: dict, comment: str) -> str:
    title = profile.get("job_title") or "HR Professional"
    company = profile.get("company_name") or ""
    industry = profile.get("industry") or ""
    topic = (post.get("topic") or "").replace("_", " ")
    source = post.get("source_slug", "")

    parts = [title]
    if company:
        parts.append(f"at {company}")
    if industry:
        parts.append(f"({industry})")
    if comment and len(comment) > 15:
        parts.append(f"who commented: '{comment[:80]}'")
    else:
        parts.append(f"who engaged with {source} community content about {topic}")
    return " ".join(parts)

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LinkedIn engagement lead finder — connects to your real Chrome")
    parser.add_argument("--cdp", action="store_true", default=True,
                        help="Connect to real Chrome via CDP (default; Chrome must be started with --remote-debugging-port=9222)")
    parser.add_argument("--cdp-port", type=int, default=9222, help="CDP port (default: 9222)")
    parser.add_argument("--headless", action="store_true", help="Launch headless Playwright Chromium instead of CDP")
    parser.add_argument("--posts-per-source", type=int, default=15, help="Max posts per company page")
    parser.add_argument("--max-leads", type=int, default=200, help="Max total engagers to process")
    args = parser.parse_args()

    use_cdp = not args.headless  # CDP is default unless --headless overrides

    OUTPUT_PATH.parent.mkdir(exist_ok=True)

    print("=" * 70, flush=True)
    print("LinkedIn Engagement Lead Finder — HR Cloud ICP", flush=True)
    print(f"Mode: {'CDP (real Chrome)' if use_cdp else 'Playwright Chromium'}", flush=True)
    print(f"Sources: {len(SOURCES)} | Posts/source: {args.posts_per_source} | Max leads: {args.max_leads}", flush=True)
    print("=" * 70, flush=True)

    with sync_playwright() as p:
        if use_cdp:
            cdp_url = f"http://localhost:{args.cdp_port}"
            print(f"\nPhase 0: Connecting to Chrome at {cdp_url}", flush=True)
            try:
                browser = p.chromium.connect_over_cdp(cdp_url)
            except Exception as e:
                print(f"\n  ERROR: Could not connect to Chrome.", flush=True)
                print(f"  {e}", flush=True)
                print("\n  Fix: Quit Chrome completely, then run:", flush=True)
                print(f'    pkill -x "Google Chrome"', flush=True)
                print(f'    open -a "Google Chrome" --args --remote-debugging-port={args.cdp_port}', flush=True)
                print("  Then go to linkedin.com in that Chrome window (log in if needed).", flush=True)
                print("  Then re-run this script.", flush=True)
                sys.exit(1)

            # Use existing context + existing LinkedIn page if available
            contexts = browser.contexts
            context = contexts[0] if contexts else browser.new_context()

            # Find an existing LinkedIn page or open a new one
            page = None
            for ctx in browser.contexts:
                for pg in ctx.pages:
                    if "linkedin.com" in pg.url:
                        page = pg
                        print(f"  Using existing LinkedIn page: {pg.url}", flush=True)
                        break
                if page:
                    break

            if page is None:
                page = context.new_page()
                page.goto("https://www.linkedin.com/feed", wait_until="domcontentloaded", timeout=30_000)
                time.sleep(2)

        else:
            # Fallback: launch Playwright Chromium (may be blocked by LinkedIn)
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page = context.new_page()
            load_cookies(context, COOKIES_PATH)
            page.goto("https://www.linkedin.com", wait_until="domcontentloaded", timeout=20_000)
            time.sleep(2)

        # ── Auth check ────────────────────────────────────────────────────────
        print("\nPhase 0: Authentication", flush=True)
        if not is_logged_in(page):
            if use_cdp:
                print("  Not logged into LinkedIn in Chrome. Please log in now...", flush=True)
                page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
                login_flow(page, COOKIES_PATH)
            else:
                load_cookies(context, COOKIES_PATH)
                page.reload(wait_until="domcontentloaded")
                time.sleep(2)
                if not is_logged_in(page):
                    print("ERROR: Not logged in. Run with --cdp mode (default).", flush=True)
                    sys.exit(1)

        print("  Logged in ✓", flush=True)

        # ── Phase 1: Discover qualifying posts ────────────────────────────────
        print("\nPhase 1: Discovering posts from 4 sources...", flush=True)
        all_posts = []
        for source in SOURCES:
            posts = extract_posts_from_feed(page, source)
            qualifying = [p for p in posts if p["topic"]]
            print(f"  [{source['slug']}] {len(posts)} posts → {len(qualifying)} qualifying", flush=True)
            for p in qualifying[:args.posts_per_source]:
                print(f"    [{p['topic']}] {p['url'][-60:]} | {p['reactions']}r {p['comments']}c", flush=True)
            all_posts.extend(qualifying[:args.posts_per_source])
            time.sleep(1)

        print(f"\n  Total qualifying posts: {len(all_posts)}", flush=True)

        # ── Phase 2: Extract engagers from each post ──────────────────────────
        print("\nPhase 2: Extracting engagers from qualifying posts...", flush=True)
        seen_slugs: dict = {}  # slug → {engager, post, count}

        for post in all_posts:
            print(f"\n  [{post['source_slug']}] {post['url'][-70:]}", flush=True)
            engagers = extract_engagers_from_post(page, post)
            print(f"    → {len(engagers)} engagers extracted", flush=True)

            for eng in engagers:
                slug = eng["slug"]
                if slug not in seen_slugs:
                    seen_slugs[slug] = {"engager": eng, "post": post, "count": 1}
                else:
                    seen_slugs[slug]["count"] += 1

            if len(seen_slugs) >= args.max_leads:
                break
            time.sleep(2)

        print(f"\n  Total unique engagers: {len(seen_slugs)}", flush=True)

        # ── Phase 3: Enrich profiles ──────────────────────────────────────────
        print("\nPhase 3: Enriching profiles...", flush=True)
        leads = []
        items = list(seen_slugs.values())

        for i, item in enumerate(items):
            eng = item["engager"]
            post = item["post"]
            count = item["count"]
            name = eng["name"]
            profile_url = eng["profile_url"]
            comment = eng["comment_text"]

            print(f"  [{i+1}/{len(items)}] {name} — {profile_url}", flush=True)
            profile = extract_profile(page, profile_url)
            time.sleep(1.5)

            score_result = score_lead(name, profile, post, comment, count)
            tier = score_result["tier"]

            if tier in ("SKIP", "EXCLUDED"):
                print(f"    → {tier}: {score_result['reason'][:70]}", flush=True)
                continue

            name_parts = name.split()
            first = name_parts[0] if name_parts else ""
            last = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            last = re.sub(r",?\s*(MBA|PHR|SHRM|SPHR|CHHR|PhD|EdD|CPC|FACHE|RACR|RACL|SWP)\S*.*$", "", last).strip()

            leads.append({
                "first_name": first,
                "last_name": last,
                "linkedin_url": profile_url,
                "job_title": profile.get("job_title") or name,
                "company_name": profile.get("company_name", ""),
                "company_size": profile.get("company_size", ""),
                "industry": profile.get("industry", ""),
                "location": profile.get("location", ""),
                "source_page": post["source_page"],
                "source_post_url": post["url"],
                "post_topic": post.get("topic", ""),
                "engagement_type": eng["engagement_type"],
                "comment_text": comment,
                "engagement_date": post.get("post_date", ""),
                "engagement_count": (post.get("reactions", 0) or 0) + (post.get("comments", 0) or 0),
                "lead_score": score_result["score"],
                "lead_tier": f"Tier {tier}",
                "qualification_reason": build_qual_reason(profile, post, comment),
                "outreach_angle": build_outreach_angle(profile, post, comment),
                "email": "",
                "email_status": "NOT_ENRICHED",
            })
            print(f"    → Tier {tier} (score={score_result['score']}): {score_result['reason'][:80]}", flush=True)

        if not use_cdp:
            browser.close()

    # ── Sort + write CSV ──────────────────────────────────────────────────────
    tier_order = {"Tier A": 0, "Tier B": 1, "Tier C": 2}
    leads.sort(key=lambda r: (tier_order.get(r["lead_tier"], 9), -r["lead_score"]))

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        w.writeheader()
        w.writerows(leads)

    print("\n" + "=" * 70, flush=True)
    print(f"Total qualified leads: {len(leads)}", flush=True)
    tier_counts: dict = {}
    for r in leads:
        tier_counts[r["lead_tier"]] = tier_counts.get(r["lead_tier"], 0) + 1
    for t, c in sorted(tier_counts.items()):
        print(f"  {t}: {c}", flush=True)
    print(f"\nOutput → {OUTPUT_PATH}", flush=True)
    print("\nTop 20:", flush=True)
    for r in leads[:20]:
        print(f"  [{r['lead_tier']}/{r['lead_score']:3d}] {r['first_name']} {r['last_name']:<20} | {r.get('job_title','')[:38]:<38} | {r.get('company_name','')}", flush=True)


if __name__ == "__main__":
    main()
