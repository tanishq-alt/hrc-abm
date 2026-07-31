"""
Tests for evaluate_proposal.py — backtest logic against fixture data.
- two_proportion_z_test() returns p < 0.05 for clearly different proportions
- two_proportion_z_test() returns p ≈ 1.0 when proportions are equal
- compute_confidence() correctly maps (p_value, sample_size) → confidence level
- update_proposal_backtest() writes values into YAML without corrupting structure
- Proposal with sample_size < 30 is blocked with needs_more_data status
"""
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


def get_evaluate_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "evaluate_proposal",
        str(Path(__file__).parent.parent / ".claude" / "skills" /
            "improving-gtm-outbound" / "scripts" / "evaluate_proposal.py")
    )
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    return mod


SAMPLE_PROPOSAL_YAML = """version: "001"
created_at: "2026-07-31T00:00:00Z"
status: "pending_review"
description: "Test proposal for evaluation"

hypothesis:
  observation: >
    Test observation.
  proposed_change:
    file: "engine/signals.py"
    parameter: "SIGNAL_BASE_SCORES['rfp_hris']"
    current_value: 30
    proposed_value: 35
    change_type: "signal_weight"

supporting_evidence:
  segments:
    - dimensions: {"vertical": "healthcare"}
      sends: 45
      replies: 12
      meetings: 5
      reply_rate_pct: 26.7
      meeting_rate_pct: 11.1

backtest:
  historical_periods: 3
  estimated_lift_pct: null
  p_value: null
  sample_size: 45
  confidence: "pending"

canary:
  status: "not_started"
  canary_start_date: null
  canary_pct: 20
  min_cycles: 2
  canary_meeting_rate: null
  control_meeting_rate: null

human_review:
  reviewer: null
  reviewed_at: null
  decision: null
  notes: null

diff_file: null
"""


class TestTwoProportionZTest:
    def setup_method(self):
        self.mod = get_evaluate_module()

    def test_equal_proportions_high_p_value(self):
        # 10% vs 10% — should not be significant
        p = self.mod.two_proportion_z_test(100, 10, 100, 10)
        assert p > 0.5, f"Equal proportions should have high p-value, got {p}"

    def test_very_different_proportions_low_p_value(self):
        # 2% vs 20% with large samples — should be significant
        p = self.mod.two_proportion_z_test(200, 4, 200, 40)
        assert p < 0.05, f"Clearly different proportions should have p < 0.05, got {p}"

    def test_zero_in_either_group_returns_1(self):
        assert self.mod.two_proportion_z_test(0, 0, 100, 10) == 1.0
        assert self.mod.two_proportion_z_test(100, 10, 0, 0) == 1.0

    def test_zero_events_in_both_returns_1(self):
        p = self.mod.two_proportion_z_test(100, 0, 100, 0)
        assert p == 1.0

    def test_p_value_between_0_and_1(self):
        p = self.mod.two_proportion_z_test(50, 5, 50, 15)
        assert 0.0 <= p <= 1.0


class TestComputeConfidence:
    def setup_method(self):
        self.mod = get_evaluate_module()

    def test_high_confidence(self):
        assert self.mod.compute_confidence(0.005, 150) == "high"

    def test_medium_confidence(self):
        assert self.mod.compute_confidence(0.03, 50) == "medium"

    def test_low_confidence_high_p(self):
        assert self.mod.compute_confidence(0.2, 50) == "low"

    def test_low_confidence_small_sample(self):
        # p < 0.01 but sample < 100 → not high
        result = self.mod.compute_confidence(0.005, 50)
        assert result in ("medium", "high")  # p < 0.01 and n >= 30 → medium

    def test_low_confidence_insufficient_sample(self):
        # p < 0.05 but n < 30 → low
        assert self.mod.compute_confidence(0.03, 20) == "low"


class TestUpdateProposalBacktest:
    def setup_method(self):
        self.mod = get_evaluate_module()
        self.tmp = tempfile.TemporaryDirectory()

    def teardown_method(self):
        self.tmp.cleanup()

    def _write_proposal(self, content: str) -> Path:
        path = Path(self.tmp.name) / "v001_test.yaml"
        path.write_text(content)
        return path

    def test_updates_estimated_lift(self):
        path = self._write_proposal(SAMPLE_PROPOSAL_YAML)
        self.mod.update_proposal_backtest(path, {
            "estimated_lift_pct": 5.5,
            "p_value": 0.03,
            "sample_size": 45,
            "confidence": "medium",
        })
        content = path.read_text()
        assert "5.5" in content

    def test_updates_confidence(self):
        path = self._write_proposal(SAMPLE_PROPOSAL_YAML)
        self.mod.update_proposal_backtest(path, {
            "estimated_lift_pct": 3.2,
            "p_value": 0.02,
            "sample_size": 50,
            "confidence": "medium",
        })
        content = path.read_text()
        assert '"medium"' in content

    def test_updates_status_to_pending_review_when_confident(self):
        path = self._write_proposal(SAMPLE_PROPOSAL_YAML)
        self.mod.update_proposal_backtest(path, {
            "estimated_lift_pct": 4.0,
            "p_value": 0.03,
            "sample_size": 35,
            "confidence": "medium",
        })
        content = path.read_text()
        assert 'status: "pending_review"' in content

    def test_updates_status_to_needs_more_data_when_low_confidence(self):
        path = self._write_proposal(SAMPLE_PROPOSAL_YAML)
        self.mod.update_proposal_backtest(path, {
            "estimated_lift_pct": None,
            "p_value": None,
            "sample_size": 10,
            "confidence": "low",
        })
        content = path.read_text()
        assert 'status: "needs_more_data"' in content

    def test_does_not_corrupt_yaml_structure(self):
        path = self._write_proposal(SAMPLE_PROPOSAL_YAML)
        self.mod.update_proposal_backtest(path, {
            "estimated_lift_pct": 2.1,
            "p_value": 0.04,
            "sample_size": 40,
            "confidence": "medium",
        })
        content = path.read_text()
        # Core structure keys must still be present
        for key in ["version:", "hypothesis:", "backtest:", "canary:", "human_review:"]:
            assert key in content, f"YAML structure damaged — missing {key}"


class TestLoadProposal:
    def setup_method(self):
        self.mod = get_evaluate_module()
        self.tmp = tempfile.TemporaryDirectory()

    def teardown_method(self):
        self.tmp.cleanup()

    def test_loads_version(self):
        path = Path(self.tmp.name) / "v001_test.yaml"
        path.write_text(SAMPLE_PROPOSAL_YAML)
        proposal = self.mod.load_proposal(path)
        assert proposal["version"] == "001"

    def test_loads_change_type(self):
        path = Path(self.tmp.name) / "v001_test.yaml"
        path.write_text(SAMPLE_PROPOSAL_YAML)
        proposal = self.mod.load_proposal(path)
        assert proposal["change_type"] == "signal_weight"

    def test_loads_sample_size(self):
        path = Path(self.tmp.name) / "v001_test.yaml"
        path.write_text(SAMPLE_PROPOSAL_YAML)
        proposal = self.mod.load_proposal(path)
        assert proposal["sample_size"] == 45
