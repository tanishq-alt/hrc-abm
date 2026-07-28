"""
Signal interpreter — pure interpretation layer.

Converts raw evidence into a structured hypothesis.
No scores, tiers, CRM writes, contact enrichment, or outreach.
"""
from dataclasses import dataclass, field
from typing import List, Optional


RELEVANT_WORKFLOWS = {
    "candidate_recruiting",
    "offer_onboarding_handoff",
    "new_hire_forms_tasks",
    "mobile_frontline_onboarding",
    "onboarding_guidance",
    "credentials_licenses",
    "training_renewals",
    "employee_records",
    "employee_communication",
    "time_shifts_performance",
    "payroll_hris_integration_gap",
}

SIGNAL_CATEGORIES = {
    "pdf_new_hire_packet":    ("workflow_pain",        "new_hire_forms_tasks"),
    "manual_onboarding":      ("workflow_pain",        "new_hire_forms_tasks"),
    "job_manual_task":        ("workflow_pain",        "new_hire_forms_tasks"),
    "adp_confirmed":          ("technology_change",    "payroll_hris_integration_gap"),
    "adp_switching":          ("competitive_dissatisfaction", "payroll_hris_integration_gap"),
    "rfp_hris":               ("procurement",          "new_hire_forms_tasks"),
    "sam_contract_award":     ("procurement",          "new_hire_forms_tasks"),
    "new_hr_leader":          ("leadership_change",    "new_hire_forms_tasks"),
    "acquisition":            ("growth",               "new_hire_forms_tasks"),
    "grant_award":            ("growth",               "new_hire_forms_tasks"),
    "facility_expansion":     ("growth",               "mobile_frontline_onboarding"),
    "osha_citation":          ("compliance_or_readiness", "training_renewals"),
    "cms_deficiency":         ("compliance_or_readiness", "credentials_licenses"),
    "caregiver_hiring_surge": ("growth",               "mobile_frontline_onboarding"),
    "seasonal_hiring":        ("growth",               "mobile_frontline_onboarding"),
    "frontline_comm_gap":     ("workflow_pain",        "employee_communication"),
    "credential_complexity":  ("compliance_or_readiness", "credentials_licenses"),
    "high_turnover":          ("workflow_pain",        "new_hire_forms_tasks"),
}

SAFE_TO_MENTION = {
    "pdf_new_hire_packet", "manual_onboarding", "job_manual_task",
    "rfp_hris", "sam_contract_award", "new_hr_leader", "acquisition",
    "grant_award", "facility_expansion", "osha_citation", "cms_deficiency",
    "caregiver_hiring_surge", "seasonal_hiring", "credential_complexity",
}

NOT_SAFE_TO_MENTION = {
    "website_visit", "ad_click", "profile_view", "email_open",
    "third_party_intent", "anonymous_community",
}

PRODUCT_MAP = {
    "pdf_new_hire_packet":    ("Onboard", "Maya"),
    "manual_onboarding":      ("Onboard", "Maya"),
    "job_manual_task":        ("Onboard", None),
    "adp_confirmed":          ("Onboard", "Workmates"),
    "rfp_hris":               ("Onboard", "People"),
    "osha_citation":          ("Train", "Onboard"),
    "cms_deficiency":         ("Credential Tracking", "Train"),
    "credential_complexity":  ("Credential Tracking", None),
    "caregiver_hiring_surge": ("Onboard", "Workmates"),
    "seasonal_hiring":        ("Onboard", None),
    "frontline_comm_gap":     ("Workmates", None),
    "high_turnover":          ("Onboard", "Workmates"),
    "facility_expansion":     ("Onboard", "Workmates"),
    "new_hr_leader":          ("Onboard", None),
    "acquisition":            ("Onboard", "People"),
    "grant_award":            ("Onboard", None),
}

# Not inherently negative — classify, don't penalize
MODERN_HRIS_PLATFORMS = {
    "workday": "workflow_extension_fit",
    "successfactors": "workflow_extension_fit",
    "ceridian": "workflow_extension_fit",
    "dayforce": "workflow_extension_fit",
    "ukg": "workflow_extension_fit",
    "kronos": "workflow_extension_fit",
    "infor": "workflow_extension_fit",
    "oracle hcm": "workflow_extension_fit",
    "adp workforce now": "integration_fit",
    "adp run": "integration_fit",
    "paylocity": "integration_fit",
    "paycom": "integration_fit",
    "paycor": "integration_fit",
    "bamboohr": "possible_displacement",
    "rippling": "possible_displacement",
    "gusto": "possible_displacement",
}

WHY_NOW_SIGNALS = {
    "rfp_hris", "new_hr_leader", "acquisition", "facility_expansion",
    "seasonal_hiring", "caregiver_hiring_surge", "grant_award", "cms_deficiency",
    "osha_citation",
}


@dataclass
class SignalInterpretation:
    relevance_verdict: str = "not_relevant"  # relevant / not_relevant / uncertain
    clean_summary: str = ""
    likely_meaning: str = ""
    business_implication: str = ""
    primary_product: str = ""
    secondary_product: str = ""
    signal_category: str = "noise"
    signal_strength: str = "low"            # high / medium / low
    signal_strength_reason: str = ""
    confidence: str = "low"                 # high / medium / low
    confidence_reason: str = ""
    freshness_status: str = "unknown"       # fresh / aging / stale / timeless_but_needs_reverification / unknown
    fresh_until: str = ""
    why_now: Optional[str] = None
    safe_to_mention: bool = True
    safe_to_mention_reason: str = ""
    what_not_to_assume: List[str] = field(default_factory=list)
    false_positive_risks: List[str] = field(default_factory=list)
    competitive_context: str = ""
    open_questions: List[str] = field(default_factory=list)
    hris_fit_category: str = "unknown"


def classify_hris(hris_name: str) -> str:
    """Classify detected HRIS — never a blanket disqualifier."""
    low = hris_name.lower()
    for platform, category in MODERN_HRIS_PLATFORMS.items():
        if platform in low:
            return category
    return "unknown"


def interpret_signal(
    signal_type: str,
    evidence_tier: str,
    evidence_excerpt: str,
    signal_date: str,
    freshness_score: int,        # 0-100 from signals.py
    hris_incumbent: str = "",
    adp_status: str = "not_found",
    vertical: str = "",
    signal_count: int = 1,
    has_contradiction: bool = False,
    entity_confirmed: bool = True,
) -> SignalInterpretation:
    """
    Pure interpretation. No scoring, tiering, CRM writes, or outreach.
    """
    interp = SignalInterpretation()

    # Relevance gate
    cat_info = SIGNAL_CATEGORIES.get(signal_type)
    if not cat_info:
        interp.relevance_verdict = "uncertain"
        interp.signal_category = "noise"
        return interp

    interp.relevance_verdict = "relevant"
    interp.signal_category = cat_info[0]

    # Product mapping
    prod = PRODUCT_MAP.get(signal_type, ("Onboard", None))
    interp.primary_product = prod[0]
    interp.secondary_product = prod[1] or ""

    # Signal strength
    if evidence_tier in ("A", "B") and freshness_score >= 65 and not has_contradiction:
        interp.signal_strength = "high"
        interp.signal_strength_reason = f"Tier {evidence_tier} source, fresh signal"
    elif evidence_tier in ("A", "B") and freshness_score >= 40:
        interp.signal_strength = "medium"
        interp.signal_strength_reason = f"Tier {evidence_tier} source, aging signal"
    elif evidence_tier == "C" and signal_count >= 2:
        interp.signal_strength = "medium"
        interp.signal_strength_reason = "Multiple Tier C sources"
    else:
        interp.signal_strength = "low"
        interp.signal_strength_reason = f"Tier {evidence_tier} source or insufficient corroboration"

    # Confidence
    if evidence_tier in ("A", "B") and entity_confirmed and not has_contradiction:
        interp.confidence = "high"
        interp.confidence_reason = f"Tier {evidence_tier} source with verified entity"
    elif evidence_tier in ("A", "B") and not entity_confirmed:
        interp.confidence = "medium"
        interp.confidence_reason = "Good source tier but entity not fully confirmed"
    elif has_contradiction:
        interp.confidence = "low"
        interp.confidence_reason = "Contradictory evidence found"
    elif evidence_tier == "C":
        interp.confidence = "low"
        interp.confidence_reason = "Tier C source — discovery only"
    else:
        interp.confidence = "medium"
        interp.confidence_reason = "Moderate source authority"

    # Freshness
    if freshness_score >= 85:
        interp.freshness_status = "fresh"
    elif freshness_score >= 65:
        interp.freshness_status = "aging"
    elif freshness_score >= 40:
        interp.freshness_status = "stale"
    elif signal_type in ("manual_onboarding", "pdf_new_hire_packet"):
        interp.freshness_status = "timeless_but_needs_reverification"
    else:
        interp.freshness_status = "stale"

    # Safe to mention
    if signal_type in NOT_SAFE_TO_MENTION:
        interp.safe_to_mention = False
        interp.safe_to_mention_reason = "Surveillance-type signal — background only"
    else:
        interp.safe_to_mention = True
        interp.safe_to_mention_reason = "Public or company-hosted source"

    # Why-now
    if signal_type in WHY_NOW_SIGNALS and freshness_score >= 65:
        WHY_NOW = {
            "rfp_hris": "Active procurement — evaluation window is open",
            "new_hr_leader": "New HR leader in first 90 days — prime evaluation window",
            "acquisition": "Post-acquisition HR standardization pressure",
            "facility_expansion": "New facility opening — onboarding volume spike",
            "seasonal_hiring": "Seasonal hiring window",
            "caregiver_hiring_surge": "Active caregiver hiring surge",
            "grant_award": "Fresh grant funding — budget available",
            "cms_deficiency": "Recent CMS deficiency — compliance pressure now",
            "osha_citation": "Recent OSHA citation — safety training urgency",
        }
        interp.why_now = WHY_NOW.get(signal_type)

    # HRIS classification (never disqualify, just classify)
    if hris_incumbent:
        interp.hris_fit_category = classify_hris(hris_incumbent)
        if interp.hris_fit_category == "exact_workflow_already_solved":
            interp.signal_strength = "low"
            interp.signal_strength_reason = "Current HRIS appears to solve the target workflow"
    elif adp_status == "confirmed":
        interp.hris_fit_category = "integration_fit"

    # What not to assume
    ASSUMPTIONS = {
        "adp_confirmed": "A job posting mentioning ADP does not prove production use",
        "pdf_new_hire_packet": "A paper packet may be optional rather than primary process",
        "new_hr_leader": "A new HR leader does not prove budget authority",
        "rfp_hris": "An RFP may have been amended or already awarded",
        "grant_award": "Generic funding does not prove HR technology priority",
        "cms_deficiency": "A deficiency citation does not prove the company will act quickly",
    }
    if signal_type in ASSUMPTIONS:
        interp.what_not_to_assume.append(ASSUMPTIONS[signal_type])

    # False positive risks
    if signal_type == "pdf_new_hire_packet":
        interp.false_positive_risks = [
            "Packet is an archive (outdated)",
            "Packet is for volunteers or contractors only",
            "Paper option exists but digital onboarding is primary",
            "Source belongs to a different entity",
        ]

    # Open questions (max 5)
    QUESTIONS = {
        "pdf_new_hire_packet": ["Is this packet still the current onboarding method?",
                                "Is HR centralized or facility-level?"],
        "adp_confirmed":       ["Does the company use ADP in production today?",
                                "Is there an active integration gap?"],
        "rfp_hris":            ["Is the RFP still open?", "Who is the procurement contact?"],
        "new_hr_leader":       ["Has the new leader indicated a technology mandate?"],
        "cms_deficiency":      ["Is the deficiency staffing-related?"],
    }
    interp.open_questions = QUESTIONS.get(signal_type, [])[:5]

    return interp
