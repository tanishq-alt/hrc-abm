"""
Composite account scorer.
Combines ICP score + signal aggregation score + penalties.
Outputs a final 0-100 composite score and account tier.
"""
from dataclasses import dataclass


PENALTIES = {
    "single_source_only":      -10,   # only one signal, from one source
    "no_tier_ab":              -15,   # no Tier A or B evidence at all
    "domain_unverified":       -20,   # domain_status != "verified"
    "signal_stale":            -8,    # all signals > 180 days old
    "employee_count_too_low":  -25,   # < 50 employees confirmed
    "modern_hris_confirmed":   -30,   # Workday / UKG / SAP already deployed
}


@dataclass
class CompositeScore:
    icp_score: int
    signal_score: int
    raw_composite: int
    penalties_applied: list
    penalty_total: int
    final_score: int
    account_tier: str
    is_qualified: bool
    rejection_reason: str = ""

    @classmethod
    def compute(
        cls,
        icp_score: int,
        signal_score: int,
        signal_count: int,
        has_tier_ab: bool,
        domain_status: str,
        all_signals_stale: bool,
        employee_count_confirmed_low: bool,
        modern_hris_confirmed: bool,
    ) -> "CompositeScore":
        # Weighted blend: ICP 55%, signals 45%
        raw = int(icp_score * 0.55 + signal_score * 0.45)

        penalties = []
        penalty_total = 0

        if signal_count <= 1:
            penalties.append("single_source_only")
            penalty_total += abs(PENALTIES["single_source_only"])
        if not has_tier_ab:
            penalties.append("no_tier_ab")
            penalty_total += abs(PENALTIES["no_tier_ab"])
        if domain_status != "verified":
            penalties.append("domain_unverified")
            penalty_total += abs(PENALTIES["domain_unverified"])
        if all_signals_stale:
            penalties.append("signal_stale")
            penalty_total += abs(PENALTIES["signal_stale"])
        if employee_count_confirmed_low:
            penalties.append("employee_count_too_low")
            penalty_total += abs(PENALTIES["employee_count_too_low"])
        if modern_hris_confirmed:
            penalties.append("modern_hris_confirmed")
            penalty_total += abs(PENALTIES["modern_hris_confirmed"])

        final = max(0, raw - penalty_total)

        # Tier classification
        if final >= 80:
            tier = "Tier 1"
        elif final >= 60:
            tier = "Tier 2"
        elif final >= 40:
            tier = "Tier 3"
        else:
            tier = "Disqualified"

        # Hard disqualification gates
        rejection = ""
        if employee_count_confirmed_low:
            tier = "Disqualified"
            rejection = "Confirmed < 50 employees"
        elif modern_hris_confirmed:
            tier = "Disqualified"
            rejection = "Modern HRIS already deployed"
        elif not has_tier_ab and signal_count <= 1:
            tier = "Disqualified"
            rejection = "Insufficient evidence: no Tier A/B and only 1 signal"

        is_qualified = tier != "Disqualified"

        return cls(
            icp_score=icp_score,
            signal_score=signal_score,
            raw_composite=raw,
            penalties_applied=penalties,
            penalty_total=penalty_total,
            final_score=final,
            account_tier=tier,
            is_qualified=is_qualified,
            rejection_reason=rejection,
        )
