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
        "ideal_employee_ranges": ["50-200", "200-500", "500-2000"],
        "ideal_industries": ["Home Health", "Hospice", "Skilled Nursing", "Assisted Living",
                             "Behavioral Health", "FQHC", "Home Care", "Senior Living"],
        "high_fit_signals": ["pdf_new_hire_packet", "caregiver_hiring_surge",
                             "cms_deficiency", "credential_complexity", "adp_confirmed"],
        "disqualifying_signals": ["workday", "successfactors", "ceridian", "infor"],
        "description": "Multi-site care provider with frontline caregiver workforce",
    },
    "education": {
        "ideal_employee_ranges": ["50-200", "200-500", "500-2000"],
        "ideal_industries": ["K-12 School District", "Charter School Network",
                             "Private School", "Head Start", "Community College"],
        "high_fit_signals": ["pdf_new_hire_packet", "seasonal_hiring", "rfp_hris",
                             "adp_confirmed", "credential_complexity"],
        "disqualifying_signals": ["frontline education", "powerschool hris"],
        "description": "District or network with seasonal hiring surge and paper onboarding",
    },
    "manufacturing": {
        "ideal_employee_ranges": ["100-500", "500-2000"],
        "ideal_industries": ["Manufacturing", "Logistics", "Distribution", "Construction"],
        "high_fit_signals": ["osha_citation", "adp_confirmed", "frontline_comm_gap",
                             "job_manual_task", "acquisition"],
        "disqualifying_signals": ["workday", "ukg", "kronos"],
        "description": "Plant-floor employer with hourly workforce and OSHA compliance burden",
    },
    "nonprofit": {
        "ideal_employee_ranges": ["50-200", "200-500"],
        "ideal_industries": ["Nonprofit", "Social Services", "Faith-Based", "Human Services"],
        "high_fit_signals": ["pdf_new_hire_packet", "grant_award", "new_hr_leader",
                             "adp_confirmed", "job_manual_task"],
        "disqualifying_signals": ["bamboohr", "rippling", "gusto"],
        "description": "Grant-funded org with lean HR team and paper-heavy onboarding",
    },
    "government": {
        "ideal_employee_ranges": ["50-500", "500-2000"],
        "ideal_industries": ["County Government", "Municipality", "Special District",
                             "Transit Authority", "Utilities"],
        "high_fit_signals": ["rfp_hris", "pdf_new_hire_packet", "sam_contract_award",
                             "adp_confirmed", "seasonal_hiring"],
        "disqualifying_signals": ["neogov", "tyler technologies"],
        "description": "Local/county government with procurement-driven buying and paper onboarding",
    },
}

# Employee range points
EMPLOYEE_RANGE_SCORES = {
    "1-25":      0,
    "25-50":     5,
    "50-100":    18,
    "100-200":   25,
    "200-500":   30,
    "500-1000":  25,
    "1000-2000": 20,
    "2000-5000": 12,
    "5000+":     5,
}

MULTI_LOCATION_BONUS = 8
FRONTLINE_WORKFORCE_BONUS = 6
US_BASED_BONUS = 4


def score_firmographic(employee_range: str, industry: str, vertical: str,
                        is_multi_location: bool, is_frontline: bool,
                        country: str = "US") -> tuple[int, list]:
    """Score firmographic fit (0-30)."""
    notes = []
    score = 0

    # Employee range
    emp_score = EMPLOYEE_RANGE_SCORES.get(employee_range, 10)
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
