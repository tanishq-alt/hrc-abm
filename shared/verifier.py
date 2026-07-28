"""Shared verifier — re-exports from scrapers/shared/verifier.py for new module paths."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scrapers", "shared"))
from verifier import verify_domain, is_resolvable, resolve_domain, DomainResolution  # noqa: F401
