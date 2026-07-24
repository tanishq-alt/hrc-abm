"""Canonical output schema used by ALL 7 HR Intel prompts.

Every scraper should produce rows conforming to CANONICAL_FIELDS and use
make_row() to fill in defaults, ensuring consistent CSV output.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# ── CSV column names (25 canonical columns) ──────────────────────────────────
CANONICAL_FIELDS = [
    "company_name",
    "canonical_domain",
    "country",
    "industry",
    "employee_range",
    "location_count_or_range",
    "primary_signal_category",
    "signal_date",
    "strongest_signal_summary",
    "strongest_signal_url",
    "second_signal_summary",
    "second_signal_url",
    "adp_status",
    "adp_product_or_scope",
    "fit_score",
    "intent_score",
    "evidence_score",
    "timing_score",
    "uniqueness_score",
    "total_score",
    "confidence",
    "best_hr_cloud_product",
    "outreach_angle",
    "recommended_buyer_titles",
    "disqualifiers_or_risks",
]

# domain_status values
DOMAIN_STATUS_VERIFIED = "verified"
DOMAIN_STATUS_VERIFIED_PARENT_ONLY = "verified_parent_only"
DOMAIN_STATUS_FACILITY_NO_UNIQUE = "facility_no_unique_domain"
DOMAIN_STATUS_UNRESOLVED = "unresolved"

# adp_status values
ADP_CONFIRMED = "confirmed"
ADP_STRONGLY_LIKELY = "strongly_likely"
ADP_NOT_FOUND = "not_found"
ADP_NOT_CHECKED = "not_checked"

# confidence values
CONFIDENCE_CONFIRMED = "confirmed"
CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"

# best_hr_cloud_product values
PRODUCT_ONBOARD = "Onboard"
PRODUCT_WORKMATES = "Workmates"
PRODUCT_ONBOARD_WORKMATES = "Onboard+Workmates"
PRODUCT_OTHER = "Other"


@dataclass
class Signal:
    """One piece of evidence supporting the lead."""
    signal_type: str = ""
    source_tier: str = "C"           # A, B, or C
    source_title: str = ""
    exact_url: str = ""
    source_date: str = ""
    access_date: str = ""
    evidence_excerpt_max_30_words: str = ""
    what_it_proves: str = ""
    what_it_does_not_prove: str = ""


@dataclass
class LeadRecord:
    """Full canonical lead record. Use make_row() to produce a CSV-ready dict."""
    # Identity
    company_name: str = ""
    legal_or_parent_name: str = ""
    canonical_domain: str = ""
    domain_status: str = DOMAIN_STATUS_UNRESOLVED

    # Classification
    company_type: str = ""
    industry: str = ""
    subindustry: str = ""
    hq_city: str = ""
    hq_state_province: str = ""
    country: str = "US"

    # Size
    employee_range: str = ""
    employee_range_source_url: str = ""
    location_count_or_range: str = ""
    location_source_url: str = ""
    frontline_or_hourly_workforce_evidence: str = ""

    # ADP
    adp_status: str = ADP_NOT_CHECKED
    adp_product_or_scope: str = ""
    adp_evidence_url: str = ""

    # Primary signal
    primary_signal_category: str = ""
    signal_date: str = ""
    freshness_days: int = 0
    signals: List[Signal] = field(default_factory=list)

    # Scoring (each 0-100 range as described in playbook)
    fit_score: int = 0
    intent_score: int = 0
    evidence_score: int = 0
    timing_score: int = 0
    uniqueness_score: int = 0
    total_score: int = 0

    # Qualification
    confidence: str = CONFIDENCE_MEDIUM
    best_hr_cloud_product: str = PRODUCT_ONBOARD

    # Outreach
    why_hr_cloud_fits: str = ""
    recommended_buyer_titles: str = ""
    outreach_angle: str = ""
    safe_personalized_first_line: str = ""
    recommended_cta: str = ""
    disqualifiers_or_risks: str = ""
    next_verification_step: str = ""

    # Evidence convenience fields (top 2 signals flattened for CSV)
    strongest_signal_summary: str = ""
    strongest_signal_url: str = ""
    second_signal_summary: str = ""
    second_signal_url: str = ""


def make_row(record: LeadRecord) -> dict:
    """Convert a LeadRecord to a flat CSV dict using CANONICAL_FIELDS columns."""
    # Auto-populate flattened signal fields from signals list
    if record.signals:
        s0 = record.signals[0]
        record.strongest_signal_summary = s0.evidence_excerpt_max_30_words or s0.what_it_proves
        record.strongest_signal_url = s0.exact_url
    if len(record.signals) >= 2:
        s1 = record.signals[1]
        record.second_signal_summary = s1.evidence_excerpt_max_30_words or s1.what_it_proves
        record.second_signal_url = s1.exact_url

    d = asdict(record)
    row = {}
    for col in CANONICAL_FIELDS:
        row[col] = d.get(col, "")
    return row


def make_row_from_dict(data: dict) -> dict:
    """Build a canonical CSV row from a plain dict, filling missing keys with ''."""
    row = {}
    for col in CANONICAL_FIELDS:
        row[col] = data.get(col, "")
    return row
