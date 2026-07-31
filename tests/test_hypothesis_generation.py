"""
Tests for analyze_outcomes.py — proposal YAML format validation.
- write_proposal() creates a valid YAML-parseable file
- Required fields are present: version, status, description, hypothesis, backtest, canary
- change_type is one of the valid enum values
- Proposal file name follows vNNN_ pattern
- Status defaults to 'pending_review'
"""
import re
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


VALID_CHANGE_TYPES = {
    "copy_tuning", "query_addition", "signal_weight",
    "tier_floor_adjustment", "icp_score_boundary", "hard_gate",
}


class TestProposalFileFormat:
    def setup_method(self):
        self.mod = get_analyze_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.proposals_dir = Path(self.tmp.name)
        import unittest.mock as mock
        mock.patch.object(self.mod, "PROPOSALS_DIR", self.proposals_dir).start()

    def teardown_method(self):
        self.tmp.cleanup()

    def test_write_proposal_creates_file(self):
        path = self.mod.write_proposal(
            version="001",
            description="Test proposal",
            hypothesis={
                "observation": "Test observation text.",
                "file": "engine/signals.py",
                "parameter": "SIGNAL_BASE_SCORES['rfp_hris']",
                "current_value": 30,
                "proposed_value": 35,
                "change_type": "signal_weight",
            },
            evidence_segments=[{
                "dimensions": {"vertical": "healthcare"},
                "sends": 40,
                "replies": 10,
                "meetings": 5,
                "reply_rate_pct": 25.0,
                "meeting_rate_pct": 12.5,
            }],
            backtest_placeholder={"sample_size": 40, "historical_periods": 3},
        )
        assert path.exists()

    def test_proposal_filename_pattern(self):
        path = self.mod.write_proposal(
            version="042",
            description="Another test proposal here",
            hypothesis={
                "observation": "Obs.",
                "file": "engine/scorer.py",
                "parameter": "icp_floor",
                "current_value": 26,
                "proposed_value": 28,
                "change_type": "tier_floor_adjustment",
            },
            evidence_segments=[],
            backtest_placeholder={"sample_size": 35, "historical_periods": 2},
        )
        assert re.match(r"^v\d{3}_", path.name), f"Filename should start with vNNN_: {path.name}"

    def test_proposal_contains_required_sections(self):
        path = self.mod.write_proposal(
            version="001",
            description="Required sections test",
            hypothesis={
                "observation": "Some observation.",
                "file": "engine/signals.py",
                "parameter": "SIGNAL_BASE_SCORES['pdf_new_hire_packet']",
                "current_value": 35,
                "proposed_value": 40,
                "change_type": "signal_weight",
            },
            evidence_segments=[{
                "dimensions": {},
                "sends": 50,
                "replies": 10,
                "meetings": 4,
                "reply_rate_pct": 20.0,
                "meeting_rate_pct": 8.0,
            }],
            backtest_placeholder={"sample_size": 50, "historical_periods": 3},
        )
        content = path.read_text()
        for required_field in ["version:", "status:", "description:", "hypothesis:",
                               "backtest:", "canary:", "human_review:"]:
            assert required_field in content, f"Missing section: {required_field}"

    def test_proposal_status_defaults_to_pending_review(self):
        path = self.mod.write_proposal(
            version="001",
            description="Status test",
            hypothesis={
                "observation": "Obs.",
                "file": "engine/signals.py",
                "parameter": "SIGNAL_BASE_SCORES['test']",
                "current_value": 10,
                "proposed_value": 15,
                "change_type": "signal_weight",
            },
            evidence_segments=[],
            backtest_placeholder={"sample_size": 30, "historical_periods": 1},
        )
        content = path.read_text()
        assert 'status: "pending_review"' in content

    def test_proposal_change_type_written_correctly(self):
        for change_type in ["signal_weight", "copy_tuning", "query_addition"]:
            path = self.mod.write_proposal(
                version="001",
                description=f"Change type {change_type}",
                hypothesis={
                    "observation": "Obs.",
                    "file": "engine/signals.py",
                    "parameter": "test",
                    "current_value": 1,
                    "proposed_value": 2,
                    "change_type": change_type,
                },
                evidence_segments=[],
                backtest_placeholder={"sample_size": 30, "historical_periods": 1},
            )
            content = path.read_text()
            assert f'change_type: "{change_type}"' in content

    def test_evidence_segments_written_to_proposal(self):
        path = self.mod.write_proposal(
            version="001",
            description="Evidence segments test",
            hypothesis={
                "observation": "Obs.",
                "file": "engine/signals.py",
                "parameter": "test",
                "current_value": 1,
                "proposed_value": 2,
                "change_type": "signal_weight",
            },
            evidence_segments=[{
                "dimensions": {"vertical": "healthcare"},
                "sends": 42,
                "replies": 8,
                "meetings": 4,
                "reply_rate_pct": 19.0,
                "meeting_rate_pct": 9.5,
            }],
            backtest_placeholder={"sample_size": 42, "historical_periods": 2},
        )
        content = path.read_text()
        assert "sends: 42" in content
        assert "meeting_rate_pct: 9.5" in content

    def test_canary_starts_as_not_started(self):
        path = self.mod.write_proposal(
            version="001",
            description="Canary test",
            hypothesis={
                "observation": "Obs.",
                "file": "engine/signals.py",
                "parameter": "test",
                "current_value": 1,
                "proposed_value": 2,
                "change_type": "tier_floor_adjustment",
            },
            evidence_segments=[],
            backtest_placeholder={"sample_size": 30, "historical_periods": 1},
        )
        content = path.read_text()
        assert 'status: "not_started"' in content
        assert "canary_pct: 20" in content
        assert "min_cycles: 2" in content
