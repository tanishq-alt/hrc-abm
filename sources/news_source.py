"""Press release / news trigger signal source.

Searches for news events that indicate buying triggers:
- New location openings (expansion)
- Acquisitions and mergers
- New HR leader hired
- Grant funding announcements
- Headcount growth announcements
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


NEWS_SIGNAL_MAP = {
    "acquisition": {
        "keywords": ["acquired", "merger", "acquisition", "merges with", "purchased by", "sold to"],
        "queries": [
            '"{company}" acquired merger acquisition 2024 2025',
            '"{company}" "acquired by" OR "merges with"',
        ],
        "raw_score": 20,
    },
    "facility_expansion": {
        "keywords": ["new location", "opens new", "expansion", "new facility", "new office", "new branch"],
        "queries": [
            '"{company}" "new location" OR "opens" OR "expansion" {state} 2024 2025',
            '"{company}" "new facility" OR "new office" press release',
        ],
        "raw_score": 15,
    },
    "new_hr_leader": {
        "keywords": ["appoints", "names", "welcomes", "joins as", "named as", "director of human resources",
                     "chro", "vp of hr", "chief people officer"],
        "queries": [
            '"{company}" "director of human resources" OR "CHRO" appointed named 2024 2025',
            '"{company}" new "HR director" OR "people officer" joined hired',
        ],
        "raw_score": 18,
    },
    "grant_award": {
        "keywords": ["grant award", "receives grant", "funding award", "awarded grant", "grant recipient"],
        "queries": [
            '"{company}" "grant award" OR "receives grant" OR "funding" 2024 2025',
        ],
        "raw_score": 15,
    },
}


class NewsSource(BaseSource):
    """Press release / news trigger signal collector."""

    source_name = "news"
    rate_limit_seconds = 4.0

    def __init__(self, signal_types: List[str] = None):
        self.signal_types = signal_types or list(NEWS_SIGNAL_MAP.keys())

    def collect(
        self,
        company_name: str,
        domain: str,
        state: str = "",
        vertical: str = "",
        **kwargs,
    ) -> List[Signal]:
        signals = []

        for signal_type in self.signal_types:
            config = NEWS_SIGNAL_MAP.get(signal_type, {})
            queries = config.get("queries", [])
            keywords = config.get("keywords", [])
            raw_score = config.get("raw_score", 12)

            for template in queries[:1]:
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

                    matched_kw = [kw for kw in keywords if kw in combined]
                    if not matched_kw:
                        continue

                    kw = matched_kw[0]
                    idx = combined.find(kw)
                    excerpt = (body or title)[max(0, idx-30):idx+150].strip()

                    from urllib.parse import urlparse
                    source_domain = urlparse(url).netloc.replace("www.", "")

                    sig = Signal.from_type(
                        signal_type=signal_type,
                        source_url=url,
                        source_domain=source_domain,
                        evidence_excerpt=excerpt[:200],
                        signal_date="",
                        what_it_proves=f"News/press release confirms {signal_type} for {company_name}",
                        what_it_does_not_prove="News article — verify with additional sources",
                        source_name="News / Press Releases",
                        raw_score=raw_score,
                    )
                    signals.append(sig)
                    break

                if any(s.signal_type == signal_type for s in signals):
                    break

        return signals
