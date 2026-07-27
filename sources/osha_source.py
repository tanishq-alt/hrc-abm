"""OSHA citation signal source.

OSHA violations are high-quality buying triggers for manufacturing and healthcare.
An OSHA citation means:
  - The company has an audit trail problem
  - Documentation compliance is a real concern
  - HR leadership is under pressure to fix it

Sources:
  - OSHA enforcement data (osha.gov)
  - DDG search for OSHA citations
"""
from __future__ import annotations

import sys
import os
import time
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.base import BaseSource
from engine.signals import Signal

try:
    from scrapers.shared.ddg import ddg_search
except ImportError:
    try:
        from shared.ddg import ddg_search
    except ImportError:
        def ddg_search(q, max_results=10, retries=3):
            try:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    return list(ddgs.text(q, max_results=max_results))
            except Exception:
                return []


OSHA_KEYWORDS = [
    "osha citation", "osha penalty", "osha violation", "osha fine",
    "osha inspection", "osha willful", "osha serious", "osha repeat",
    "workplace safety violation", "osha recordkeeping",
]

OSHA_QUERY_TEMPLATES = [
    '"{company}" OSHA citation penalty violation {state}',
    'site:osha.gov "{company}" enforcement inspection',
    '"{company}" OSHA fine workplace safety',
]


class OSHASource(BaseSource):
    """OSHA citation signal collector (manufacturing and healthcare)."""

    source_name = "osha"
    rate_limit_seconds = 4.0

    def collect(
        self,
        company_name: str,
        domain: str,
        state: str = "",
        vertical: str = "",
        **kwargs,
    ) -> List[Signal]:
        # Most relevant for manufacturing and healthcare
        if vertical and vertical not in ("manufacturing", "healthcare", ""):
            return []

        signals = []

        for template in OSHA_QUERY_TEMPLATES[:2]:
            query = template.format(company=company_name, state=state)
            results = ddg_search(query, max_results=8)
            time.sleep(self.rate_limit_seconds)

            for r in results:
                url = r.get("href", "")
                title = r.get("title", "")
                body = r.get("body", "")
                combined = (title + " " + body).lower()

                company_lower = company_name.lower()
                if company_lower not in combined:
                    continue

                matched = [kw for kw in OSHA_KEYWORDS if kw in combined]
                if not matched:
                    continue

                kw = matched[0]
                idx = combined.find(kw)
                excerpt = (body or title)[max(0, idx-30):idx+120].strip()

                from urllib.parse import urlparse
                source_domain = urlparse(url).netloc.replace("www.", "")

                is_official = "osha.gov" in source_domain
                raw_score = 22 if is_official else 15

                sig = Signal.from_type(
                    signal_type="osha_citation",
                    source_url=url,
                    source_domain=source_domain,
                    evidence_excerpt=excerpt[:200],
                    signal_date="",
                    what_it_proves=(
                        f"OSHA citation/penalty for {company_name} — "
                        "documentation compliance is under regulatory scrutiny"
                    ),
                    what_it_does_not_prove="Does not confirm HRIS or onboarding system",
                    source_name="OSHA.gov",
                    raw_score=raw_score,
                )
                signals.append(sig)
                break

            if signals:
                break

        return signals[:1]
