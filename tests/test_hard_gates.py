"""
Tests for engine/scorer.py — Hard gate behavior.
hard_gates_triggered=["below_employee_floor"] immediately returns Disqualified
regardless of all other scores being maxed.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from engine.scorer import QualificationResult


MAX_ICP_KWARGS = dict(
    priority_vertical=True,
    employee_range_score=7,
    complexity_score=7,
    hiring_volume_score=5,
    geography_score=3,
    product_workflow_score=5,
)

MAX_INTENT_KWARGS = dict(
    signal_reveals_problem=8,
    signal_is_current=5,
    why_now_concrete=4,
    multi_signal_bonus=4,
    product_relevance=4,
)

MAX_CONFIDENCE_KWARGS = dict(
    source_authority=6,
    entity_match_score=4,
    date_verified=3,
    excerpt_specificity=3,
    contradiction_resolved=2,
    source_independence=2,
)

MAX_CONTACT_KWARGS = dict(
    champion_title_exists=6,
    champion_contact_found=4,
    econ_buyer_identifiable=3,
    verified_channel_data=3,
    centralized_ownership=2,
    no_active_duplicate=2,
)

ALL_MAX = {**MAX_ICP_KWARGS, **MAX_INTENT_KWARGS, **MAX_CONFIDENCE_KWARGS, **MAX_CONTACT_KWARGS}


class TestHardGates:
    def test_below_employee_floor_disqualifies_regardless_of_score(self):
        """
        hard_gates_triggered=['below_employee_floor'] → Disqualified
        even when all dimension scores are maxed.
        """
        result = QualificationResult.qualify(
            **ALL_MAX,
            hard_gates_triggered=["below_employee_floor"],
        )
        assert result.tier == "Disqualified", (
            f"Expected Disqualified, got {result.tier}"
        )
        assert result.hard_gate_status is True
        assert result.is_qualified is False

    def test_below_employee_floor_via_param(self):
        """employee_count_confirmed_low=True is also a hard gate."""
        result = QualificationResult.qualify(
            **ALL_MAX,
            employee_count_confirmed_low=True,
        )
        assert result.tier == "Disqualified"
        assert result.hard_gate_status is True
        assert result.is_qualified is False

    def test_current_customer_gate(self):
        """current_customer gate → Disqualified."""
        result = QualificationResult.qualify(
            **ALL_MAX,
            hard_gates_triggered=["current_customer"],
        )
        assert result.tier == "Disqualified"
        assert result.hard_gate_status is True
        assert "customer" in result.hard_gate_reason.lower()

    def test_identity_unresolved_gate(self):
        """identity_unresolved gate → Disqualified."""
        result = QualificationResult.qualify(
            **ALL_MAX,
            hard_gates_triggered=["identity_unresolved"],
        )
        assert result.tier == "Disqualified"
        assert result.hard_gate_status is True

    def test_competitor_gate(self):
        """competitor gate → Disqualified."""
        result = QualificationResult.qualify(
            **ALL_MAX,
            hard_gates_triggered=["competitor"],
        )
        assert result.tier == "Disqualified"
        assert result.is_qualified is False

    def test_do_not_contact_gate(self):
        """do_not_contact gate → Disqualified."""
        result = QualificationResult.qualify(
            **ALL_MAX,
            hard_gates_triggered=["do_not_contact"],
        )
        assert result.tier == "Disqualified"
        assert result.hard_gate_status is True

    def test_first_gate_stops_evaluation(self):
        """First triggered gate stops evaluation — hard_gate_reason set to first gate."""
        result = QualificationResult.qualify(
            **ALL_MAX,
            hard_gates_triggered=["current_customer", "competitor"],
        )
        assert result.tier == "Disqualified"
        # Only first gate reason is captured
        assert result.hard_gate_reason != ""

    def test_no_hard_gate_allows_qualification(self):
        """No hard gates with max scores → qualified."""
        result = QualificationResult.qualify(**ALL_MAX)
        assert result.tier == "Tier 1"
        assert result.is_qualified is True
        assert result.hard_gate_status is False

    def test_empty_gate_list_is_ignored(self):
        """Empty hard_gates_triggered list is treated as no gates."""
        result = QualificationResult.qualify(
            **ALL_MAX,
            hard_gates_triggered=[],
        )
        assert result.tier == "Tier 1"

    def test_invalid_gate_key_is_ignored(self):
        """Unknown gate key that is not in HARD_GATE_KEYS is silently ignored."""
        result = QualificationResult.qualify(
            **ALL_MAX,
            hard_gates_triggered=["not_a_real_gate_key"],
        )
        # Should not crash, and not trigger a gate
        assert result.hard_gate_status is False
