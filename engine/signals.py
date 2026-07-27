"""
Signal normalization and aggregation layer.
Every source (DDG, CMS, OSHA, job posts, PDFs) emits Signal objects.
The aggregator weights, deduplicates, and ranks them per account.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List


# Signal families → maps to ICP dimensions
FAMILY_MAP = {
    "manual_onboarding":      "process_evidence",
    "adp_confirmed":          "technographic",
    "adp_switching":          "technographic",
    "job_manual_task":        "process_evidence",
    "pdf_new_hire_packet":    "process_evidence",
    "osha_citation":          "regulatory_pressure",
    "cms_deficiency":         "regulatory_pressure",
    "dol_violation":          "regulatory_pressure",
    "sam_contract_award":     "intent_trigger",
    "grant_award":            "intent_trigger",
    "acquisition":            "intent_trigger",
    "new_hr_leader":          "intent_trigger",
    "facility_expansion":     "intent_trigger",
    "rfp_hris":               "intent_trigger",
    "caregiver_hiring_surge": "process_evidence",
    "seasonal_hiring":        "process_evidence",
    "frontline_comm_gap":     "process_evidence",
    "credential_complexity":  "process_evidence",
    "high_turnover":          "process_evidence",
    "lookalike_dna":          "firmographic",
}

TIER_WEIGHTS = {"A": 1.0, "B": 0.80, "C": 0.50, "D": 0.10}

# Max raw score per signal type
SIGNAL_BASE_SCORES = {
    "pdf_new_hire_packet":    35,
    "manual_onboarding":      30,
    "job_manual_task":        22,
    "adp_confirmed":          28,
    "adp_switching":          25,
    "osha_citation":          20,
    "cms_deficiency":         20,
    "dol_violation":          18,
    "rfp_hris":               30,
    "sam_contract_award":     18,
    "grant_award":            15,
    "acquisition":            20,
    "new_hr_leader":          18,
    "facility_expansion":     15,
    "caregiver_hiring_surge": 16,
    "seasonal_hiring":        14,
    "frontline_comm_gap":     16,
    "credential_complexity":  14,
    "high_turnover":          12,
    "lookalike_dna":          12,
}


@dataclass
class Signal:
    signal_type: str
    signal_family: str = ""
    tier: str = "C"
    source_url: str = ""
    source_domain: str = ""
    evidence_excerpt: str = ""      # max 50 words
    signal_date: str = ""           # ISO date string
    freshness_score: int = 70       # 0-100, decays weekly
    raw_score: int = 0              # before weighting
    weighted_score: float = 0.0     # raw * tier_weight * freshness_decay
    what_it_proves: str = ""
    what_it_does_not_prove: str = ""
    source_name: str = ""

    def __post_init__(self):
        if not self.signal_family:
            self.signal_family = FAMILY_MAP.get(self.signal_type, "general")
        if not self.raw_score:
            self.raw_score = SIGNAL_BASE_SCORES.get(self.signal_type, 10)
        self.freshness_score = self._compute_freshness()
        self.weighted_score = self._compute_weighted()

    def _compute_freshness(self) -> int:
        if not self.signal_date:
            return 50
        try:
            sig_date = datetime.fromisoformat(self.signal_date).date()
            days_old = (date.today() - sig_date).days
            if days_old <= 30:
                return 100
            if days_old <= 90:
                return 85
            if days_old <= 180:
                return 65
            if days_old <= 365:
                return 40
            return 15
        except Exception:
            return 50

    def _compute_weighted(self) -> float:
        tier_w = TIER_WEIGHTS.get(self.tier, 0.5)
        freshness_w = self.freshness_score / 100
        return self.raw_score * tier_w * freshness_w


class SignalAggregator:
    """Aggregate signals for a single account."""

    def __init__(self, signals: List[Signal]):
        self.signals = signals

    def deduplicated(self) -> List[Signal]:
        """One signal per (signal_type, source_domain) pair — keep highest weighted."""
        seen: dict[tuple, Signal] = {}
        for s in self.signals:
            key = (s.signal_type, s.source_domain)
            if key not in seen or s.weighted_score > seen[key].weighted_score:
                seen[key] = s
        return list(seen.values())

    def top_signals(self, n: int = 3) -> List[Signal]:
        deduped = self.deduplicated()
        return sorted(deduped, key=lambda s: -s.weighted_score)[:n]

    def signal_score(self) -> int:
        """Aggregate signal score (0-100) for this account."""
        top = self.top_signals(5)
        if not top:
            return 0
        total = sum(s.weighted_score for s in top)
        normalized = min(100, int(total / 175 * 100))
        families = {s.signal_family for s in top}
        if len(families) >= 3:
            normalized = min(100, normalized + 10)
        elif len(families) >= 2:
            normalized = min(100, normalized + 5)
        return normalized

    def has_tier_a_or_b(self) -> bool:
        return any(s.tier in ("A", "B") for s in self.deduplicated())

    def best_signal(self) -> Signal | None:
        top = self.top_signals(1)
        return top[0] if top else None

    def all_stale(self) -> bool:
        return all(s.freshness_score < 40 for s in self.deduplicated())
