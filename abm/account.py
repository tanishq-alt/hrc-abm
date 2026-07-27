"""Full enriched Account dataclass — the canonical ABM record."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Account:
    # ── Identity ──────────────────────────────────────────────────────────────
    company_name: str = ""
    canonical_domain: str = ""
    domain_status: str = "unresolved"   # verified / verified_parent_only / unresolved

    # ── Firmographics ─────────────────────────────────────────────────────────
    industry: str = ""
    vertical: str = ""                  # healthcare / education / manufacturing / etc.
    employee_range: str = ""
    location_count: str = ""
    hq_city: str = ""
    hq_state: str = ""
    country: str = "US"
    is_multi_location: bool = False
    is_frontline_workforce: bool = False

    # ── Technographics ────────────────────────────────────────────────────────
    adp_status: str = "not_checked"     # confirmed / strongly_likely / not_found / not_checked
    adp_product: str = ""               # ADP Workforce Now / ADP Run / TotalSource
    hris_incumbent: str = ""            # any detected HRIS
    has_modern_onboarding: bool = False
    has_paper_evidence: bool = False

    # ── Signals ───────────────────────────────────────────────────────────────
    primary_signal_type: str = ""
    primary_signal_tier: str = ""
    primary_evidence_excerpt: str = ""
    primary_evidence_url: str = ""
    second_signal_type: str = ""
    second_evidence_excerpt: str = ""
    second_evidence_url: str = ""
    signal_count: int = 0
    trigger_signal_types: List[str] = field(default_factory=list)

    # ── Scores ────────────────────────────────────────────────────────────────
    icp_firmographic: int = 0
    icp_technographic: int = 0
    icp_behavioral: int = 0
    icp_buying_trigger: int = 0
    icp_score: int = 0
    signal_score: int = 0
    composite_score: int = 0            # final 0-100 score

    # ── Tier & qualification ──────────────────────────────────────────────────
    account_tier: str = ""              # Tier 1 / Tier 2 / Tier 3 / Disqualified
    is_qualified: bool = False
    rejection_reason: str = ""
    disqualifiers: str = ""

    # ── Buying committee ──────────────────────────────────────────────────────
    champion_title: str = ""
    economic_buyer_title: str = ""
    influencer_title: str = ""

    # ── Outreach ──────────────────────────────────────────────────────────────
    best_hr_cloud_product: str = "Onboard"
    outreach_angle: str = ""
    safe_first_line: str = ""
    pain_hypothesis: str = ""
    proof_point: str = ""
    recommended_cta: str = ""
    email_subject_a: str = ""
    email_subject_b: str = ""
    email_1_body: str = ""
    email_2_body: str = ""
    email_3_body: str = ""
    linkedin_note: str = ""

    # ── Meta ──────────────────────────────────────────────────────────────────
    data_freshness_days: int = 0
    next_action: str = ""
    source_scraper: str = ""


# CSV export columns for Apollo / CRM import
ACCOUNT_CSV_FIELDS = [
    "account_tier",
    "composite_score",
    "company_name",
    "canonical_domain",
    "industry",
    "vertical",
    "employee_range",
    "hq_state",
    "country",
    "adp_status",
    "adp_product",
    "hris_incumbent",
    "primary_signal_type",
    "primary_signal_tier",
    "primary_evidence_excerpt",
    "primary_evidence_url",
    "second_signal_type",
    "second_evidence_excerpt",
    "signal_count",
    "icp_score",
    "signal_score",
    "best_hr_cloud_product",
    "champion_title",
    "economic_buyer_title",
    "safe_first_line",
    "outreach_angle",
    "email_subject_a",
    "email_subject_b",
    "recommended_cta",
    "disqualifiers",
    "next_action",
]
