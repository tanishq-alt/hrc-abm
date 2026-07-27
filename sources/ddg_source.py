"""DuckDuckGo search signal source.

Searches DDG for company-specific signals across multiple query templates.
Returns normalized Signal objects.
"""
from __future__ import annotations

import sys
import os
import time
from typing import List

# Support running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.base import BaseSource
from engine.signals import Signal

try:
    from scrapers.shared.ddg import ddg_search
except ImportError:
    try:
        from shared.ddg import ddg_search
    except ImportError:
        def ddg_search(query, max_results=10, retries=3):
            try:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=max_results))
            except Exception:
                return []


# Query templates per signal type
QUERY_TEMPLATES = {
    "manual_onboarding": [
        '"{company}" "new hire packet" filetype:pdf',
        '"{company}" "new employee orientation" paper fillable',
        '"{company}" site:{domain} "new hire" paperwork',
    ],
    "adp_confirmed": [
        '"{company}" "ADP WorkforceNow" OR "ADP Run" OR "ADP payroll"',
        'site:{domain} "powered by ADP" OR "adp.com" OR "workforcenow"',
        '"{company}" "ADP" payroll system HR',
    ],
    "job_manual_task": [
        'site:indeed.com "{company}" HR "maintain spreadsheet" OR "paper forms" OR "manual entry"',
        'site:linkedin.com/jobs "{company}" "data entry" "new hire" OR "onboarding"',
        '"{company}" HR coordinator "manage paper" OR "filing" OR "manual process"',
    ],
    "osha_citation": [
        '"{company}" OSHA citation penalty violation',
        'site:osha.gov "{company}" inspection',
    ],
    "cms_deficiency": [
        '"{company}" CMS deficiency survey citation',
        '"{company}" Medicare survey "statement of deficiencies"',
    ],
    "new_hr_leader": [
        '"{company}" "director of human resources" OR "HR director" hired appointed 2024 2025',
        '"{company}" "new CHRO" OR "new VP HR" OR "joins as HR"',
    ],
    "acquisition": [
        '"{company}" acquired merger acquisition 2024 2025',
        '"{company}" "acquired by" OR "merges with" OR "acquires"',
    ],
}


class DDGSource(BaseSource):
    """DuckDuckGo search signal collector."""

    source_name = "ddg"
    rate_limit_seconds = 4.0

    def __init__(self, signal_types: List[str] = None, max_results: int = 5):
        self.signal_types = signal_types or list(QUERY_TEMPLATES.keys())
        self.max_results = max_results

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
            templates = QUERY_TEMPLATES.get(signal_type, [])
            for template in templates[:1]:  # One query per signal type to avoid rate limits
                query = template.format(
                    company=company_name,
                    domain=domain,
                    state=state,
                )
                results = ddg_search(query, max_results=self.max_results)
                time.sleep(self.rate_limit_seconds)

                for r in results:
                    url = r.get("href", "")
                    title = r.get("title", "")
                    body = r.get("body", "")
                    excerpt = (body[:200] if body else title[:200]).strip()

                    if not url or not excerpt:
                        continue

                    # Basic relevance check
                    company_lower = company_name.lower()
                    if company_lower not in (title + body + url).lower():
                        continue

                    from urllib.parse import urlparse
                    source_domain = urlparse(url).netloc.replace("www.", "")

                    sig = Signal.from_type(
                        signal_type=signal_type,
                        source_url=url,
                        source_domain=source_domain,
                        evidence_excerpt=excerpt,
                        signal_date="",  # DDG doesn't reliably provide dates
                        what_it_proves=f"DDG search result confirms {signal_type} for {company_name}",
                        what_it_does_not_prove="May be secondary source — confirm with page fetch",
                        source_name="DuckDuckGo",
                        raw_score=20,
                    )
                    signals.append(sig)
                    break  # One signal per signal_type per query

        return signals
