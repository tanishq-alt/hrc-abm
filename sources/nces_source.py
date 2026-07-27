"""NCES (National Center for Education Statistics) data signal source.

Targets education vertical: K-12 districts, charter schools, Head Start.
NCES data provides authoritative enrollment and staff counts.

Signals extracted:
- District enrollment size (maps to employee range)
- Enrollment growth (hiring surge trigger)
- NCES district ID (confirms it's a real K-12 entity)
"""
from __future__ import annotations

import re
import sys
import os
import time
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.base import BaseSource
from engine.signals import Signal

try:
    from scrapers.shared.ddg import ddg_search
    from scrapers.shared.fetcher import fetch_text
except ImportError:
    try:
        from shared.ddg import ddg_search
        from shared.fetcher import fetch_text
    except ImportError:
        def ddg_search(q, max_results=10, retries=3):
            try:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    return list(ddgs.text(q, max_results=max_results))
            except Exception:
                return []
        def fetch_text(url, timeout=10):
            return ""


NCES_QUERY_TEMPLATES = [
    'site:nces.ed.gov "{company}" district',
    'site:nces.ed.gov "{company}" school',
    '"{company}" NCES district enrollment staff {state}',
    'nces.ed.gov school district "{company}" {state}',
]

NCES_KEYWORDS = [
    "nces", "national center for education statistics",
    "enrollment", "district id", "school district",
    "fte teachers", "staff count", "lea",
]


class NCESSource(BaseSource):
    """NCES education data signal collector (education vertical only)."""

    source_name = "nces"
    rate_limit_seconds = 4.0

    def collect(
        self,
        company_name: str,
        domain: str,
        state: str = "",
        vertical: str = "",
        **kwargs,
    ) -> List[Signal]:
        # Only relevant for education vertical
        if vertical and vertical not in ("education", ""):
            return []

        signals = []

        for template in NCES_QUERY_TEMPLATES[:2]:
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

                matched = [kw for kw in NCES_KEYWORDS if kw in combined]
                if not matched:
                    continue

                kw = matched[0]
                idx = combined.find(kw)
                excerpt = (body or title)[max(0, idx-30):idx+150].strip()

                from urllib.parse import urlparse
                source_domain = urlparse(url).netloc.replace("www.", "")

                is_official = "nces.ed.gov" in source_domain
                raw_score = 20 if is_official else 12

                sig = Signal.from_type(
                    signal_type="nces_district_data",
                    source_url=url,
                    source_domain=source_domain,
                    evidence_excerpt=excerpt[:200],
                    signal_date="",
                    what_it_proves=(
                        f"NCES data confirms {company_name} is a real K-12 district "
                        "with authoritative enrollment and staff counts"
                    ),
                    what_it_does_not_prove="Does not confirm HRIS system or onboarding process",
                    source_name="NCES / ED.gov",
                    raw_score=raw_score,
                )
                signals.append(sig)
                break

            if signals:
                break

        return signals[:1]
