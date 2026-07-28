"""
Tests for engine/interpreter.py — Signal freshness classification.
- 200-day-old signal → freshness_status "stale"
- 10-day-old signal → freshness_status "fresh"
- manual_onboarding with old date → "timeless_but_needs_reverification"
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from engine.interpreter import interpret_signal


class TestSignalFreshness:
    def test_200_day_old_signal_is_stale(self):
        """freshness_score < 40 → freshness_status 'stale' for non-timeless signals."""
        result = interpret_signal(
            signal_type="new_hr_leader",
            evidence_tier="C",
            evidence_excerpt="New HR Director hired 200 days ago.",
            signal_date="",
            freshness_score=20,  # Very low → stale
        )
        assert result.freshness_status == "stale", (
            f"Expected 'stale' for very old signal, got '{result.freshness_status}'"
        )

    def test_10_day_old_signal_is_fresh(self):
        """freshness_score >= 85 → freshness_status 'fresh'."""
        result = interpret_signal(
            signal_type="rfp_hris",
            evidence_tier="B",
            evidence_excerpt="Active RFP for HRIS posted this week.",
            signal_date="",
            freshness_score=90,  # High → fresh
        )
        assert result.freshness_status == "fresh", (
            f"Expected 'fresh' for recent signal, got '{result.freshness_status}'"
        )

    def test_manual_onboarding_old_date_timeless(self):
        """manual_onboarding with very low freshness_score → timeless_but_needs_reverification."""
        result = interpret_signal(
            signal_type="manual_onboarding",
            evidence_tier="C",
            evidence_excerpt="Please print and bring new hire packet on Day 1.",
            signal_date="",
            freshness_score=30,  # Low but timeless signal type
        )
        assert result.freshness_status == "timeless_but_needs_reverification", (
            f"Expected 'timeless_but_needs_reverification' for old manual_onboarding, "
            f"got '{result.freshness_status}'"
        )

    def test_pdf_new_hire_packet_old_is_timeless(self):
        """pdf_new_hire_packet with low freshness_score → timeless_but_needs_reverification."""
        result = interpret_signal(
            signal_type="pdf_new_hire_packet",
            evidence_tier="A",
            evidence_excerpt="New hire packet. Please complete all forms.",
            signal_date="",
            freshness_score=25,  # Low → timeless category
        )
        assert result.freshness_status == "timeless_but_needs_reverification", (
            f"Expected 'timeless_but_needs_reverification' for old pdf_new_hire_packet, "
            f"got '{result.freshness_status}'"
        )

    def test_aging_signal_in_65_to_84_range(self):
        """freshness_score 65-84 → 'aging'."""
        result = interpret_signal(
            signal_type="facility_expansion",
            evidence_tier="B",
            evidence_excerpt="New clinic opening announced.",
            signal_date="",
            freshness_score=70,  # Aging range
        )
        assert result.freshness_status == "aging", (
            f"Expected 'aging', got '{result.freshness_status}'"
        )

    def test_stale_hiring_signal_in_40_to_64_range(self):
        """freshness_score 40-64 → 'stale' for non-timeless signals."""
        result = interpret_signal(
            signal_type="caregiver_hiring_surge",
            evidence_tier="C",
            evidence_excerpt="Multiple caregiver positions open.",
            signal_date="",
            freshness_score=50,  # Stale range
        )
        assert result.freshness_status == "stale", (
            f"Expected 'stale', got '{result.freshness_status}'"
        )

    def test_why_now_returned_for_fresh_rfp(self):
        """Fresh RFP signal returns a why_now reason."""
        result = interpret_signal(
            signal_type="rfp_hris",
            evidence_tier="B",
            evidence_excerpt="HRIS RFP issued, deadline March 2026.",
            signal_date="",
            freshness_score=90,
        )
        assert result.why_now is not None, "Fresh RFP should have a why_now"
        assert len(result.why_now) > 0

    def test_why_now_not_returned_for_stale_signal(self):
        """Stale signal should NOT return a why_now (freshness_score < 65)."""
        result = interpret_signal(
            signal_type="rfp_hris",
            evidence_tier="C",
            evidence_excerpt="Old RFP from last year.",
            signal_date="",
            freshness_score=40,  # Below 65 threshold
        )
        assert result.why_now is None, (
            f"Stale signal should not have why_now, got: '{result.why_now}'"
        )
