"""
Tests for analyze_outcomes.py — segment math and metric computation.
- compute_metrics() correctly calculates rates
- Baseline vs segment comparison correctly identifies outperformers
- Minimum sample enforcement (< 30 sends → no hypothesis)
- Segment with 2x meeting rate triggers hypothesis generation
- All-zero sends handled without division error
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


def get_analyze_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "analyze_outcomes",
        str(Path(__file__).parent.parent / ".claude" / "skills" /
            "improving-gtm-outbound" / "scripts" / "analyze_outcomes.py")
    )
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    return mod


def make_outcome_row(**kwargs) -> dict:
    defaults = {
        "outcome_id": "abc123",
        "canonical_domain": "acme.com",
        "company_name": "Acme Corp",
        "outreach_date": "2026-07-01",
        "contact_title": "HR Director",
        "contact_persona_role": "champion",
        "sequence_name": "ABM Tier 1",
        "sequence_step": "1",
        "outcome": "no_response",
        "outcome_date": "",
        "days_to_outcome": "",
        "email_subject_used": "Your new hire packet",
        "account_tier_at_send": "Tier 1",
        "icp_score_at_send": "28",
        "intent_score_at_send": "18",
        "signal_type_at_send": "pdf_new_hire_packet",
        "vertical": "healthcare",
        "adp_status_at_send": "confirmed",
        "hris_fit_category_at_send": "integration_fit",
        "campaign_batch": "2026-07-01",
    }
    defaults.update(kwargs)
    return defaults


class TestComputeMetrics:
    def setup_method(self):
        self.mod = get_analyze_module()

    def test_empty_rows_return_zeros(self):
        m = self.mod.compute_metrics([])
        assert m["sends"] == 0
        assert m["reply_rate_pct"] == 0.0
        assert m["meeting_rate_pct"] == 0.0

    def test_all_no_response(self):
        rows = [make_outcome_row(outcome="no_response") for _ in range(10)]
        m = self.mod.compute_metrics(rows)
        assert m["sends"] == 10
        assert m["replies"] == 0
        assert m["meetings"] == 0
        assert m["reply_rate_pct"] == 0.0

    def test_reply_rate_calculation(self):
        rows = [make_outcome_row(outcome="reply") for _ in range(3)]
        rows += [make_outcome_row(outcome="no_response") for _ in range(7)]
        m = self.mod.compute_metrics(rows)
        assert m["sends"] == 10
        assert m["replies"] == 3
        assert m["reply_rate_pct"] == 30.0

    def test_meeting_rate_calculation(self):
        rows = [make_outcome_row(outcome="meeting_booked") for _ in range(5)]
        rows += [make_outcome_row(outcome="no_response") for _ in range(95)]
        m = self.mod.compute_metrics(rows)
        assert m["sends"] == 100
        assert m["meetings"] == 5
        assert m["meeting_rate_pct"] == 5.0

    def test_mixed_outcomes(self):
        rows = [
            make_outcome_row(outcome="meeting_booked"),
            make_outcome_row(outcome="reply"),
            make_outcome_row(outcome="bounced"),
            make_outcome_row(outcome="no_response"),
            make_outcome_row(outcome="no_response"),
        ]
        m = self.mod.compute_metrics(rows)
        assert m["sends"] == 5
        assert m["meetings"] == 1
        assert m["replies"] == 1
        assert m["bounced"] == 1
        assert m["positive_outcome_rate_pct"] == 40.0

    def test_min_sample_flag(self):
        rows_29 = [make_outcome_row() for _ in range(29)]
        rows_30 = [make_outcome_row() for _ in range(30)]
        assert self.mod.compute_metrics(rows_29)["min_sample_met"] is False
        assert self.mod.compute_metrics(rows_30)["min_sample_met"] is True


class TestHypothesisGeneration:
    def setup_method(self):
        self.mod = get_analyze_module()

    def _make_segment_rows(self, n: int, outcome: str = "no_response") -> list:
        return [make_outcome_row(outcome=outcome) for _ in range(n)]

    def test_below_minimum_sample_produces_no_hypothesis(self):
        # 29 sends is below minimum of 30
        rows_29 = self._make_segment_rows(29, "meeting_booked")
        baseline = self.mod.compute_metrics(self._make_segment_rows(100, "no_response"))

        segments = {("vertical", "healthcare"): rows_29}
        hypotheses = self.mod.generate_hypotheses(segments, baseline)
        # No hypothesis because min_sample not met
        assert len(hypotheses) == 0

    def test_outperforming_segment_generates_hypothesis(self):
        # Baseline: 2% meeting rate
        baseline_rows = [make_outcome_row(outcome="meeting_booked") for _ in range(2)]
        baseline_rows += [make_outcome_row(outcome="no_response") for _ in range(98)]
        baseline = self.mod.compute_metrics(baseline_rows)

        # Segment: 10% meeting rate (5x baseline) with 40 sends
        # Key format must match segment_rows() output — label marker + value
        seg_rows = [make_outcome_row(outcome="meeting_booked",
                                     signal_type_at_send="rfp_hris",
                                     vertical="healthcare") for _ in range(4)]
        seg_rows += [make_outcome_row(outcome="no_response",
                                      signal_type_at_send="rfp_hris",
                                      vertical="healthcare") for _ in range(36)]

        # Use the tuple format that segment_rows() produces for vertical+signal segments
        seg_key = ("vertical=healthcare", "signal", "rfp_hris")
        segments = {seg_key: seg_rows}

        # Verify _key_to_dict correctly extracts signal from this key format
        key_dict = self.mod._key_to_dict(seg_key)
        assert key_dict.get("signal") == "rfp_hris", (
            f"_key_to_dict should extract 'signal=rfp_hris', got {key_dict}"
        )

        hypotheses = self.mod.generate_hypotheses(segments, baseline)
        assert len(hypotheses) >= 1

    def test_zero_baseline_does_not_crash(self):
        baseline = {"meeting_rate_pct": 0.0, "reply_rate_pct": 0.0, "sends": 0}
        seg_rows = [make_outcome_row(outcome="meeting_booked") for _ in range(30)]
        segments = {("vertical", "healthcare"): seg_rows}
        # Should not raise ZeroDivisionError
        try:
            hypotheses = self.mod.generate_hypotheses(segments, baseline)
        except ZeroDivisionError:
            pytest.fail("generate_hypotheses raised ZeroDivisionError with zero baseline")


class TestNextVersion:
    def setup_method(self):
        self.mod = get_analyze_module()

    def test_returns_padded_string(self):
        tmp_dir = Path(tempfile.mkdtemp())
        v = self.mod.next_version(proposals_dir=tmp_dir)
        assert v == "001"
        assert len(v) == 3

    def test_increments_from_existing(self):
        tmp_dir = Path(tempfile.mkdtemp())
        (tmp_dir / "v003_some_proposal.yaml").write_text("")
        (tmp_dir / "v001_other.yaml").write_text("")
        v = self.mod.next_version(proposals_dir=tmp_dir)
        assert v == "004"
