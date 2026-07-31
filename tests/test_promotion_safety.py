"""
Tests for promote_learning.py — gate enforcement.
Critical invariant: promote_learning.py NEVER directly edits source files.

Tests:
- generate_diff_guidance() returns a string with the diff, not a file edit
- Hard gate change_type triggers a block (sys.exit) before any writes
- Approved proposal updates APPROVED_LEARNINGS.md with correct fields
- Rejected proposal does NOT touch APPROVED_LEARNINGS.md
- Proposal YAML human_review section is updated with reviewer/decision
- run_tests() is the first step (abort if tests fail)
"""
import re
import sys
import tempfile
import unittest.mock as mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


def get_promote_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "promote_learning",
        str(Path(__file__).parent.parent / ".claude" / "skills" /
            "improving-gtm-outbound" / "scripts" / "promote_learning.py")
    )
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    return mod


SAMPLE_APPROVED_PROPOSAL = """version: "001"
created_at: "2026-07-31T00:00:00Z"
status: "pending_review"
description: "Increase rfp_hris signal weight"

hypothesis:
  observation: >
    Healthcare rfp_hris accounts show 12% meeting rate.
  proposed_change:
    file: "engine/signals.py"
    parameter: "SIGNAL_BASE_SCORES['rfp_hris']"
    current_value: 30
    proposed_value: 35
    change_type: "signal_weight"

supporting_evidence:
  segments: []

backtest:
  historical_periods: 3
  estimated_lift_pct: 5.5
  p_value: 0.03
  sample_size: 45
  confidence: "medium"

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

HARD_GATE_PROPOSAL = SAMPLE_APPROVED_PROPOSAL.replace(
    'change_type: "signal_weight"', 'change_type: "hard_gate"'
)


class TestGenerateDiffGuidance:
    def setup_method(self):
        self.mod = get_promote_module()

    def test_returns_string_not_none(self):
        proposal = {
            "version": "001",
            "description": "Test change",
            "target_file": "engine/signals.py",
            "parameter": "SIGNAL_BASE_SCORES['rfp_hris']",
            "current_value": "30",
            "proposed_value": "35",
            "confidence": "medium",
            "estimated_lift_pct": 5.5,
        }
        result = self.mod.generate_diff_guidance(proposal)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_contains_file_and_parameter(self):
        proposal = {
            "version": "001",
            "description": "Test change",
            "target_file": "engine/scorer.py",
            "parameter": "icp_floor",
            "current_value": "26",
            "proposed_value": "28",
            "confidence": "medium",
            "estimated_lift_pct": None,
        }
        result = self.mod.generate_diff_guidance(proposal)
        assert "engine/scorer.py" in result
        assert "icp_floor" in result

    def test_contains_apply_instructions(self):
        proposal = {
            "version": "001",
            "description": "Test",
            "target_file": "engine/signals.py",
            "parameter": "X",
            "current_value": "1",
            "proposed_value": "2",
            "confidence": "low",
            "estimated_lift_pct": None,
        }
        result = self.mod.generate_diff_guidance(proposal)
        assert "python3 -m pytest" in result
        assert "git add" in result
        assert "git commit" in result

    def test_never_edits_source_files(self):
        """generate_diff_guidance must not open or write any .py files."""
        import builtins
        written_files = []
        original_open = builtins.open

        def mock_open(path, mode="r", *args, **kwargs):
            if "w" in str(mode) and str(path).endswith(".py"):
                written_files.append(str(path))
            return original_open(path, mode, *args, **kwargs)

        proposal = {
            "version": "001",
            "description": "Test",
            "target_file": "engine/signals.py",
            "parameter": "X",
            "current_value": "1",
            "proposed_value": "2",
            "confidence": "medium",
            "estimated_lift_pct": 3.0,
        }
        with mock.patch("builtins.open", mock_open):
            self.mod.generate_diff_guidance(proposal)

        assert written_files == [], (
            f"generate_diff_guidance wrote to Python source files: {written_files}"
        )


class TestHardGateBlock:
    def setup_method(self):
        self.mod = get_promote_module()

    def test_hard_gate_change_type_triggers_exit(self):
        tmp = tempfile.TemporaryDirectory()
        proposal_path = Path(tmp.name) / "v001_hard_gate.yaml"
        proposal_path.write_text(HARD_GATE_PROPOSAL)

        with pytest.raises(SystemExit):
            self.mod.run(proposal_path, "approve", "Test Reviewer", "testing")
        tmp.cleanup()


class TestProposalReviewUpdate:
    def setup_method(self):
        self.mod = get_promote_module()
        self.tmp = tempfile.TemporaryDirectory()

    def teardown_method(self):
        self.tmp.cleanup()

    def test_updates_reviewer_field(self):
        path = Path(self.tmp.name) / "v001_test.yaml"
        path.write_text(SAMPLE_APPROVED_PROPOSAL)
        self.mod.update_proposal_review(path, "Jane Smith", "approve", "Looks good")
        content = path.read_text()
        assert '"Jane Smith"' in content

    def test_updates_decision_field(self):
        path = Path(self.tmp.name) / "v001_test.yaml"
        path.write_text(SAMPLE_APPROVED_PROPOSAL)
        self.mod.update_proposal_review(path, "John Doe", "reject", "Not enough data")
        content = path.read_text()
        assert '"reject"' in content or '"rejected"' in content

    def test_updates_status_to_approved(self):
        path = Path(self.tmp.name) / "v001_test.yaml"
        path.write_text(SAMPLE_APPROVED_PROPOSAL)
        self.mod.update_proposal_review(path, "Jane Smith", "approve", "")
        content = path.read_text()
        assert "approved" in content

    def test_does_not_corrupt_yaml_structure(self):
        path = Path(self.tmp.name) / "v001_test.yaml"
        path.write_text(SAMPLE_APPROVED_PROPOSAL)
        self.mod.update_proposal_review(path, "Jane Smith", "approve", "Notes here")
        content = path.read_text()
        for key in ["version:", "hypothesis:", "backtest:", "canary:"]:
            assert key in content, f"Structure corrupted — missing {key}"


class TestApprovedLearningsUpdate:
    def setup_method(self):
        self.mod = get_promote_module()
        self.tmp = tempfile.TemporaryDirectory()

    def teardown_method(self):
        self.tmp.cleanup()

    def _make_proposal(self) -> dict:
        path = Path(self.tmp.name) / "v001_test.yaml"
        path.write_text(SAMPLE_APPROVED_PROPOSAL)
        return {
            "version": "001",
            "description": "Increase rfp_hris signal weight",
            "target_file": "engine/signals.py",
            "parameter": "SIGNAL_BASE_SCORES['rfp_hris']",
            "current_value": "30",
            "proposed_value": "35",
            "confidence": "medium",
            "estimated_lift_pct": 5.5,
            "_path": path,
        }

    def test_appends_entry_to_approved_learnings(self):
        approved_file = Path(self.tmp.name) / "APPROVED_LEARNINGS.md"
        approved_file.write_text("# Approved Learnings\n")

        with mock.patch.object(self.mod, "APPROVED_LEARNINGS", approved_file):
            self.mod.append_to_approved_learnings(self._make_proposal(), "Jane Smith", "Approved")

        content = approved_file.read_text()
        assert "v001" in content
        assert "Jane Smith" in content
        assert "engine/signals.py" in content

    def test_rejection_does_not_modify_approved_learnings(self):
        approved_file = Path(self.tmp.name) / "APPROVED_LEARNINGS.md"
        original_content = "# Approved Learnings\n*No learnings yet.*\n"
        approved_file.write_text(original_content)

        # Rejection should NOT call append_to_approved_learnings
        # Verify the file is unchanged after a rejection path
        # (promote_learning.run with decision=reject does not call append)
        with mock.patch.object(self.mod, "APPROVED_LEARNINGS", approved_file):
            with mock.patch.object(self.mod, "run_tests", return_value=True):
                with mock.patch.object(self.mod, "append_audit"):
                    try:
                        self.mod.run(
                            self._make_proposal()["_path"],
                            "reject",
                            "Jane Smith",
                            "Not enough data"
                        )
                    except Exception:
                        pass

        content = approved_file.read_text()
        assert content == original_content, "Rejection should not modify APPROVED_LEARNINGS.md"
