"""
Tests for abm/apollo_export.py — Apollo export format.
- account_to_apollo_row() includes "Intent Score", "Confidence Score", "Audit Status" keys
- Safe-to-mention field present
- Export file has no duplicate headers
"""
import sys
import csv
import io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from abm.account import Account
from abm.apollo_export import account_to_apollo_row, APOLLO_FIELDS, export_to_apollo


def make_test_account(**kwargs) -> Account:
    """Create a minimal test Account with all required new fields."""
    defaults = dict(
        company_name="Acme Healthcare",
        canonical_domain="acmehealthcare.com",
        domain_status="verified",
        account_tier="Tier 2",
        composite_score=67,
        icp_score=52,
        primary_signal_type="pdf_new_hire_packet",
        primary_evidence_excerpt="Print and return packet on Day 1.",
        primary_evidence_url="https://acmehealthcare.com/hr/packet.pdf",
        champion_title="HR Director",
        best_hr_cloud_product="Onboard",
        # New fields
        intent_score=14,
        confidence_score=11,
        contactability_score=10,
        signal_strength="medium",
        signal_confidence="medium",
        signal_safe_to_mention=True,
        why_now="",
        hris_fit_category="integration_fit",
        entity_type="employer",
        parent_company="",
        negative_evidence=[],
        audit_status="pass",
        audit_score=88,
        next_research_action="Find second confirming signal",
    )
    defaults.update(kwargs)
    return Account(**defaults)


class TestApolloExportRow:
    def test_row_includes_intent_score(self):
        """account_to_apollo_row() includes 'Intent Score' key."""
        account = make_test_account(intent_score=14)
        row = account_to_apollo_row(account)
        assert "Intent Score" in row, f"'Intent Score' not found in row keys: {list(row.keys())}"
        assert row["Intent Score"] == 14

    def test_row_includes_confidence_score(self):
        """account_to_apollo_row() includes 'Confidence Score' key."""
        account = make_test_account(confidence_score=11)
        row = account_to_apollo_row(account)
        assert "Confidence Score" in row
        assert row["Confidence Score"] == 11

    def test_row_includes_audit_status(self):
        """account_to_apollo_row() includes 'Audit Status' key."""
        account = make_test_account(audit_status="pass_with_warning")
        row = account_to_apollo_row(account)
        assert "Audit Status" in row
        assert row["Audit Status"] == "pass_with_warning"

    def test_row_includes_safe_to_mention(self):
        """'Safe to Mention' field is present in the row."""
        account = make_test_account(signal_safe_to_mention=True)
        row = account_to_apollo_row(account)
        assert "Safe to Mention" in row, f"'Safe to Mention' not in row: {list(row.keys())}"
        assert row["Safe to Mention"] == "True"

    def test_safe_to_mention_false_serialized_correctly(self):
        """Safe to Mention=False is serialized as string 'False'."""
        account = make_test_account(signal_safe_to_mention=False)
        row = account_to_apollo_row(account)
        assert row["Safe to Mention"] == "False"

    def test_row_includes_contactability_score(self):
        """'Contactability Score' is in the row."""
        account = make_test_account(contactability_score=10)
        row = account_to_apollo_row(account)
        assert "Contactability Score" in row
        assert row["Contactability Score"] == 10

    def test_row_includes_signal_strength(self):
        """'Signal Strength' is in the row."""
        account = make_test_account(signal_strength="high")
        row = account_to_apollo_row(account)
        assert "Signal Strength" in row
        assert row["Signal Strength"] == "high"

    def test_row_includes_hris_fit_category(self):
        """'HRIS Fit Category' is in the row."""
        account = make_test_account(hris_fit_category="workflow_extension_fit")
        row = account_to_apollo_row(account)
        assert "HRIS Fit Category" in row
        assert row["HRIS Fit Category"] == "workflow_extension_fit"

    def test_row_includes_entity_type(self):
        """'Entity Type' is in the row."""
        account = make_test_account(entity_type="employer")
        row = account_to_apollo_row(account)
        assert "Entity Type" in row

    def test_row_includes_audit_score(self):
        """'Audit Score' is in the row."""
        account = make_test_account(audit_score=88)
        row = account_to_apollo_row(account)
        assert "Audit Score" in row
        assert row["Audit Score"] == 88

    def test_row_includes_next_research_action(self):
        """'Next Research Action' is in the row."""
        account = make_test_account(next_research_action="Find champion")
        row = account_to_apollo_row(account)
        assert "Next Research Action" in row
        assert row["Next Research Action"] == "Find champion"

    def test_row_includes_why_now(self):
        """'Why Now' is in the row."""
        account = make_test_account(why_now="New HR leader in first 90 days")
        row = account_to_apollo_row(account)
        assert "Why Now" in row
        assert row["Why Now"] == "New HR leader in first 90 days"

    def test_negative_evidence_serialized_to_string(self):
        """negative_evidence list is serialized as semicolon-joined string."""
        account = make_test_account(
            negative_evidence=[
                {"label": "Workday detected", "severity": "warning"},
                {"label": "Content may be archived", "severity": "warning"},
            ]
        )
        row = account_to_apollo_row(account)
        assert "Negative Evidence" in row
        assert "Workday detected" in row["Negative Evidence"]

    def test_empty_negative_evidence_is_empty_string(self):
        """Empty negative_evidence → empty string in row."""
        account = make_test_account(negative_evidence=[])
        row = account_to_apollo_row(account)
        assert row["Negative Evidence"] == ""


class TestApolloFieldsNoDuplicates:
    def test_apollo_fields_has_no_duplicate_headers(self):
        """APOLLO_FIELDS list has no duplicate entries."""
        seen = set()
        duplicates = []
        for field in APOLLO_FIELDS:
            if field in seen:
                duplicates.append(field)
            seen.add(field)
        assert duplicates == [], f"Duplicate fields found in APOLLO_FIELDS: {duplicates}"

    def test_apollo_fields_contains_new_required_fields(self):
        """APOLLO_FIELDS contains all new required fields."""
        required_new_fields = [
            "Intent Score",
            "Confidence Score",
            "Contactability Score",
            "Signal Strength",
            "Signal Confidence",
            "Safe to Mention",
            "Why Now",
            "HRIS Fit Category",
            "Entity Type",
            "Parent Company",
            "Negative Evidence",
            "Audit Status",
            "Audit Score",
            "Next Research Action",
        ]
        for field in required_new_fields:
            assert field in APOLLO_FIELDS, f"'{field}' not found in APOLLO_FIELDS"

    def test_row_keys_match_apollo_fields(self):
        """Row returned by account_to_apollo_row() has same keys as APOLLO_FIELDS."""
        account = make_test_account()
        row = account_to_apollo_row(account)
        for field in APOLLO_FIELDS:
            assert field in row, f"APOLLO_FIELDS entry '{field}' missing from row"
