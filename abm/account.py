"""Full enriched Account dataclass — the canonical ABM record."""
from dataclasses import dataclass, field
from typing import List, Dict


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

    # ── Independent scores (new model) ───────────────────────────────────────
    intent_score: int = 0                    # 0-25
    confidence_score: int = 0               # 0-20
    contactability_score: int = 0           # 0-20
    # icp_score already exists, keep it (new max = 35)

    # ── Hard gates ────────────────────────────────────────────────────────────
    hard_gate_status: bool = False
    hard_gate_reason: str = ""

    # ── Penalties ledger ──────────────────────────────────────────────────────
    penalties: List[dict] = field(default_factory=list)   # list of {name, points}

    # ── Signal quality ────────────────────────────────────────────────────────
    signal_strength: str = ""               # high / medium / low
    signal_confidence: str = ""             # high / medium / low
    signal_safe_to_mention: bool = True
    why_now: str = ""

    # ── Negative evidence ────────────────────────────────────────────────────
    negative_evidence: List[dict] = field(default_factory=list)
    false_positive_reason: str = ""

    # ── Entity resolution (extended) ─────────────────────────────────────────
    entity_type: str = ""                   # employer / facility / parent / district / franchise / government
    parent_company: str = ""
    parent_domain: str = ""
    facility_or_subsidiary: str = ""
    identity_confidence: str = ""           # high / medium / low

    # ── HRIS classification ───────────────────────────────────────────────────
    hris_fit_category: str = ""             # integration_fit / workflow_extension_fit / possible_displacement / exact_workflow_already_solved / unknown

    # ── Audit ────────────────────────────────────────────────────────────────
    audit_status: str = ""                  # pass / pass_with_warning / return_to_research / downgrade / reject
    audit_score: int = 0
    audit_flags: List[str] = field(default_factory=list)

    # ── Research ─────────────────────────────────────────────────────────────
    next_research_action: str = ""
    recheck_date: str = ""


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
    "intent_score",
    "confidence_score",
    "contactability_score",
    "hard_gate_status",
    "hard_gate_reason",
    "signal_strength",
    "signal_confidence",
    "signal_safe_to_mention",
    "why_now",
    "false_positive_reason",
    "entity_type",
    "parent_company",
    "parent_domain",
    "hris_fit_category",
    "audit_status",
    "audit_score",
    "next_research_action",
    "recheck_date",
]
