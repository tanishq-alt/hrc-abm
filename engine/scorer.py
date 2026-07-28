"""
Account qualification scorer.

Provides two interfaces:
1. QualificationResult.qualify() — new 4-dimensional model with hard gates and tier floors
2. CompositeScore.compute() — legacy interface (backward compat, calls qualify() internally)
"""
from dataclasses import dataclass, field
from typing import List, Optional


# ── HRIS fit categories ───────────────────────────────────────────────────────
HRIS_FIT = {
    "integration_fit":              0,   # ADP, Paylocity, Paycom — add-on opportunity
    "workflow_extension_fit":       0,   # Workday, UKG — layer on top
    "possible_displacement":       -5,   # BambooHR, Rippling, Gusto — harder, not impossible
    "exact_workflow_already_solved":-15, # ONLY with verified evidence it solves target workflow
    "unknown":                      0,
}

# ── Penalty catalogue ─────────────────────────────────────────────────────────
PENALTIES = {
    "only_tier_d_evidence":           -20,
    "parent_only_identity":            -5,
    "single_weak_source":             -10,
    "signal_aging":                    -5,
    "signal_stale":                   -15,
    "contradictory_evidence":         -10,
    "no_exact_excerpt":                -8,
    "no_champion":                    -10,
    "decentralized_franchise":         -8,
    "suspected_duplicate":            -15,
    "exact_workflow_solved_by_hris":  -15,  # replaces blanket modern_hris_confirmed
    "domain_unverified":              -20,
    "employee_count_too_low":         -25,
}

# ── Hard gates (override all scores) ─────────────────────────────────────────
HARD_GATES = [
    ("identity_unresolved",          "Company identity unresolved — cannot score"),
    ("no_employer_entity",           "No real employer entity found"),
    ("current_customer",             "Current HR Cloud customer — suppressed"),
    ("competitor",                   "Competitor — suppressed"),
    ("active_rfp_closed",            "RFP already awarded or closed"),
    ("only_stale_signals",           "All signals stale — reverify before outreach"),
    ("do_not_contact",               "Suppressed: do-not-contact"),
    ("below_employee_floor",         "Below minimum employee count"),
    ("no_relevant_workflow",         "No HR Cloud-relevant workflow identified"),
    ("facility_no_buyer",            "Facility-level only — cannot resolve buying authority"),
    ("central_signal_false",         "Central qualifying signal disproven"),
    ("outside_geography",            "Outside approved geography"),
]
HARD_GATE_KEYS = {g[0] for g in HARD_GATES}


@dataclass
class TierFloorCheck:
    dimension: str
    required: int
    actual: int
    passed: bool
    message: str = ""


@dataclass
class QualificationResult:
    icp_score: int = 0              # 0-35
    intent_score: int = 0           # 0-25
    confidence_score: int = 0       # 0-20
    contactability_score: int = 0   # 0-20
    total_score: int = 0            # 0-100
    penalties: List[dict] = field(default_factory=list)
    penalty_total: int = 0
    hard_gate_status: bool = False
    hard_gate_reason: str = ""
    tier: str = "Disqualified"
    tier_floor_checks: List[TierFloorCheck] = field(default_factory=list)
    missing_activation_requirement: str = ""
    next_research_action: str = ""
    recheck_date: str = ""
    qualification_explanation: str = ""
    is_qualified: bool = False
    rejection_reason: str = ""

    @classmethod
    def qualify(
        cls,
        # ICP dimensions (0-35)
        priority_vertical: bool = False,
        employee_range_score: int = 0,     # 0-7
        complexity_score: int = 0,          # multi-loc/frontline, 0-7
        hiring_volume_score: int = 0,       # 0-5
        geography_score: int = 3,           # 0-3
        product_workflow_score: int = 0,    # 0-5
        # Intent (0-25)
        signal_reveals_problem: int = 0,    # 0-8
        signal_is_current: int = 0,         # 0-5
        why_now_concrete: int = 0,          # 0-4
        multi_signal_bonus: int = 0,        # 0-4
        product_relevance: int = 0,         # 0-4
        # Confidence (0-20)
        source_authority: int = 0,          # 0-6
        entity_match_score: int = 0,        # 0-4
        date_verified: int = 0,             # 0-3
        excerpt_specificity: int = 0,       # 0-3
        contradiction_resolved: int = 0,    # 0-2
        source_independence: int = 0,       # 0-2
        # Contactability (0-20)
        champion_title_exists: int = 0,     # 0-6
        champion_contact_found: int = 0,    # 0-4
        econ_buyer_identifiable: int = 0,   # 0-3
        verified_channel_data: int = 0,     # 0-3
        centralized_ownership: int = 0,     # 0-2
        no_active_duplicate: int = 2,       # 0-2
        # Penalty flags
        only_tier_d: bool = False,
        parent_only_identity: bool = False,
        single_weak_source: bool = False,
        signal_aging: bool = False,
        signal_stale: bool = False,
        contradictory_evidence: bool = False,
        no_exact_excerpt: bool = False,
        no_champion_found: bool = False,
        decentralized_franchise: bool = False,
        suspected_duplicate: bool = False,
        domain_status: str = "verified",
        employee_count_confirmed_low: bool = False,
        hris_fit_category: str = "unknown",
        # Hard gate flags (set the key name to True to trigger)
        hard_gates_triggered: List[str] = None,
    ) -> "QualificationResult":
        result = cls()

        # ── Hard gates first ──────────────────────────────────────────────────
        if hard_gates_triggered:
            for gate_key in hard_gates_triggered:
                if gate_key in HARD_GATE_KEYS:
                    result.hard_gate_status = True
                    result.hard_gate_reason = next(
                        g[1] for g in HARD_GATES if g[0] == gate_key
                    )
                    result.tier = "Disqualified"
                    result.rejection_reason = result.hard_gate_reason
                    result.is_qualified = False
                    return result

        if employee_count_confirmed_low:
            result.hard_gate_status = True
            result.hard_gate_reason = "Below minimum employee count"
            result.tier = "Disqualified"
            result.rejection_reason = result.hard_gate_reason
            result.is_qualified = False
            return result

        # ── Raw dimension scores ──────────────────────────────────────────────
        vertical_pts = 8 if priority_vertical else 3
        icp = min(35, vertical_pts + employee_range_score + complexity_score
                  + hiring_volume_score + geography_score + product_workflow_score)

        intent = min(25, signal_reveals_problem + signal_is_current + why_now_concrete
                     + multi_signal_bonus + product_relevance)

        confidence = min(20, source_authority + entity_match_score + date_verified
                         + excerpt_specificity + contradiction_resolved + source_independence)

        contact = min(20, champion_title_exists + champion_contact_found
                      + econ_buyer_identifiable + verified_channel_data
                      + centralized_ownership + no_active_duplicate)

        raw_total = icp + intent + confidence + contact

        # ── Penalties ─────────────────────────────────────────────────────────
        penalty_list = []
        penalty_total = 0

        def _apply(flag: bool, key: str):
            if flag:
                pts = abs(PENALTIES[key])
                penalty_list.append({"name": key, "points": -pts})
                return pts
            return 0

        penalty_total += _apply(only_tier_d, "only_tier_d_evidence")
        penalty_total += _apply(parent_only_identity, "parent_only_identity")
        penalty_total += _apply(single_weak_source, "single_weak_source")
        penalty_total += _apply(signal_aging, "signal_aging")
        penalty_total += _apply(signal_stale, "signal_stale")
        penalty_total += _apply(contradictory_evidence, "contradictory_evidence")
        penalty_total += _apply(no_exact_excerpt, "no_exact_excerpt")
        penalty_total += _apply(no_champion_found, "no_champion_found")
        penalty_total += _apply(decentralized_franchise, "decentralized_franchise")
        penalty_total += _apply(suspected_duplicate, "suspected_duplicate")
        penalty_total += _apply(domain_status != "verified", "domain_unverified")
        penalty_total += _apply(employee_count_confirmed_low, "employee_count_too_low")

        # HRIS penalty — only when workflow is demonstrably solved
        if hris_fit_category == "exact_workflow_already_solved":
            penalty_total += abs(PENALTIES["exact_workflow_solved_by_hris"])
            penalty_list.append({"name": "exact_workflow_solved_by_hris",
                                  "points": PENALTIES["exact_workflow_solved_by_hris"]})

        final = max(0, raw_total - penalty_total)

        result.icp_score = icp
        result.intent_score = intent
        result.confidence_score = confidence
        result.contactability_score = contact
        result.total_score = final
        result.penalties = penalty_list
        result.penalty_total = penalty_total

        # ── Tier floors ───────────────────────────────────────────────────────
        floors = []
        if final >= 80:
            # Tier 1 floor checks
            t1_checks = [
                TierFloorCheck("icp_score",            26, icp,        icp >= 26),
                TierFloorCheck("intent_score",         17, intent,     intent >= 17),
                TierFloorCheck("confidence_score",     14, confidence, confidence >= 14),
                TierFloorCheck("contactability_score", 12, contact,    contact >= 12),
                TierFloorCheck("champion_found",        1, champion_title_exists, champion_title_exists > 0),
            ]
            floors = t1_checks
            if all(c.passed for c in t1_checks):
                result.tier = "Tier 1"
            else:
                # Failed floor → drop to Tier 2
                failed = [c.dimension for c in t1_checks if not c.passed]
                result.tier = "Tier 2"
                result.missing_activation_requirement = f"Tier 1 floor failed: {', '.join(failed)}"
                result.next_research_action = f"Improve: {', '.join(failed)}"
        elif final >= 65:
            t2_checks = [
                TierFloorCheck("icp_score",        23, icp,        icp >= 23),
                TierFloorCheck("intent_score",     11, intent,     intent >= 11),
                TierFloorCheck("confidence_score", 11, confidence, confidence >= 11),
            ]
            floors = t2_checks
            if all(c.passed for c in t2_checks):
                result.tier = "Tier 2"
                result.next_research_action = "Find second confirming signal or verify champion"
            else:
                failed = [c.dimension for c in t2_checks if not c.passed]
                result.tier = "Tier 3"
                result.missing_activation_requirement = f"Tier 2 floor failed: {', '.join(failed)}"
        elif final >= 45:
            result.tier = "Tier 3"
            result.next_research_action = "Monitor. Recheck in 30 days."
        else:
            result.tier = "Disqualified"
            result.rejection_reason = "Total score below minimum (< 45)"

        result.tier_floor_checks = floors
        result.is_qualified = result.tier not in ("Disqualified",)
        return result


# ── Backward-compatible CompositeScore ───────────────────────────────────────
@dataclass
class CompositeScore:
    """Legacy interface — wraps QualificationResult for backward compat."""
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
        modern_hris_confirmed: bool,   # kept for compat — now maps to hris classification
    ) -> "CompositeScore":
        # Map old params to new qualifier
        hard_gates = []
        if employee_count_confirmed_low:
            hard_gates.append("below_employee_floor")

        # Convert ICP score (old 0-100) to new dimension approximations
        emp_score = min(7, int(icp_score / 30 * 7))
        complexity = min(7, int(icp_score / 30 * 5))
        product_match = min(5, int(icp_score / 30 * 4))

        # Map signal_score to intent dims
        sig_reveals = min(8, int(signal_score / 100 * 8)) if has_tier_ab else min(4, int(signal_score / 100 * 4))
        sig_current = min(5, int(signal_score / 100 * 5)) if not all_signals_stale else 0

        source_auth = 6 if has_tier_ab else 2
        entity_match = 3
        date_ver = 0 if all_signals_stale else 2
        excerpt_spec = 2

        champ_title = 6
        econ_id = 2
        no_dup = 2

        # HRIS fit — old boolean maps to possible_displacement if no evidence
        hris_cat = "possible_displacement" if modern_hris_confirmed else "unknown"

        result = QualificationResult.qualify(
            priority_vertical=icp_score >= 60,
            employee_range_score=emp_score,
            complexity_score=complexity,
            hiring_volume_score=0,
            geography_score=3,
            product_workflow_score=product_match,
            signal_reveals_problem=sig_reveals,
            signal_is_current=sig_current,
            why_now_concrete=0,
            multi_signal_bonus=min(4, signal_count - 1) if signal_count > 1 else 0,
            product_relevance=min(4, int(signal_score / 100 * 4)),
            source_authority=source_auth,
            entity_match_score=entity_match,
            date_verified=date_ver,
            excerpt_specificity=excerpt_spec,
            contradiction_resolved=2,
            source_independence=min(2, signal_count - 1) if signal_count > 1 else 0,
            champion_title_exists=champ_title,
            champion_contact_found=0,
            econ_buyer_identifiable=econ_id,
            verified_channel_data=0,
            centralized_ownership=2,
            no_active_duplicate=no_dup,
            only_tier_d=not has_tier_ab and signal_count <= 1,
            single_weak_source=signal_count <= 1,
            signal_stale=all_signals_stale,
            domain_status=domain_status,
            employee_count_confirmed_low=employee_count_confirmed_low,
            hris_fit_category=hris_cat,
            hard_gates_triggered=hard_gates,
        )

        raw = int(icp_score * 0.55 + signal_score * 0.45)
        return cls(
            icp_score=icp_score,
            signal_score=signal_score,
            raw_composite=raw,
            penalties_applied=[p["name"] for p in result.penalties],
            penalty_total=result.penalty_total,
            final_score=result.total_score,
            account_tier=result.tier,
            is_qualified=result.is_qualified,
            rejection_reason=result.rejection_reason,
        )
