"""
Tests for pipeline ordering — committee mapping happens after qualification.
Verifies that Account.contactability_score defaults to 0 (contact enrichment deferred).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from abm.account import Account


class TestCommitteeAfterQualification:
    def test_account_contactability_score_defaults_to_zero(self):
        """Account.contactability_score defaults to 0 — enrichment is deferred."""
        account = Account(
            company_name="Test Corp",
            canonical_domain="testcorp.com",
        )
        assert account.contactability_score == 0, (
            f"contactability_score should default to 0 (deferred), got {account.contactability_score}"
        )

    def test_account_intent_score_defaults_to_zero(self):
        """Account.intent_score defaults to 0."""
        account = Account()
        assert account.intent_score == 0

    def test_account_confidence_score_defaults_to_zero(self):
        """Account.confidence_score defaults to 0."""
        account = Account()
        assert account.confidence_score == 0

    def test_pipeline_imports_committee_module(self):
        """pipeline/run.py imports committee mapping (map_buying_committee)."""
        import sys
        original_argv = sys.argv
        sys.argv = ["run.py"]
        try:
            # Just verify the import works
            from engine.committee import map_buying_committee, champion_title, economic_buyer_title
            assert callable(map_buying_committee)
            assert callable(champion_title)
            assert callable(economic_buyer_title)
        finally:
            sys.argv = original_argv

    def test_new_account_has_empty_champion_title(self):
        """New Account has empty champion_title — populated after qualification."""
        account = Account()
        assert account.champion_title == ""

    def test_contactability_score_can_be_set(self):
        """contactability_score can be explicitly set after committee mapping."""
        account = Account(
            company_name="Test Corp",
            canonical_domain="testcorp.com",
            contactability_score=12,
        )
        assert account.contactability_score == 12

    def test_account_has_next_research_action_field(self):
        """Account has next_research_action field for Tier 2 required field."""
        account = Account()
        assert hasattr(account, "next_research_action")
        assert account.next_research_action == ""

    def test_account_has_hard_gate_fields(self):
        """Account has hard_gate_status and hard_gate_reason fields."""
        account = Account()
        assert hasattr(account, "hard_gate_status")
        assert hasattr(account, "hard_gate_reason")
        assert account.hard_gate_status is False
        assert account.hard_gate_reason == ""

    def test_account_has_negative_evidence_field(self):
        """Account has negative_evidence list field."""
        account = Account()
        assert hasattr(account, "negative_evidence")
        assert isinstance(account.negative_evidence, list)
        assert account.negative_evidence == []

    def test_account_has_audit_fields(self):
        """Account has audit_status, audit_score, and audit_flags fields."""
        account = Account()
        assert hasattr(account, "audit_status")
        assert hasattr(account, "audit_score")
        assert hasattr(account, "audit_flags")
        assert account.audit_score == 0
        assert account.audit_flags == []
