"""Job posting signal source.

Searches for HR job postings that indicate:
- Manual/paper onboarding processes (job tasks mention paper, spreadsheets, filing)
- ADP usage (job qualifications mention ADP experience required)
- New HR leader hires (CHRO, HR Director recently hired)
- Organizational growth (multiple open HR positions)
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


# Keywords that indicate manual/paper HR processes in job postings
MANUAL_PROCESS_KEYWORDS = [
    "maintain paper", "paper files", "paper records", "paper forms",
    "manual data entry", "maintain spreadsheet", "enter data manually",
    "filing personnel", "physical files", "binder", "file cabinet",
    "scan and file", "update spreadsheet", "maintain binders",
    "i-9 paper", "paper i-9",
]

# Keywords that confirm ADP usage in job requirements
ADP_KEYWORDS = [
    "adp workforce", "adp run", "adp payroll", "adp hris",
    "experience with adp", "proficiency in adp", "adp workforcenow",
    "adp totalforce", "adp preferred",
]

# Leadership hire keywords
LEADERSHIP_KEYWORDS = [
    "director of human resources", "vp of human resources", "chro",
    "chief human resources", "vp hr", "director hr", "head of hr",
    "hr director", "people director",
]

JOB_QUERY_TEMPLATES = [
    # Manual process signals
    'site:indeed.com "{company}" HR "paper" OR "manual" OR "spreadsheet" onboarding',
    'site:linkedin.com/jobs "{company}" "HR" "paper forms" OR "manual entry" OR "filing"',
    '"{company}" job posting HR coordinator "maintain" "records" OR "files"',
    # ADP signals
    'site:indeed.com "{company}" "ADP" human resources payroll',
    '"{company}" careers "ADP WorkforceNow" OR "ADP RUN" required',
    # New leader hires
    '"{company}" "director of human resources" hiring 2024 2025',
    '"{company}" new "HR director" OR "CHRO" appointed joined',
]


class JobsSource(BaseSource):
    """Job posting signal collector."""

    source_name = "jobs"
    rate_limit_seconds = 5.0

    def __init__(self, max_results: int = 8):
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

        for template in JOB_QUERY_TEMPLATES[:4]:  # Limit queries to avoid rate limits
            query = template.format(company=company_name, domain=domain, state=state)
            results = ddg_search(query, max_results=self.max_results)
            time.sleep(self.rate_limit_seconds)

            for r in results:
                url = r.get("href", "")
                title = r.get("title", "")
                body = r.get("body", "")
                combined = (title + " " + body).lower()

                company_lower = company_name.lower()
                if company_lower not in combined and domain.lower() not in combined:
                    continue

                signal_type = None
                excerpt = ""

                # Check for manual process evidence
                for kw in MANUAL_PROCESS_KEYWORDS:
                    if kw in combined:
                        signal_type = "job_manual_task"
                        idx = combined.find(kw)
                        excerpt = (body or title)[max(0, idx-30):idx+100].strip()
                        break

                # Check for ADP confirmation
                if not signal_type:
                    for kw in ADP_KEYWORDS:
                        if kw in combined:
                            signal_type = "adp_confirmed"
                            idx = combined.find(kw)
                            excerpt = (body or title)[max(0, idx-30):idx+100].strip()
                            break

                # Check for new HR leader
                if not signal_type:
                    for kw in LEADERSHIP_KEYWORDS:
                        if kw in combined:
                            signal_type = "new_hr_leader"
                            excerpt = f"Job posting: {title[:80]}"
                            break

                if not signal_type or not excerpt:
                    continue

                from urllib.parse import urlparse
                source_domain = urlparse(url).netloc.replace("www.", "")

                raw_score = {
                    "job_manual_task": 22,
                    "adp_confirmed": 20,
                    "new_hr_leader": 18,
                }.get(signal_type, 15)

                sig = Signal.from_type(
                    signal_type=signal_type,
                    source_url=url,
                    source_domain=source_domain,
                    evidence_excerpt=excerpt[:200],
                    signal_date="",
                    what_it_proves=f"Job posting at {company_name} references {signal_type}",
                    what_it_does_not_prove="Job posting may be expired or role already filled",
                    source_name="Job Boards",
                    raw_score=raw_score,
                )
                signals.append(sig)

        return signals
