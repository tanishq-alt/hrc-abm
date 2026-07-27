"""Shared fetcher — re-exports from scrapers/shared/fetcher.py for new module paths."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scrapers", "shared"))
from fetcher import fetch_text  # noqa: F401
