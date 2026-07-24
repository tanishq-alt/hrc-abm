# scrapers/shared — shared utilities for all 7 HR Intel prompts
from .ddg import ddg_search
from .fetcher import fetch_text
from .schema import CANONICAL_FIELDS, make_row
from .verifier import verify_domain

__all__ = ["ddg_search", "fetch_text", "CANONICAL_FIELDS", "make_row", "verify_domain"]
