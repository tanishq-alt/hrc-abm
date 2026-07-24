"""Canonical domain verification — 7-step protocol.

Returns domain_status as one of:
  verified                  — resolves to a unique company domain
  verified_parent_only      — domain is a parent/holding entity (not the operating brand)
  facility_no_unique_domain — location/facility without its own domain
  unresolved                — could not confirm a real company domain
"""
from urllib.parse import urlparse

# Step 2: manual corrections (common mis-parses)
DOMAIN_CORRECTIONS = {
    "workforcenow.adp.com": "adp.com",
    "jobs.lever.co": "lever.co",
    "boards.greenhouse.io": "greenhouse.io",
    "apply.workable.com": "workable.com",
    "careers.jobvite.com": "jobvite.com",
    "jobs.ashbyhq.com": "ashbyhq.com",
    "recruiting.myapps.paychex.com": "paychex.com",
}

# Step 3: CDN / generic hosting — not real company domains
GENERIC_HOSTS = {
    "s3.amazonaws.com",
    "hubspotusercontent.com",
    "squarespace.com",
    "webflow.io",
    "webflow.com",
    "wixsite.com",
    "hibu.com",
    "sharepoint.com",
    "drive.google.com",
    "dropbox.com",
    "docsend.com",
    "cloudfront.net",
    "fastly.net",
    "rackcdn.com",
    "azurewebsites.net",
    "netlify.app",
    "vercel.app",
    "pages.dev",
    "github.io",
    "wordpress.com",
    "blogspot.com",
    "medium.com",
    "substack.com",
}

# Known parent / holding-company indicators in domain
PARENT_INDICATORS = {
    "holdings", "group", "capital", "partners", "ventures", "associates",
    "corp", "llc", "inc", "co.",
}

# Job-board / aggregator domains that are not employer domains
JOB_BOARD_DOMAINS = {
    "indeed.com", "linkedin.com", "glassdoor.com", "ziprecruiter.com",
    "monster.com", "careerbuilder.com", "simplyhired.com", "salary.com",
    "payscale.com", "handshake.com", "wellfound.com", "seek.com",
    "workable.com", "lever.co", "greenhouse.io", "jobvite.com",
    "ashbyhq.com", "smartrecruiters.com", "icims.com", "taleo.net",
}


def _extract_netloc(url: str) -> str:
    """Step 1: extract netloc and strip www."""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def verify_domain(url: str) -> tuple[str, str]:
    """Run the 7-step domain verification protocol.

    Args:
        url: Raw URL or domain string to verify.

    Returns:
        (canonical_domain, domain_status) tuple.
        domain_status is one of: verified | verified_parent_only |
                                  facility_no_unique_domain | unresolved
    """
    # Step 1: extract netloc
    host = _extract_netloc(url)
    if not host:
        return ("", "unresolved")

    # Step 2: apply corrections
    if host in DOMAIN_CORRECTIONS:
        host = DOMAIN_CORRECTIONS[host]

    # Step 3: check CDN/generic → unresolved
    for generic in GENERIC_HOSTS:
        if host == generic or host.endswith("." + generic):
            return (host, "facility_no_unique_domain")

    # Step 3b: job board domains → unresolved
    for jb in JOB_BOARD_DOMAINS:
        if host == jb or host.endswith("." + jb):
            return (host, "unresolved")

    # Step 4: check for empty or IP-only
    import re
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
        return (host, "unresolved")

    # Step 5: collapse to root domain for dedup purposes
    parts = host.split(".")
    # Preserve k12.XX.us school district domains
    if len(parts) >= 4 and parts[-3] == "k12":
        canonical = host
    elif len(parts) >= 3 and parts[0] not in (
        "my", "cdn", "static", "uploads", "docs", "files",
        "assets", "api", "mail", "app", "portal", "careers",
    ):
        canonical = ".".join(parts[-2:])
    else:
        canonical = host

    # Step 6: check for parent/holding company signals in domain name
    domain_lower = canonical.lower()
    if any(indicator in domain_lower for indicator in PARENT_INDICATORS):
        return (canonical, "verified_parent_only")

    # Step 7: return verified
    return (canonical, "verified")


def is_resolvable(domain: str) -> bool:
    """Light DNS check — returns True if domain resolves (optional use)."""
    import socket
    try:
        socket.getaddrinfo(domain, None, socket.AF_INET)
        return True
    except Exception:
        return False
