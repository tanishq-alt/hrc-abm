"""Shared DDG search — re-exports from scrapers/shared/ddg.py for new module paths."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scrapers", "shared"))
from ddg import ddg_search  # noqa: F401
