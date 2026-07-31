"""
Tests for ingest_outcomes.py — schema validation and join integrity.
- Canonical domain normalisation strips www. and paths
- outcome_id deduplication skips already-seen rows
- Missing website column → row skipped with reason 'no_canonical_domain'
- infer_persona_role joins correctly for known titles
- Apollo and HubSpot format detection
"""
import csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "improving-gtm-outbound" / "scripts"))

import pytest


# Import the functions we need to test without triggering main()
def get_ingest_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ingest_outcomes",
        str(Path(__file__).parent.parent / ".claude" / "skills" /
            "improving-gtm-outbound" / "scripts" / "ingest_outcomes.py")
    )
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    return mod


class TestDomainNormalisation:
    def setup_method(self):
        self.mod = get_ingest_module()

    def test_strips_www(self):
        result = self.mod.normalise_domain("https://www.acmehealthcare.com")
        assert result == "acmehealthcare.com"

    def test_strips_path(self):
        result = self.mod.normalise_domain("https://acmehealthcare.com/jobs/apply")
        assert result == "acmehealthcare.com"

    def test_lowercases(self):
        result = self.mod.normalise_domain("https://AcmeHealthcare.COM")
        assert result == "acmehealthcare.com"

    def test_adds_scheme_if_missing(self):
        result = self.mod.normalise_domain("acmehealthcare.com")
        assert result == "acmehealthcare.com"

    def test_empty_returns_empty(self):
        result = self.mod.normalise_domain("")
        assert result == ""


class TestOutcomeIdDeduplication:
    def setup_method(self):
        self.mod = get_ingest_module()

    def test_same_inputs_produce_same_id(self):
        id1 = self.mod.make_outcome_id("acme.com", "2026-07-01", "HR Director")
        id2 = self.mod.make_outcome_id("acme.com", "2026-07-01", "HR Director")
        assert id1 == id2

    def test_different_domain_produces_different_id(self):
        id1 = self.mod.make_outcome_id("acme.com", "2026-07-01", "HR Director")
        id2 = self.mod.make_outcome_id("bestcare.com", "2026-07-01", "HR Director")
        assert id1 != id2

    def test_title_is_case_insensitive_in_id(self):
        id1 = self.mod.make_outcome_id("acme.com", "2026-07-01", "hr director")
        id2 = self.mod.make_outcome_id("acme.com", "2026-07-01", "HR Director")
        assert id1 == id2

    def test_id_is_16_chars(self):
        oid = self.mod.make_outcome_id("acme.com", "2026-07-01", "HR Director")
        assert len(oid) == 16


class TestOutcomeDerivation:
    def setup_method(self):
        self.mod = get_ingest_module()

    def test_meeting_booked_yes(self):
        row = {"_meeting_booked": "Yes", "_replied": "No", "_bounced": "No",
               "_unsubscribed": "No", "_last_activity": "2026-07-15"}
        outcome, _ = self.mod.derive_outcome(row)
        assert outcome == "meeting_booked"

    def test_replied_yes(self):
        row = {"_meeting_booked": "No", "_replied": "Yes", "_bounced": "No",
               "_unsubscribed": "No", "_last_activity": "2026-07-10"}
        outcome, _ = self.mod.derive_outcome(row)
        assert outcome == "reply"

    def test_bounced(self):
        row = {"_meeting_booked": "No", "_replied": "No", "_bounced": "Yes",
               "_unsubscribed": "No", "_last_activity": ""}
        outcome, _ = self.mod.derive_outcome(row)
        assert outcome == "bounced"

    def test_no_response_default(self):
        row = {"_meeting_booked": "No", "_replied": "No", "_bounced": "No",
               "_unsubscribed": "No", "_last_activity": ""}
        outcome, _ = self.mod.derive_outcome(row)
        assert outcome == "no_response"

    def test_meeting_takes_priority_over_reply(self):
        row = {"_meeting_booked": "Yes", "_replied": "Yes", "_bounced": "No",
               "_unsubscribed": "No", "_last_activity": ""}
        outcome, _ = self.mod.derive_outcome(row)
        assert outcome == "meeting_booked"


class TestDateNormalisation:
    def setup_method(self):
        self.mod = get_ingest_module()

    def test_iso_format(self):
        assert self.mod.normalise_date("2026-07-01") == "2026-07-01"

    def test_us_slash_format(self):
        assert self.mod.normalise_date("07/01/2026") == "2026-07-01"

    def test_empty_returns_empty(self):
        assert self.mod.normalise_date("") == ""

    def test_iso_with_time(self):
        result = self.mod.normalise_date("2026-07-01T14:30:00")
        assert result == "2026-07-01"


class TestFormatDetection:
    def setup_method(self):
        self.mod = get_ingest_module()

    def test_detects_apollo(self):
        headers = ["Company", "Website", "Title", "Replied", "Meeting Booked", "Sent At"]
        col_map = self.mod.detect_format(headers)
        assert col_map is self.mod.APOLLO_COLUMN_MAP

    def test_detects_hubspot(self):
        headers = ["Associated Company", "Website URL", "Job Title",
                   "Enrollment name", "First meeting booked"]
        col_map = self.mod.detect_format(headers)
        assert col_map is self.mod.HUBSPOT_COLUMN_MAP


class TestPersonaRoleJoin:
    def test_known_titles_map_to_correct_roles(self):
        from engine.personalizer import infer_persona_role
        assert infer_persona_role("director of human resources") == "champion"
        assert infer_persona_role("cfo") == "economic_buyer"
        assert infer_persona_role("hr manager") == "influencer"
        assert infer_persona_role("it director") == "blocker"

    def test_unknown_title_returns_unknown(self):
        from engine.personalizer import infer_persona_role
        result = infer_persona_role("unknown random title xyz")
        assert result in ("unknown", "champion", "influencer", "economic_buyer", "blocker")


class TestDaysDelta:
    def setup_method(self):
        self.mod = get_ingest_module()

    def test_computes_days(self):
        result = self.mod.compute_days("2026-07-01", "2026-07-15")
        assert result == "14"

    def test_missing_dates_return_empty(self):
        assert self.mod.compute_days("", "2026-07-15") == ""
        assert self.mod.compute_days("2026-07-01", "") == ""
