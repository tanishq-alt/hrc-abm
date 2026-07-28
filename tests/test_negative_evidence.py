"""
Tests for pipeline/run.py — find_negative_evidence() function.
- "volunteer only" text → fatal negative
- "workday" text → warning (not fatal)
- clean text → empty list
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


def get_find_negative_evidence():
    """Import find_negative_evidence from pipeline/run.py without triggering main()."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run",
        str(Path(__file__).parent.parent / "pipeline" / "run.py")
    )
    mod = importlib.util.load_from_spec_if_no_source = None
    # Use exec approach to avoid argparse triggering
    run_path = Path(__file__).parent.parent / "pipeline" / "run.py"
    namespace = {}
    with open(run_path) as f:
        source = f.read()
    # Execute only the function definition lines we need
    exec(compile(source, str(run_path), "exec"), namespace)
    return namespace["find_negative_evidence"]


# Direct import approach
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))


class TestFindNegativeEvidence:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Import find_negative_evidence directly."""
        # Patch sys.argv to prevent argparse from reading test args
        import sys
        original_argv = sys.argv
        sys.argv = ["run.py"]
        try:
            from pipeline.run import find_negative_evidence
            self.find_negative_evidence = find_negative_evidence
        finally:
            sys.argv = original_argv

    def test_volunteer_only_produces_fatal_negative(self):
        """'volunteer only' text → fatal negative evidence."""
        text = "This packet is for volunteer only positions at our organization."
        negatives = self.find_negative_evidence("acme.com", text, "pdf_new_hire_packet")

        fatal = [n for n in negatives if n["severity"] == "fatal"]
        assert len(fatal) >= 1, f"Expected at least 1 fatal negative, got: {negatives}"
        assert any("volunteer" in n["label"].lower() or "contractors" in n["label"].lower()
                   for n in fatal)

    def test_contractors_only_produces_fatal_negative(self):
        """'contractors only' text → fatal negative evidence."""
        text = "These forms are for contractors only and not for regular employees."
        negatives = self.find_negative_evidence("acme.com", text, "pdf_new_hire_packet")

        fatal = [n for n in negatives if n["severity"] == "fatal"]
        assert len(fatal) >= 1, f"Expected fatal negative for 'contractors only', got: {negatives}"

    def test_not_for_employees_produces_fatal_negative(self):
        """'not for employees' text → fatal negative."""
        text = "This onboarding material is not for employees of our company."
        negatives = self.find_negative_evidence("acme.com", text, "manual_onboarding")

        fatal = [n for n in negatives if n["severity"] == "fatal"]
        assert len(fatal) >= 1

    def test_workday_produces_warning_not_fatal(self):
        """'workday' text → warning severity (not fatal)."""
        text = "We use Workday for all HR processes and employee management."
        negatives = self.find_negative_evidence("acme.com", text, "pdf_new_hire_packet")

        assert len(negatives) >= 1, f"Expected at least 1 negative for workday text, got empty"

        workday_negs = [n for n in negatives if "workday" in n.get("label", "").lower()
                        or "workday" in n.get("type", "").lower()
                        or "hris_fit_category" in n]
        assert len(workday_negs) >= 1, f"Expected Workday-related negative, got: {negatives}"

        # Should be warning, not fatal
        for n in workday_negs:
            assert n["severity"] != "fatal", (
                f"Workday detection should be 'warning', not 'fatal': {n}"
            )

    def test_clean_text_produces_empty_list(self):
        """Clean, normal text → no negatives."""
        text = "Acme Healthcare hires caregivers for home health services in Texas."
        negatives = self.find_negative_evidence("acmehealthcare.com", text, "caregiver_hiring_surge")

        assert negatives == [], f"Expected empty list for clean text, got: {negatives}"

    def test_archived_content_produces_warning(self):
        """'archived' content → warning severity."""
        text = "ARCHIVED: This page is no longer active. Please contact HR for current forms."
        negatives = self.find_negative_evidence("acme.com", text, "pdf_new_hire_packet")

        archive_negs = [n for n in negatives
                        if "archive" in n.get("label", "").lower() or "stale" in n.get("type", "")]
        assert len(archive_negs) >= 1, f"Expected archived content negative, got: {negatives}"
        for n in archive_negs:
            assert n["severity"] == "warning"

    def test_staffing_agency_produces_warning(self):
        """'staffing agency' text → warning."""
        text = "We are a staffing agency placing temporary workers with client companies."
        negatives = self.find_negative_evidence("staffingco.com", text, "caregiver_hiring_surge")

        staffing_negs = [n for n in negatives if n.get("type") == "staffing_agency"]
        assert len(staffing_negs) >= 1, f"Expected staffing agency warning, got: {negatives}"
        for n in staffing_negs:
            assert n["severity"] == "warning"

    def test_workday_is_warning_not_hard_gate(self):
        """Workday warning should NOT trigger a fatal gate."""
        text = "We use Workday for payroll and benefits administration."
        negatives = self.find_negative_evidence("acme.com", text, "pdf_new_hire_packet")

        has_fatal = any(n["severity"] == "fatal" for n in negatives)
        assert not has_fatal, (
            f"Workday should produce warnings only, not fatals. Got: {negatives}"
        )

    def test_multiple_negatives_can_coexist(self):
        """Multiple negative signals can appear together."""
        text = "This page is archived. We use Workday for all HR processes."
        negatives = self.find_negative_evidence("acme.com", text, "pdf_new_hire_packet")

        assert len(negatives) >= 2, f"Expected multiple negatives, got: {negatives}"
