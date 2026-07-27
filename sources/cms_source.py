"""CMS Care Compare / Medicare deficiency signal source.

Targets healthcare vertical: home health, hospice, SNF, ALF.
CMS deficiencies and low star ratings are high-quality buying triggers.

Sources:
  - CMS Care Compare (care.cms.gov)
  - Medicare.gov nursing home compare
  - DDG search for CMS survey findings
"""
from __future__ import annotations

import re
import sys
import os
import time
from typing import List
from datetime import date

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

CMS_DEFICIENCY_KEYWORDS = [
    "cms deficiency",
    "statement of deficiency",
    "cms citation",
    "survey findings",
    "cms survey",
    "plan of correction",
    "cms complaint",
    "cms violation",
    "f-tag",
    "scope and severity",
    "immediate jeopardy",
    "standard deficiency",
]

CMS_QUERY_TEMPLATES = [
    '"{company}" CMS deficiency survey citation {state}',
    '"{company}" "statement of deficiencies" Medicare survey',
    '"{company}" CMS inspection findings healthcare',
    'site:medicare.gov "{company}" nursing home inspection',
]


class CMSSource(BaseSource):
    """CMS Care Compare deficiency signal collector (healthcare vertical only)."""

    source_name = "cms"
    rate_limit_seconds = 4.0

    def collect(
        self,
        company_name: str,
        domain: str,
        state: str = "",
        vertical: str = "",
        **kwargs,
    ) -> List[Signal]:
        # Only relevant for healthcare vertical
        if vertical and vertical not in ("healthcare", ""):
            return []

        signals = []

        for template in CMS_QUERY_TEMPLATES[:2]:
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

                matched_keywords = [kw for kw in CMS_DEFICIENCY_KEYWORDS if kw in combined]
                if not matched_keywords:
                    continue

                kw = matched_keywords[0]
                idx = combined.find(kw)
                excerpt = (body or title)[max(0, idx-30):idx+120].strip()

                from urllib.parse import urlparse
                source_domain = urlparse(url).netloc.replace("www.", "")

                is_cms_official = "medicare.gov" in source_domain or "cms.gov" in source_domain
                signal_type = "cms_deficiency" if is_cms_official else "cms_care_compare_flag"
                raw_score = 25 if is_cms_official else 18

                sig = Signal.from_type(
                    signal_type=signal_type,
                    source_url=url,
                    source_domain=source_domain,
                    evidence_excerpt=excerpt[:200],
                    signal_date="",
                    what_it_proves=(
                        f"CMS survey deficiency for {company_name} — "
                        "regulatory documentation pressure is a buying trigger"
                    ),
                    what_it_does_not_prove="Does not confirm paper onboarding or ADP usage",
                    source_name="CMS / Medicare.gov",
                    raw_score=raw_score,
                )
                signals.append(sig)
                break

            if signals:
                break

        return signals[:1]
