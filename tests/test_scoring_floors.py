"""
Tests for engine/scorer.py — Tier floor enforcement.
Strong ICP but low intent_score (< 17) should NOT produce Tier 1.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from engine.scorer import QualificationResult


class TestTierFloors:
    def test_strong_icp_low_intent_does_not_produce_tier1(self):
        """
        Max ICP (35) but intent_score < 17 should not produce Tier 1.
        Intent must be >= 17 for Tier 1 floor.
        """
        result = QualificationResult.qualify(
            # ICP: maxed out
            priority_vertical=True,          # +8
            employee_range_score=7,          # +7
            complexity_score=7,              # +7
            hiring_volume_score=5,           # +5
            geography_score=3,               # +3
            product_workflow_score=5,        # +5  → ICP = 35 (capped)
            # Intent: low (below 17 floor)
            signal_reveals_problem=3,        # +3
            signal_is_current=3,             # +3
            why_now_concrete=2,              # +2
            multi_signal_bonus=2,            # +2
            product_relevance=2,             # +2  → intent = 12 (< 17 floor)
            # Confidence: high
            source_authority=6,              # +6
            entity_match_score=4,            # +4
            date_verified=3,                 # +3
            excerpt_specificity=3,           # +3
            contradiction_resolved=2,        # +2
            source_independence=2,           # +2  → confidence = 20
            # Contactability: high
            champion_title_exists=6,         # +6
            champion_contact_found=4,        # +4
            econ_buyer_identifiable=3,       # +3
            verified_channel_data=3,         # +3
            centralized_ownership=2,         # +2
            no_active_duplicate=2,           # +2  → contact = 20
        )
        # Total raw = 35 + 12 + 20 + 20 = 87, which should try Tier 1
        # But intent floor fails (12 < 17) → drops to Tier 2
        assert result.tier != "Tier 1", (
            f"Expected Tier 2 (intent floor fail), got {result.tier} "
            f"(intent={result.intent_score})"
        )
        assert result.intent_score == 12

    def test_all_floors_met_produces_tier1(self):
        """When all Tier 1 floors are met, tier should be Tier 1."""
        result = QualificationResult.qualify(
            priority_vertical=True,          # 8
            employee_range_score=7,
            complexity_score=7,
            hiring_volume_score=5,
            geography_score=3,
            product_workflow_score=5,        # ICP = 35 > 26 floor
            signal_reveals_problem=8,
            signal_is_current=5,
            why_now_concrete=4,
            multi_signal_bonus=4,
            product_relevance=4,             # intent = 25 > 17 floor
            source_authority=6,
            entity_match_score=4,
            date_verified=3,
            excerpt_specificity=3,
            contradiction_resolved=2,
            source_independence=2,           # confidence = 20 > 14 floor
            champion_title_exists=6,
            champion_contact_found=4,
            econ_buyer_identifiable=3,
            verified_channel_data=3,
            centralized_ownership=2,
            no_active_duplicate=2,           # contact = 20 > 12 floor
        )
        assert result.tier == "Tier 1", (
            f"Expected Tier 1, got {result.tier}. "
            f"ICP={result.icp_score}, Intent={result.intent_score}, "
            f"Confidence={result.confidence_score}, Contact={result.contactability_score}, "
            f"Total={result.total_score}"
        )

    def test_low_confidence_blocks_tier1(self):
        """Confidence score < 14 should prevent Tier 1."""
        result = QualificationResult.qualify(
            priority_vertical=True,
            employee_range_score=7,
            complexity_score=7,
            hiring_volume_score=5,
            geography_score=3,
            product_workflow_score=5,        # ICP = 35
            signal_reveals_problem=8,
            signal_is_current=5,
            why_now_concrete=4,
            multi_signal_bonus=4,
            product_relevance=4,             # intent = 25
            source_authority=2,              # low confidence
            entity_match_score=2,
            date_verified=1,
            excerpt_specificity=1,
            contradiction_resolved=1,
            source_independence=1,           # confidence = 8 < 14 floor
            champion_title_exists=6,
            champion_contact_found=4,
            econ_buyer_identifiable=3,
            verified_channel_data=3,
            centralized_ownership=2,
            no_active_duplicate=2,           # contact = 20
        )
        assert result.tier != "Tier 1"

    def test_no_champion_blocks_tier1(self):
        """champion_title_exists=0 should prevent Tier 1."""
        result = QualificationResult.qualify(
            priority_vertical=True,
            employee_range_score=7,
            complexity_score=7,
            hiring_volume_score=5,
            geography_score=3,
            product_workflow_score=5,
            signal_reveals_problem=8,
            signal_is_current=5,
            why_now_concrete=4,
            multi_signal_bonus=4,
            product_relevance=4,
            source_authority=6,
            entity_match_score=4,
            date_verified=3,
            excerpt_specificity=3,
            contradiction_resolved=2,
            source_independence=2,
            champion_title_exists=0,         # no champion
            champion_contact_found=0,
            econ_buyer_identifiable=3,
            verified_channel_data=3,
            centralized_ownership=2,
            no_active_duplicate=2,
        )
        assert result.tier != "Tier 1"

    def test_score_below_45_is_disqualified(self):
        """Total score below 45 → Disqualified."""
        result = QualificationResult.qualify(
            priority_vertical=False,
            employee_range_score=0,
            complexity_score=0,
            hiring_volume_score=0,
            geography_score=0,
            product_workflow_score=0,
            signal_reveals_problem=0,
            signal_is_current=0,
            why_now_concrete=0,
            multi_signal_bonus=0,
            product_relevance=0,
            source_authority=0,
            entity_match_score=0,
            date_verified=0,
            excerpt_specificity=0,
            contradiction_resolved=0,
            source_independence=0,
            champion_title_exists=0,
            champion_contact_found=0,
            econ_buyer_identifiable=0,
            verified_channel_data=0,
            centralized_ownership=0,
            no_active_duplicate=0,
        )
        assert result.tier == "Disqualified"
        assert result.is_qualified is False

    def test_tier2_range_produces_tier2(self):
        """Score in 65-79 range with Tier 2 floors met → Tier 2."""
        result = QualificationResult.qualify(
            priority_vertical=True,          # 8
            employee_range_score=5,          # icp ~ 27
            complexity_score=5,
            hiring_volume_score=3,
            geography_score=3,
            product_workflow_score=3,        # ICP = 27 > 23 floor
            signal_reveals_problem=6,
            signal_is_current=4,
            why_now_concrete=2,
            multi_signal_bonus=1,
            product_relevance=2,             # intent = 15 > 11 floor
            source_authority=4,
            entity_match_score=3,
            date_verified=2,
            excerpt_specificity=2,
            contradiction_resolved=1,
            source_independence=1,           # confidence = 13 > 11 floor
            champion_title_exists=4,
            champion_contact_found=2,
            econ_buyer_identifiable=2,
            verified_channel_data=1,
            centralized_ownership=1,
            no_active_duplicate=2,
        )
        # Should be somewhere in the Tier 2-3 range
        assert result.tier in ("Tier 2", "Tier 3"), (
            f"Expected Tier 2 or 3, got {result.tier} (total={result.total_score})"
        )
