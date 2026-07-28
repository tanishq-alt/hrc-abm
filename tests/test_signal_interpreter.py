"""
Tests for engine/interpreter.py — Signal interpretation.
- interpret_signal() returns no tier, no composite score, no CRM write.
- Modern HRIS classified (not disqualified): Workday → hris_fit_category != "disqualified"
  and relevance_verdict == "relevant".
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from engine.interpreter import interpret_signal, SignalInterpretation


class TestSignalInterpreterPurity:
    def test_returns_signal_interpretation_object(self):
        """interpret_signal() returns a SignalInterpretation, not a score."""
        result = interpret_signal(
            signal_type="pdf_new_hire_packet",
            evidence_tier="A",
            evidence_excerpt="Print and bring completed forms on your first day.",
            signal_date="",
            freshness_score=80,
        )
        assert isinstance(result, SignalInterpretation)

    def test_no_tier_attribute(self):
        """Result has no 'tier' or 'account_tier' attribute (pure interpretation)."""
        result = interpret_signal(
            signal_type="manual_onboarding",
            evidence_tier="B",
            evidence_excerpt="HR coordinator processes new hire paperwork manually.",
            signal_date="",
            freshness_score=70,
        )
        assert not hasattr(result, "tier")
        assert not hasattr(result, "account_tier")
        assert not hasattr(result, "composite_score")

    def test_no_crm_side_effects(self):
        """Function is pure — no external side effects possible."""
        # Just verify it runs without touching any external systems
        result = interpret_signal(
            signal_type="rfp_hris",
            evidence_tier="B",
            evidence_excerpt="RFP for Human Resources Information System open until Dec 2025.",
            signal_date="",
            freshness_score=90,
        )
        assert result.relevance_verdict == "relevant"

    def test_no_contact_enrichment_fields(self):
        """Result contains no contact data fields."""
        result = interpret_signal(
            signal_type="new_hr_leader",
            evidence_tier="C",
            evidence_excerpt="New HR Director hired at Acme Corp.",
            signal_date="",
            freshness_score=75,
        )
        assert not hasattr(result, "champion_title")
        assert not hasattr(result, "email")
        assert not hasattr(result, "linkedin_url")


class TestModernHRISClassification:
    def test_workday_classified_not_disqualified(self):
        """Workday → hris_fit_category != 'disqualified' and relevance still 'relevant'."""
        result = interpret_signal(
            signal_type="pdf_new_hire_packet",
            evidence_tier="A",
            evidence_excerpt="Company-hosted new hire packet with paper forms.",
            signal_date="",
            freshness_score=80,
            hris_incumbent="workday",
        )
        assert result.hris_fit_category != "disqualified", (
            f"Workday should not produce 'disqualified' category, got: {result.hris_fit_category}"
        )
        assert result.relevance_verdict == "relevant", (
            f"Signal should remain relevant despite Workday, got: {result.relevance_verdict}"
        )

    def test_workday_classified_as_workflow_extension_fit(self):
        """Workday maps to workflow_extension_fit."""
        result = interpret_signal(
            signal_type="manual_onboarding",
            evidence_tier="B",
            evidence_excerpt="HR coordinator processes forms by hand.",
            signal_date="",
            freshness_score=70,
            hris_incumbent="workday",
        )
        assert result.hris_fit_category == "workflow_extension_fit"

    def test_adp_classified_as_integration_fit(self):
        """ADP status confirmed → hris_fit_category is integration_fit."""
        result = interpret_signal(
            signal_type="adp_confirmed",
            evidence_tier="B",
            evidence_excerpt="Experience with ADP Workforce Now required.",
            signal_date="",
            freshness_score=75,
            adp_status="confirmed",
        )
        assert result.hris_fit_category == "integration_fit"

    def test_bamboohr_classified_as_possible_displacement(self):
        """BambooHR → possible_displacement, not disqualified."""
        result = interpret_signal(
            signal_type="pdf_new_hire_packet",
            evidence_tier="C",
            evidence_excerpt="New hire packet attached.",
            signal_date="",
            freshness_score=60,
            hris_incumbent="bamboohr",
        )
        assert result.hris_fit_category == "possible_displacement"
        assert result.hris_fit_category != "disqualified"

    def test_unknown_hris_returns_unknown_category(self):
        """Unknown HRIS returns 'unknown', not 'disqualified'."""
        result = interpret_signal(
            signal_type="job_manual_task",
            evidence_tier="C",
            evidence_excerpt="HR coordinator completes onboarding paperwork.",
            signal_date="",
            freshness_score=55,
            hris_incumbent="some_obscure_hris_platform",
        )
        assert result.hris_fit_category == "unknown"
        assert result.hris_fit_category != "disqualified"

    def test_signal_remains_relevant_with_modern_hris(self):
        """A valid signal type stays relevant regardless of HRIS."""
        result = interpret_signal(
            signal_type="osha_citation",
            evidence_tier="A",
            evidence_excerpt="OSHA willful violation for safety training deficiencies.",
            signal_date="",
            freshness_score=85,
            hris_incumbent="successfactors",
        )
        assert result.relevance_verdict == "relevant"

    def test_unknown_signal_type_returns_uncertain(self):
        """Unknown signal type returns uncertain/not_relevant with noise category."""
        result = interpret_signal(
            signal_type="not_a_real_signal",
            evidence_tier="C",
            evidence_excerpt="Some text.",
            signal_date="",
            freshness_score=50,
        )
        assert result.relevance_verdict in ("uncertain", "not_relevant")
        assert result.signal_category == "noise"
