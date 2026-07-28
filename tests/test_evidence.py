"""
Tests for engine/evidence.py — Evidence deduplication.
Three syndicated articles with same content_hash count as 1 unique source.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from engine.evidence import Evidence, EvidenceLedger


def make_evidence(url: str, excerpt: str, tier: str = "C", claim: str = "manual_onboarding") -> Evidence:
    return Evidence(
        candidate_domain="acme.com",
        source_url=url,
        evidence_tier=tier,
        claim_type=claim,
        exact_excerpt=excerpt,
    )


class TestEvidenceLedgerDeduplication:
    def test_three_syndicated_articles_count_as_one_source(self):
        """Three articles with identical content → source_count() == 1."""
        ledger = EvidenceLedger()
        excerpt = "Employees must print, complete, and return new hire packet on Day 1."
        url_base = "https://acme.com/hr/packet.pdf"

        ev1 = make_evidence(url_base, excerpt)
        ev2 = make_evidence("https://mirror.com/acme-packet.pdf", excerpt)
        ev3 = make_evidence("https://syndicated.com/acme-packet.pdf", excerpt)

        ledger.add(ev1)
        ledger.add(ev2)
        ledger.add(ev3)

        assert ledger.source_count() == 1, (
            f"Expected 1 unique source, got {ledger.source_count()}"
        )

    def test_unique_articles_counted_separately(self):
        """Three articles with different content → source_count() == 3."""
        ledger = EvidenceLedger()
        ledger.add(make_evidence("https://acme.com/1.pdf", "New hire packet instructions"))
        ledger.add(make_evidence("https://acme.com/2.pdf", "ADP Workforce Now required skill"))
        ledger.add(make_evidence("https://acme.com/3.pdf", "CMS deficiency report 2024"))

        assert ledger.source_count() == 3

    def test_primary_evidence_excludes_syndicated(self):
        """primary_evidence() returns only non-syndicated items."""
        ledger = EvidenceLedger()
        excerpt = "shared content"
        ev1 = make_evidence("https://acme.com/primary.pdf", excerpt)
        ev2 = make_evidence("https://copy.com/copy.pdf", excerpt)
        ledger.add(ev1)
        ledger.add(ev2)

        primary = ledger.primary_evidence()
        assert len(primary) == 1
        assert primary[0].source_url == "https://acme.com/primary.pdf"

    def test_first_added_is_not_syndicated(self):
        """The first-added evidence is never marked syndicated."""
        ledger = EvidenceLedger()
        excerpt = "unique excerpt text here"
        ev = make_evidence("https://acme.com/first.pdf", excerpt)
        ledger.add(ev)
        assert ev.is_syndicated is False

    def test_duplicate_marked_syndicated(self):
        """Second evidence with same hash is marked syndicated."""
        ledger = EvidenceLedger()
        excerpt = "duplicate text content"
        ev1 = make_evidence("https://acme.com/orig.pdf", excerpt)
        ev2 = make_evidence("https://copy.com/copy.pdf", excerpt)
        ledger.add(ev1)
        ledger.add(ev2)
        assert ev2.is_syndicated is True

    def test_best_returns_highest_tier(self):
        """best() returns the highest-tier non-syndicated evidence."""
        ledger = EvidenceLedger()
        ledger.add(make_evidence("https://acme.com/c.pdf", "tier c evidence", tier="C"))
        ledger.add(make_evidence("https://acme.com/a.pdf", "tier a evidence unique", tier="A"))
        best = ledger.best()
        assert best is not None
        assert best.evidence_tier == "A"

    def test_empty_ledger_source_count_zero(self):
        ledger = EvidenceLedger()
        assert ledger.source_count() == 0
        assert ledger.best() is None

    def test_to_list_returns_all_items(self):
        """to_list() includes all items including syndicated."""
        ledger = EvidenceLedger()
        excerpt = "same"
        ledger.add(make_evidence("https://a.com/1.pdf", excerpt))
        ledger.add(make_evidence("https://b.com/2.pdf", excerpt))
        ledger.add(make_evidence("https://c.com/3.pdf", "different content"))
        items = ledger.to_list()
        assert len(items) == 3
