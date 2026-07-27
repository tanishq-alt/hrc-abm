"""SAM.gov / USAspending contract award signal source.

Contract awards are excellent buying triggers for:
- Nonprofits (federal/state grants for hiring)
- Government entities (new contracts requiring headcount)
- Healthcare (Medicaid, Medicare contracts)

A new contract award means:
  - Funding is confirmed — they have budget
  - Headcount is likely growing — onboarding demand is imminent
  - HR is under pressure to hire and onboard fast
"""
from __future__ import annotations

import sys
import os
import time
from typing import List
from datetime import date, timedelta

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


SAM_KEYWORDS = [
    "contract award", "grant award", "federal contract", "government contract",
    "sam.gov", "usaspending", "awarded contract", "grant recipient",
    "federal award", "contract modification", "task order",
    "cooperative agreement", "blanket purchase agreement",
]

SAM_QUERY_TEMPLATES = [
    'site:sam.gov "{company}"',
    'site:usaspending.gov "{company}" award',
    '"{company}" "contract award" OR "grant award" {state} 2024 2025',
    '"{company}" federal contract government award',
]


class SAMSource(BaseSource):
    """SAM.gov / USAspending contract award signal collector."""

    source_name = "sam"
    rate_limit_seconds = 4.0

    def collect(
        self,
        company_name: str,
        domain: str,
        state: str = "",
        vertical: str = "",
        **kwargs,
    ) -> List[Signal]:
        # Most relevant for nonprofit and government
        if vertical and vertical not in ("nonprofit", "government", "healthcare", ""):
            return []

        signals = []

        for template in SAM_QUERY_TEMPLATES[:2]:
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

                matched = [kw for kw in SAM_KEYWORDS if kw in combined]
                if not matched:
                    continue

                kw = matched[0]
                idx = combined.find(kw)
                excerpt = (body or title)[max(0, idx-30):idx+120].strip()

                from urllib.parse import urlparse
                source_domain = urlparse(url).netloc.replace("www.", "")

                is_official = any(d in source_domain for d in ("sam.gov", "usaspending.gov"))

                signal_type = "sam_contract_award" if is_official else "grant_award"
                raw_score = 20 if is_official else 14

                sig = Signal.from_type(
                    signal_type=signal_type,
                    source_url=url,
                    source_domain=source_domain,
                    evidence_excerpt=excerpt[:200],
                    signal_date="",
                    what_it_proves=(
                        f"Contract/grant award for {company_name} — "
                        "funding confirmed, headcount likely growing"
                    ),
                    what_it_does_not_prove="Does not confirm HRIS system or onboarding process",
                    source_name="SAM.gov / USASpending",
                    raw_score=raw_score,
                )
                signals.append(sig)
                break

            if signals:
                break

        return signals[:1]
