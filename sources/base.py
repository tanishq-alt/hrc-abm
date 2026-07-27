"""BaseSource abstract class for all signal sources.

Every source must:
1. Accept a company name + domain as input
2. Return a list of Signal objects
3. Handle errors gracefully (return [] on failure)
4. Respect rate limits — use delays between requests
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class BaseSource(ABC):
    """Abstract base class for all signal sources."""

    source_name: str = "base"
    rate_limit_seconds: float = 3.0

    @abstractmethod
    def collect(
        self,
        company_name: str,
        domain: str,
        state: str = "",
        vertical: str = "",
        **kwargs,
    ) -> List:
        """Collect signals for a given company.

        Args:
            company_name: Human-readable company name
            domain: Canonical company domain (e.g., "bestcare.org")
            state: Two-letter US state code (e.g., "TX")
            vertical: One of: healthcare, education, manufacturing, nonprofit, government
            **kwargs: Source-specific parameters

        Returns:
            List of Signal objects. Empty list if no signals found or on error.
        """
        ...

    def safe_collect(
        self,
        company_name: str,
        domain: str,
        state: str = "",
        vertical: str = "",
        **kwargs,
    ) -> List:
        """Wrapped collect() with error handling. Always returns a list."""
        try:
            return self.collect(company_name, domain, state, vertical, **kwargs)
        except Exception as e:
            print(f"  [{self.source_name}] Error collecting for {company_name}: {e}", flush=True)
            return []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
