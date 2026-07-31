"""
ICP (Ideal Customer Profile) scoring engine.
Scores each account 0-100 across 4 dimensions:
  - Firmographic fit     (0-30)
  - Technographic fit    (0-25)
  - Behavioral/intent    (0-25)
  - Buying trigger       (0-20)
"""
from dataclasses import dataclass
from typing import List


@dataclass
class ICPScore:
    firmographic: int = 0       # 0-30
    technographic: int = 0      # 0-25
    behavioral: int = 0         # 0-25
    buying_trigger: int = 0     # 0-20
    total: int = 0
    grade: str = ""             # A/B/C/D
    notes: List[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []
        if not self.total:
            self.total = self.firmographic + self.technographic + self.behavioral + self.buying_trigger
        if not self.grade:
            self.grade = self._grade()

    def _grade(self) -> str:
        if self.total >= 80:
            return "A"
        if self.total >= 65:
            return "B"
        if self.total >= 50:
            return "C"
        return "D"


# ── ICP profiles per vertical ─────────────────────────────────────────────────
# These define the ideal structural characteristics for each vertical.
# Weights reflect how predictive each dimension is for that vertical.

ICP_PROFILES = {
    "healthcare": {
        "ideal_employee_ranges": ["100-500", "500-2000", "2000-10000"],
        "ideal_industries": ["Home Health", "Hospice", "Skilled Nursing", "Assisted Living",
                             "Behavioral Health", "FQHC", "Home Care", "Senior Living",
                             "Health System", "Multi-Site Care"],
        "high_fit_signals": ["pdf_new_hire_packet", "caregiver_hiring_surge",
                             "cms_deficiency", "credential_complexity", "adp_confirmed"],
        "disqualifying_signals": ["successfactors", "ceridian", "infor"],
        "description": "Multi-site care provider with frontline caregiver workforce",
        "enterprise_signals": ["large health system", "regional health", "national provider",
                               "hundreds of locations", "thousands of caregivers"],
    },
    "education": {
        "ideal_employee_ranges": ["200-1000", "1000-5000", "5000-20000"],
        "ideal_industries": ["K-12 School District", "Charter School Network",
                             "Private School", "Head Start", "Community College",
                             "University", "Higher Education", "State University System"],
        "high_fit_signals": ["pdf_new_hire_packet", "seasonal_hiring", "rfp_hris",
                             "adp_confirmed", "credential_complexity"],
        "disqualifying_signals": ["frontline education", "powerschool hris"],
        "description": "District, network, or institution with seasonal hiring surge and paper onboarding",
        "enterprise_signals": ["largest district", "multi-campus", "state university",
                               "community college system", "charter management organization"],
    },
    "manufacturing": {
        "ideal_employee_ranges": ["200-1000", "1000-5000", "5000-50000"],
        "ideal_industries": ["Manufacturing", "Logistics", "Distribution", "Construction",
                             "Food & Beverage", "Automotive", "Aerospace", "Defense",
                             "Chemical", "Pharmaceutical Manufacturing"],
        "high_fit_signals": ["osha_citation", "adp_confirmed", "frontline_comm_gap",
                             "job_manual_task", "acquisition"],
        "disqualifying_signals": ["workday", "ukg", "kronos"],
        "description": "Plant-floor employer with large hourly workforce and OSHA compliance burden",
        "enterprise_signals": ["multiple plants", "global operations", "PE-backed",
                               "enterprise manufacturing", "thousands of hourly workers"],
    },
    "nonprofit": {
        "ideal_employee_ranges": ["100-500", "500-2000", "2000-10000"],
        "ideal_industries": ["Nonprofit", "Social Services", "Faith-Based", "Human Services",
                             "Community Action", "Healthcare Nonprofit", "Education Nonprofit",
                             "National Nonprofit", "United Way", "Red Cross"],
        "high_fit_signals": ["pdf_new_hire_packet", "grant_award", "new_hr_leader",
                             "adp_confirmed", "job_manual_task"],
        "disqualifying_signals": ["bamboohr", "rippling", "gusto"],
        "description": "Mid-to-large nonprofit with multi-program structure and compliance-heavy onboarding",
        "enterprise_signals": ["national chapter", "multi-state", "federal grants",
                               "thousands of volunteers and staff", "major foundation"],
    },
    "government": {
        "ideal_employee_ranges": ["100-1000", "1000-10000", "10000+"],
        "ideal_industries": ["County Government", "Municipality", "Special District",
                             "Transit Authority", "State Agency", "Federal Contractor",
                             "Public Works", "Port Authority"],
        "high_fit_signals": ["rfp_hris", "pdf_new_hire_packet", "sam_contract_award",
                             "adp_confirmed", "seasonal_hiring"],
        "disqualifying_signals": ["neogov", "tyler technologies"],
        "description": "Local/state government with procurement-driven buying and paper onboarding at scale",
        "enterprise_signals": ["large county", "major city", "state-level", "transit authority",
                               "port authority", "thousands of public employees"],
    },
    "utilities": {
        "ideal_employee_ranges": ["200-1000", "1000-5000", "5000-50000"],
        "ideal_industries": ["Electric Utility", "Gas Utility", "Water Utility",
                             "Public Works", "Energy Company", "Municipal Utility",
                             "Investor-Owned Utility", "Rural Electric Cooperative",
                             "Wastewater", "Telecommunications Infrastructure"],
        "high_fit_signals": ["osha_citation", "pdf_new_hire_packet", "adp_confirmed",
                             "credential_complexity", "seasonal_hiring", "acquisition"],
        "disqualifying_signals": ["workday", "successfactors"],
        "description": "Regulated utility with unionized field workforce, NERC compliance, and credential-heavy onboarding",
        "enterprise_signals": ["investor-owned utility", "regional utility", "thousands of field workers",
                               "multi-state service territory", "NERC reliability", "union contract"],
    },
}

# Employee range points — minimum 100, enterprise-inclusive
EMPLOYEE_RANGE_SCORES = {
    "1-25":       0,    # below floor
    "25-50":      0,    # below floor
    "50-100":     0,    # below floor
    "100-200":   15,    # acceptable entry
    "200-500":   22,    # good fit
    "500-1000":  30,    # sweet spot (max)
    "1000-2000": 28,    # strong fit
    "2000-5000": 22,    # enterprise — high value
    "5000-10000":16,    # large enterprise
    "10000+":    10,    # enterprise — complex but winnable
}

MULTI_LOCATION_BONUS = 8
FRONTLINE_WORKFORCE_BONUS = 6
US_BASED_BONUS = 4
ENTERPRISE_SCALE_BONUS = 5      # 1000+ employees across multiple locations


def score_firmographic(employee_range: str, industry: str, vertical: str,
                        is_multi_location: bool, is_frontline: bool,
                        country: str = "US", is_enterprise: bool = False) -> tuple[int, list]:
    """Score firmographic fit (0-30)."""
    notes = []
    score = 0

    # Employee range — hard floor at 100
    if employee_range in ("1-25", "25-50", "50-100"):
        notes.append(f"Employee range {employee_range}: below minimum floor (100)")
        return 0, notes

    emp_score = EMPLOYEE_RANGE_SCORES.get(employee_range, 12)
    score += emp_score
    notes.append(f"Employee range {employee_range}: +{emp_score}")

    # Industry match
    profile = ICP_PROFILES.get(vertical, {})
    ideal_industries = profile.get("ideal_industries", [])
    if any(ind.lower() in industry.lower() for ind in ideal_industries):
        score += 8
        notes.append("Industry: ideal vertical match +8")
    else:
        notes.append("Industry: partial match")

    # Multi-location
    if is_multi_location:
        score += MULTI_LOCATION_BONUS
        notes.append(f"Multi-location: +{MULTI_LOCATION_BONUS}")

    # Frontline workforce
    if is_frontline:
        score += FRONTLINE_WORKFORCE_BONUS
        notes.append(f"Frontline/hourly workforce: +{FRONTLINE_WORKFORCE_BONUS}")

    # Enterprise scale bonus
    if is_enterprise or employee_range in ("1000-2000", "2000-5000", "5000-10000", "10000+"):
        score += ENTERPRISE_SCALE_BONUS
        notes.append(f"Enterprise scale: +{ENTERPRISE_SCALE_BONUS}")

    # Country
    if country == "US":
        score += US_BASED_BONUS

    return min(30, score), notes


def score_technographic(adp_status: str, hris_incumbent: str,
                         has_paper_evidence: bool, vertical: str) -> tuple[int, list]:
    """Score technographic fit (0-25)."""
    notes = []
    score = 0

    # ADP status (primary displacement signal)
    if adp_status == "confirmed":
        score += 15
        notes.append("ADP confirmed: +15")
    elif adp_status == "strongly_likely":
        score += 10
        notes.append("ADP strongly likely: +10")

    # Paper/manual evidence
    if has_paper_evidence:
        score += 8
        notes.append("Paper onboarding evidence: +8")

    # No modern HRIS
    profile = ICP_PROFILES.get(vertical, {})
    disqualifiers = profile.get("disqualifying_signals", [])
    if hris_incumbent and any(d in hris_incumbent.lower() for d in disqualifiers):
        score = max(0, score - 15)
        notes.append(f"Modern HRIS found ({hris_incumbent}): -15")
    elif not hris_incumbent:
        score += 5
        notes.append("No HRIS detected: +5")

    return min(25, score), notes


def score_behavioral(signal_score: int, has_tier_ab: bool,
                      signal_count: int) -> tuple[int, list]:
    """Score behavioral/intent fit (0-25)."""
    notes = []
    # Signal score already computed by SignalAggregator (0-100)
    # Map to 0-25
    base = int(signal_score / 100 * 20)
    score = base

    if has_tier_ab:
        score += 5
        notes.append("Tier A/B evidence: +5")
    if signal_count >= 3:
        score = min(25, score + 3)
        notes.append("3+ signals: +3")
    notes.append(f"Signal quality score {signal_score}/100: +{base}")

    return min(25, score), notes


def score_buying_trigger(triggers: list[str]) -> tuple[int, list]:
    """Score buying trigger events (0-20)."""
    TRIGGER_SCORES = {
        "rfp_hris":         20,
        "new_hr_leader":    18,
        "acquisition":      16,
        "grant_award":      14,
        "osha_citation":    14,
        "cms_deficiency":   14,
        "dol_violation":    12,
        "sam_contract_award": 12,
        "facility_expansion": 10,
        "adp_switching":    15,
    }
    notes = []
    score = 0
    for trigger in triggers:
        pts = TRIGGER_SCORES.get(trigger, 0)
        if pts:
            score = max(score, pts)  # take highest single trigger
            notes.append(f"Trigger {trigger}: +{pts}")
    return min(20, score), notes


def compute_icp_score(
    employee_range: str,
    industry: str,
    vertical: str,
    is_multi_location: bool,
    is_frontline: bool,
    adp_status: str,
    hris_incumbent: str,
    has_paper_evidence: bool,
    signal_score: int,
    has_tier_ab: bool,
    signal_count: int,
    trigger_signal_types: list[str],
    country: str = "US",
) -> ICPScore:
    firm_score, firm_notes = score_firmographic(
        employee_range, industry, vertical, is_multi_location, is_frontline, country)
    tech_score, tech_notes = score_technographic(
        adp_status, hris_incumbent, has_paper_evidence, vertical)
    behav_score, behav_notes = score_behavioral(signal_score, has_tier_ab, signal_count)
    trigger_score, trigger_notes = score_buying_trigger(trigger_signal_types)

    total = firm_score + tech_score + behav_score + trigger_score
    all_notes = firm_notes + tech_notes + behav_notes + trigger_notes

    return ICPScore(
        firmographic=firm_score,
        technographic=tech_score,
        behavioral=behav_score,
        buying_trigger=trigger_score,
        total=total,
        notes=all_notes,
    )
