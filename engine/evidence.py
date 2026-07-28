"""
Evidence ledger — first-class evidence objects with full provenance.

Every score-driving claim must trace to an Evidence object.
Three syndicated articles count as one.
"""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional


@dataclass
class Evidence:
    evidence_id: str = ""
    company_name: str = ""
    candidate_domain: str = ""
    source_url: str = ""
    source_title: str = ""
    source_owner: str = ""          # company / government / aggregator / social / unknown
    source_type: str = ""           # pdf / webpage / job_post / press_release / procurement / database / social
    evidence_tier: str = "C"        # A / B / C / D
    claim_type: str = ""            # manual_onboarding / adp_use / hris_rfp / hiring / expansion / etc.
    exact_excerpt: str = ""
    normalized_claim: str = ""
    event_date: str = ""            # ISO date of the event, empty if unknown
    observed_at: str = ""           # ISO date when scraped
    fresh_until: str = ""           # ISO date after which reverification is needed
    is_primary_source: bool = True
    is_syndicated: bool = False
    duplicate_group: str = ""
    company_identity_match: str = "" # confirmed / probable / uncertain / wrong_entity
    safe_to_quote: bool = True
    safe_to_use_for_outreach: bool = True
    supports: List[str] = field(default_factory=list)     # claim types this evidence supports
    contradicts: List[str] = field(default_factory=list)  # claim types this contradicts
    limitations: str = ""           # what this evidence does NOT prove
    content_hash: str = ""

    def __post_init__(self):
        if not self.observed_at:
            self.observed_at = datetime.utcnow().date().isoformat()
        if not self.evidence_id:
            self.evidence_id = self._make_id()
        if not self.content_hash and self.exact_excerpt:
            # Hash on excerpt only so syndicated copies (same text, different URLs)
            # are detected as duplicates. Short excerpts are normalized.
            normalized = self.exact_excerpt.strip().lower()
            self.content_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _make_id(self) -> str:
        raw = f"{self.candidate_domain}:{self.source_url}:{self.claim_type}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    @property
    def is_fresh(self) -> bool:
        if not self.fresh_until:
            return True
        try:
            return date.today() <= date.fromisoformat(self.fresh_until)
        except ValueError:
            return True

    @property
    def tier_weight(self) -> float:
        return {"A": 1.0, "B": 0.8, "C": 0.5, "D": 0.1}.get(self.evidence_tier, 0.5)


# Freshness defaults by claim type (days)
FRESHNESS_DEFAULTS = {
    "job_post":           45,
    "hiring_cluster":     60,
    "leadership_change":  90,
    "rfp_hris":           0,    # active until deadline or award; 0 = check manually
    "funding":           120,
    "expansion":         120,
    "manual_onboarding": 180,
    "adp_use":            90,
    "hris_rfp":            0,
    "cms_deficiency":    365,
    "osha_citation":     365,
    "sam_award":         180,
    "stable_firmographic": 180,
}


class EvidenceLedger:
    """Holds all evidence for one account. Deduplicates syndicated sources."""

    def __init__(self):
        self._items: List[Evidence] = []

    def add(self, ev: Evidence):
        # Mark syndicated: same content_hash → duplicate
        for existing in self._items:
            if existing.content_hash and ev.content_hash == existing.content_hash:
                ev.is_syndicated = True
                ev.duplicate_group = existing.evidence_id
                break
        self._items.append(ev)

    def primary_evidence(self) -> List[Evidence]:
        """Return only non-syndicated evidence, sorted by tier then freshness."""
        unique = [e for e in self._items if not e.is_syndicated]
        return sorted(unique, key=lambda e: (-{"A":4,"B":3,"C":2,"D":1}.get(e.evidence_tier,0),
                                              not e.is_fresh))

    def best(self) -> Optional[Evidence]:
        p = self.primary_evidence()
        return p[0] if p else None

    def has_tier_ab(self) -> bool:
        return any(e.evidence_tier in ("A","B") for e in self.primary_evidence())

    def all_stale(self) -> bool:
        p = self.primary_evidence()
        return bool(p) and all(not e.is_fresh for e in p)

    def contradictions(self) -> List[Evidence]:
        return [e for e in self._items if e.contradicts]

    def source_count(self) -> int:
        """Count of independent (non-syndicated) sources."""
        return len([e for e in self._items if not e.is_syndicated])

    def to_list(self) -> List[dict]:
        return [
            {
                "evidence_id": e.evidence_id,
                "tier": e.evidence_tier,
                "claim": e.claim_type,
                "source_url": e.source_url,
                "excerpt": e.exact_excerpt[:200],
                "fresh": e.is_fresh,
                "syndicated": e.is_syndicated,
                "limitations": e.limitations,
            }
            for e in self._items
        ]
