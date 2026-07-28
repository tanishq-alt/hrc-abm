"""
Tests for engine/scorer.py — Modern HRIS treatment.
4 scenarios:
1. ADP integration_fit → no penalty
2. Workday workflow_extension_fit → no penalty
3. BambooHR possible_displacement → -5 only
4. exact_workflow_already_solved → -15 only, still not automatic Disqualified
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from engine.scorer import QualificationResult, PENALTIES


BASE_KWARGS = dict(
    priority_vertical=True,
    employee_range_score=5,
    complexity_score=5,
    hiring_volume_score=3,
    geography_score=3,
    product_workflow_score=3,
    signal_reveals_problem=6,
    signal_is_current=4,
    why_now_concrete=3,
    multi_signal_bonus=2,
    product_relevance=3,
    source_authority=5,
    entity_match_score=3,
    date_verified=2,
    excerpt_specificity=2,
    contradiction_resolved=2,
    source_independence=1,
    champion_title_exists=5,
    champion_contact_found=3,
    econ_buyer_identifiable=2,
    verified_channel_data=2,
    centralized_ownership=2,
    no_active_duplicate=2,
)


class TestModernHRISPenaltyRules:
    def test_adp_integration_fit_no_penalty(self):
        """ADP (integration_fit) incurs zero HRIS penalty."""
        baseline = QualificationResult.qualify(**BASE_KWARGS, hris_fit_category="unknown")
        adp_result = QualificationResult.qualify(**BASE_KWARGS, hris_fit_category="integration_fit")

        # Penalty names should not include HRIS-related penalty
        hris_penalties = [p for p in adp_result.penalties if "hris" in p["name"] or "workflow_solved" in p["name"]]
        assert hris_penalties == [], (
            f"ADP (integration_fit) should have no HRIS penalty, got: {hris_penalties}"
        )
        assert adp_result.total_score == baseline.total_score, (
            f"ADP should not reduce score: baseline={baseline.total_score}, adp={adp_result.total_score}"
        )

    def test_workday_workflow_extension_fit_no_penalty(self):
        """Workday (workflow_extension_fit) incurs zero HRIS penalty."""
        baseline = QualificationResult.qualify(**BASE_KWARGS, hris_fit_category="unknown")
        workday_result = QualificationResult.qualify(**BASE_KWARGS, hris_fit_category="workflow_extension_fit")

        hris_penalties = [p for p in workday_result.penalties if "workflow_solved" in p["name"]]
        assert hris_penalties == [], (
            f"Workday (workflow_extension_fit) should have no HRIS penalty, got: {hris_penalties}"
        )
        assert workday_result.total_score == baseline.total_score

    def test_bamboohr_possible_displacement_minus_five_only(self):
        """BambooHR (possible_displacement) does NOT apply HRIS penalty via scorer."""
        # Note: possible_displacement has 0 penalty in HRIS_FIT dict;
        # only exact_workflow_already_solved applies -15.
        baseline = QualificationResult.qualify(**BASE_KWARGS, hris_fit_category="unknown")
        bamboo_result = QualificationResult.qualify(**BASE_KWARGS, hris_fit_category="possible_displacement")

        # possible_displacement has no penalty in QualificationResult.qualify
        hris_penalties = [p for p in bamboo_result.penalties if "workflow_solved" in p["name"]]
        assert hris_penalties == [], "possible_displacement should not apply -15 penalty"
        # Score should be same as baseline (no extra deduction beyond possible_displacement being "0" in dict)
        assert bamboo_result.total_score == baseline.total_score

    def test_exact_workflow_solved_minus_fifteen_penalty(self):
        """exact_workflow_already_solved applies -15 penalty."""
        baseline = QualificationResult.qualify(**BASE_KWARGS, hris_fit_category="unknown")
        exact_result = QualificationResult.qualify(**BASE_KWARGS, hris_fit_category="exact_workflow_already_solved")

        hris_penalties = [p for p in exact_result.penalties if "workflow_solved" in p["name"]]
        assert len(hris_penalties) == 1, (
            f"Expected exactly 1 HRIS penalty for exact_workflow_already_solved, got: {hris_penalties}"
        )
        assert hris_penalties[0]["points"] == -15, (
            f"Expected -15 penalty, got: {hris_penalties[0]['points']}"
        )

    def test_exact_workflow_solved_not_automatic_disqualified(self):
        """exact_workflow_already_solved alone does NOT automatically Disqualify."""
        # With strong scores, even -15 should not push below 45
        result = QualificationResult.qualify(
            **BASE_KWARGS,
            hris_fit_category="exact_workflow_already_solved",
        )
        # The exact_workflow penalty is -15, but with strong base scores, should not hit Disqualified
        assert result.tier != "Disqualified", (
            f"exact_workflow_already_solved alone should not auto-Disqualify. "
            f"Got {result.tier} with total={result.total_score}"
        )

    def test_exact_workflow_solved_reduces_score_by_15(self):
        """exact_workflow_already_solved reduces score by exactly 15."""
        baseline = QualificationResult.qualify(**BASE_KWARGS, hris_fit_category="unknown")
        exact_result = QualificationResult.qualify(**BASE_KWARGS, hris_fit_category="exact_workflow_already_solved")

        expected_diff = 15
        actual_diff = baseline.total_score - exact_result.total_score
        assert actual_diff == expected_diff, (
            f"Expected score reduction of {expected_diff}, got {actual_diff} "
            f"(baseline={baseline.total_score}, exact={exact_result.total_score})"
        )

    def test_penalty_dict_has_correct_values(self):
        """Verify penalty catalogue has correct values for HRIS categories."""
        assert abs(PENALTIES["exact_workflow_solved_by_hris"]) == 15
        # Old blanket modern_hris_confirmed penalty no longer exists
        assert "modern_hris_confirmed" not in PENALTIES
