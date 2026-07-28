"""
Tests for engine/auditor.py — Lead quality auditor.
- Tier 1 account with no champion_title → audit_status "reject" or "return_to_research"
- Account with no evidence URL → fatal error
- Account with all stale evidence → fatal error
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from engine.auditor import audit_account, audit_accounts, AuditResult


def make_good_account(**overrides) -> dict:
    """Minimal valid account dict."""
    base = {
        "company_name": "Acme Healthcare",
        "canonical_domain": "acmehealthcare.com",
        "domain_status": "verified",
        "primary_evidence_url": "https://acmehealthcare.com/hr/new-hire-packet.pdf",
        "primary_evidence_excerpt": "Please print and return this new hire packet on Day 1.",
        "primary_signal_tier": "A",
        "account_tier": "Tier 2",
        "composite_score": 67,
        "champion_title": "HR Director",
        "best_hr_cloud_product": "Onboard",
    }
    base.update(overrides)
    return base


class TestAuditorFatalChecks:
    def test_tier1_no_champion_title_fails_audit(self):
        """Tier 1 account with no champion_title → audit_status is reject or return_to_research."""
        account = make_good_account(
            account_tier="Tier 1",
            composite_score=82,
            champion_title="",          # No champion!
        )
        result = audit_account(account)
        assert result.audit_status in ("reject", "return_to_research"), (
            f"Expected 'reject' or 'return_to_research' for Tier 1 without champion, "
            f"got '{result.audit_status}'"
        )
        assert result.persona_pass is False

    def test_no_evidence_url_produces_fatal_error(self):
        """Account with no evidence URL → fatal error in result."""
        account = make_good_account(primary_evidence_url="")
        result = audit_account(account)
        assert len(result.fatal_errors) > 0, "Expected at least one fatal error for missing evidence URL"
        assert result.traceability_pass is False

    def test_all_stale_evidence_produces_fatal_error(self):
        """Account with all stale evidence → fatal error."""
        account = make_good_account()
        # All evidence marked as not fresh
        stale_evidence = [
            {"evidence_id": "abc123", "tier": "C", "claim": "manual_onboarding",
             "source_url": "https://acmehealthcare.com/old-packet.pdf",
             "excerpt": "Old new hire packet.", "fresh": False, "syndicated": False, "limitations": ""},
        ]
        result = audit_account(account, stale_evidence)
        assert result.freshness_pass is False, "All stale evidence should fail freshness check"
        assert len(result.fatal_errors) > 0

    def test_no_evidence_excerpt_produces_fatal_error(self):
        """Account with no evidence excerpt → fatal error."""
        account = make_good_account(primary_evidence_excerpt="")
        result = audit_account(account)
        assert result.traceability_pass is False
        assert len(result.fatal_errors) > 0

    def test_unresolved_domain_produces_fatal_error(self):
        """Account with domain_status='unresolved' → identity_pass fails."""
        account = make_good_account(domain_status="unresolved")
        result = audit_account(account)
        assert result.identity_pass is False
        assert len(result.fatal_errors) > 0

    def test_no_canonical_domain_fails_identity(self):
        """Account with no canonical_domain → identity_pass fails."""
        account = make_good_account(canonical_domain="")
        result = audit_account(account)
        assert result.identity_pass is False

    def test_tier1_with_tier_c_source_fails_confidence(self):
        """Tier 1 account with primary_signal_tier='C' → confidence_pass fails."""
        account = make_good_account(
            account_tier="Tier 1",
            composite_score=82,
            primary_signal_tier="C",
            champion_title="HR Director",
        )
        result = audit_account(account)
        assert result.confidence_pass is False
        assert len(result.fatal_errors) > 0

    def test_missing_company_name_fails_export_integrity(self):
        """Account with no company_name → export_integrity_pass fails."""
        account = make_good_account(company_name="")
        result = audit_account(account)
        assert result.export_integrity_pass is False

    def test_good_account_passes_audit(self):
        """Well-formed account with all required fields → audit passes."""
        account = make_good_account()
        result = audit_account(account)
        assert result.audit_status in ("pass", "pass_with_warning"), (
            f"Expected pass, got '{result.audit_status}'. Errors: {result.fatal_errors}"
        )

    def test_audit_score_starts_at_100(self):
        """AuditResult starts with audit_score of 100."""
        result = AuditResult()
        assert result.audit_score == 100

    def test_batch_audit_returns_dict_by_domain(self):
        """audit_accounts() returns dict keyed by canonical_domain."""
        accounts = [
            make_good_account(canonical_domain="a.com"),
            make_good_account(canonical_domain="b.com"),
        ]
        results = audit_accounts(accounts)
        assert "a.com" in results
        assert "b.com" in results
        assert isinstance(results["a.com"], AuditResult)

    def test_no_hr_cloud_product_produces_warning(self):
        """Account with no best_hr_cloud_product → warning (not fatal)."""
        account = make_good_account(best_hr_cloud_product="")
        result = audit_account(account)
        assert result.product_fit_pass is False
        # Should be a warning, not necessarily a fatal error
        assert len(result.warnings) > 0
