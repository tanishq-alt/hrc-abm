"""
Domain and entity resolver.
Returns structured DomainResolution objects.
Legacy verify_domain() kept for backward compat.
"""
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse
import re


@dataclass
class DomainResolution:
    canonical_company_name: str = ""
    canonical_domain: str = ""
    entity_type: str = "employer"        # employer / facility / parent / district / franchise / government / unknown
    parent_company: str = ""
    parent_domain: str = ""
    facility_or_subsidiary: str = ""
    domain_status: str = "unresolved"   # verified / verified_parent_only / facility_no_unique_domain /
                                         # subsidiary_verified / government_entity_verified /
                                         # school_or_district_verified / franchise_parent_verified /
                                         # unresolved / non_employer_host / duplicate
    identity_confidence: str = "low"    # high / medium / low
    verification_evidence: str = ""
    dedupe_key: str = ""
    notes: str = ""


# ── Host blocklists ───────────────────────────────────────────────────────────
CDN_HOSTS = {
    "s3.amazonaws.com", "cloudfront.net", "storage.googleapis.com",
    "blob.core.windows.net", "r2.dev",
}

JOB_BOARDS = {
    "linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com",
    "monster.com", "careerbuilder.com", "simplyhired.com", "dice.com",
    "builtin.com", "handshake.com", "wellfound.com",
}

ATS_HOSTS = {
    "greenhouse.io", "lever.co", "workday.com", "myworkdayjobs.com",
    "icims.com", "taleo.net", "jobvite.com", "smartrecruiters.com",
    "breezy.hr", "recruitee.com", "pinpoint.co", "ashbyhq.com",
    "bamboohr.com", "rippling.com", "gusto.com", "paycom.com",
    "paylocity.com",
}

PAGE_HOSTS = {
    "wordpress.com", "squarespace.com", "wix.com", "weebly.com",
    "medium.com", "substack.com", "blogspot.com", "sites.google.com",
}

NON_EMPLOYER_HOSTS = CDN_HOSTS | JOB_BOARDS | ATS_HOSTS | PAGE_HOSTS

GENERIC_GOV_PATTERNS = [
    r"\.gov$", r"\.k12\.[a-z]{2}\.us$", r"\.edu$",
    r"county\.[a-z]{2}\.us$", r"cityof[a-z]+\.com$",
]

FRANCHISE_INDICATORS = ["franchise", "franchisee", "operator", "territory"]


def _netloc(url: str) -> str:
    try:
        parsed = urlparse(url if "://" in url else "https://" + url)
        return parsed.netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _root_domain(host: str) -> str:
    """Collapse subdomains to root domain."""
    parts = host.split(".")
    if len(parts) >= 3:
        # Keep known two-part TLDs
        if parts[-2] in ("k12", "co", "com", "org", "gov", "edu"):
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])
    return host


def _is_ats_subdomain(host: str) -> Optional[str]:
    """Detect ATS subdomains like jobs.company.com or company.greenhouse.io.
    Returns employer root if detectable, else None."""
    for ats in ATS_HOSTS:
        if host.endswith("." + ats) or host == ats:
            # e.g. acmecorp.greenhouse.io → acmecorp
            subdomain = host.replace("." + ats, "").replace(ats, "")
            if subdomain and "." not in subdomain:
                return subdomain  # candidate name, not a domain
            return None
    # subdomain patterns like jobs.employer.com, careers.employer.com
    ATS_SUBDOMAINS = {"jobs", "careers", "hiring", "apply", "recruit", "talent"}
    parts = host.split(".")
    if len(parts) >= 3 and parts[0] in ATS_SUBDOMAINS:
        return ".".join(parts[1:])
    return None


def _is_government(host: str) -> bool:
    for pat in GENERIC_GOV_PATTERNS:
        if re.search(pat, host):
            return True
    return False


def _is_school_district(host: str) -> bool:
    return bool(re.search(r"\.k12\.", host))


def resolve_domain(url: str, source_title: str = "", vertical: str = "") -> DomainResolution:
    """
    Full structured domain resolution.
    Returns DomainResolution with entity_type, status, and confidence.
    """
    res = DomainResolution()
    host = _netloc(url)
    if not host:
        res.domain_status = "unresolved"
        res.notes = "Cannot parse URL"
        return res

    root = _root_domain(host)

    # Step 1: ATS subdomain correction FIRST (before blanket blocklist)
    # e.g. acmecorp.greenhouse.io → extract employer name "acmecorp"
    employer_guess = _is_ats_subdomain(host)
    if employer_guess:
        res.notes = f"ATS subdomain corrected from {host}"
        if "." in employer_guess:
            res.canonical_domain = employer_guess
        else:
            # Only have a name, not a confirmed domain
            res.canonical_company_name = employer_guess
            res.domain_status = "unresolved"
            res.notes += " — employer domain not confirmed"
            return res

    # Step 2: Reject non-employer hosts (CDN, job boards, ATS roots, page hosts)
    if not employer_guess:
        for nh in NON_EMPLOYER_HOSTS:
            if host.endswith(nh) or root == nh:
                res.domain_status = "non_employer_host"
                res.notes = f"Blocked host: {nh}"
                return res

    if not employer_guess:
        res.canonical_domain = root

    # Step 3: CDN / document host check on the resolved domain
    for cdn in CDN_HOSTS:
        if cdn in host:
            res.domain_status = "non_employer_host"
            res.notes = f"CDN/document host: {cdn}"
            return res

    # Step 4: Government entity
    if _is_government(res.canonical_domain or root):
        res.entity_type = "government"
        res.domain_status = "government_entity_verified"
        res.identity_confidence = "medium"
        res.verification_evidence = f"Government TLD pattern: {res.canonical_domain}"
    # Step 5: School/district
    elif _is_school_district(host):
        res.entity_type = "district"
        res.domain_status = "school_or_district_verified"
        res.identity_confidence = "high"
        res.verification_evidence = f"k12 domain: {host}"
    else:
        res.entity_type = "employer"
        res.domain_status = "verified"
        res.identity_confidence = "medium"

    res.canonical_domain = res.canonical_domain or root
    res.dedupe_key = res.canonical_domain.lower()
    return res


# ── Backward-compatible function ──────────────────────────────────────────────
def verify_domain(url: str) -> tuple:
    """
    Legacy interface for backward compat with pipeline/run.py.
    Returns (canonical_domain, domain_status).
    """
    res = resolve_domain(url)
    return res.canonical_domain, res.domain_status


def is_resolvable(domain: str) -> bool:
    """Light DNS check — returns True if domain resolves (optional use)."""
    import socket
    try:
        socket.getaddrinfo(domain, None, socket.AF_INET)
        return True
    except Exception:
        return False
