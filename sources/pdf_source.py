"""PDF new-hire packet discovery source.

Searches for publicly accessible PDF new-hire packets on company domains.
This is the highest-quality signal (Tier A) for manual onboarding evidence.

Search strategy:
  1. DDG filetype:pdf search on company domain
  2. Direct URL pattern probing (common new hire packet paths)
  3. Page text extraction from careers/HR pages
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


# PDF filenames that indicate new hire packets
NEW_HIRE_PDF_PATTERNS = [
    r"new.?hire.?packet",
    r"new.?employee.?packet",
    r"onboarding.?packet",
    r"orientation.?packet",
    r"new.?hire.?forms",
    r"employee.?welcome.?packet",
    r"new.?hire.?checklist",
    r"day.?one.?packet",
    r"new.?staff.?packet",
]

# Text patterns that confirm a paper process in PDF content
PAPER_PROCESS_INDICATORS = [
    "print and sign",
    "print this form",
    "return completed form",
    "mail to hr",
    "fax to hr",
    "bring completed",
    "fill out and return",
    "download and complete",
    "scan and email",
    "paper i-9",
    "wet signature",
    "blue or black ink",
]


class PDFSource(BaseSource):
    """PDF new-hire packet signal collector."""

    source_name = "pdf"
    rate_limit_seconds = 3.0

    def __init__(self, max_results: int = 10):
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

        # Strategy 1: DDG filetype:pdf search
        queries = [
            f'site:{domain} filetype:pdf "new hire" OR "new employee" packet',
            f'"{company_name}" "new hire packet" filetype:pdf',
            f'site:{domain} filetype:pdf onboarding orientation forms',
        ]

        for query in queries:
            results = ddg_search(query, max_results=self.max_results)
            time.sleep(self.rate_limit_seconds)

            for r in results:
                url = r.get("href", "")
                title = r.get("title", "")
                body = r.get("body", "")

                if not url or not url.lower().endswith(".pdf"):
                    continue

                # Check if URL or title matches new hire packet patterns
                url_title = (url + " " + title).lower()
                is_new_hire_pdf = any(
                    re.search(pat, url_title, re.IGNORECASE)
                    for pat in NEW_HIRE_PDF_PATTERNS
                )

                if not is_new_hire_pdf:
                    continue

                # Fetch PDF text to confirm paper process indicators
                pdf_text = fetch_text(url, timeout=15)
                has_paper_indicator = any(
                    indicator in pdf_text.lower()
                    for indicator in PAPER_PROCESS_INDICATORS
                ) if pdf_text else False

                # Even without confirmation, a new hire packet PDF is strong evidence
                excerpt = f"PDF: {title[:80]}" if title else f"New hire packet PDF at {domain}"
                if pdf_text:
                    for indicator in PAPER_PROCESS_INDICATORS:
                        if indicator in pdf_text.lower():
                            idx = pdf_text.lower().find(indicator)
                            excerpt = pdf_text[max(0, idx-20):idx+100].strip()
                            break

                raw_score = 35 if has_paper_indicator else 28

                sig = Signal.from_type(
                    signal_type="pdf_new_hire_packet",
                    source_url=url,
                    source_domain=domain,
                    evidence_excerpt=excerpt[:200],
                    signal_date=str(date.today()),  # PDF discovered today
                    what_it_proves=(
                        f"Publicly accessible new hire packet PDF on {domain} — "
                        "direct evidence of paper-based onboarding process"
                    ),
                    what_it_does_not_prove=(
                        "Does not confirm ADP usage or exact employee count"
                    ),
                    source_name="PDF Discovery",
                    raw_score=raw_score,
                )
                signals.append(sig)

                if signals:
                    break  # One PDF signal per company is sufficient

            if signals:
                break

        return signals[:2]  # Max 2 PDF signals per company
