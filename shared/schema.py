"""Shared schema — re-exports from scrapers/shared/schema.py for new module paths."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scrapers", "shared"))
from schema import (  # noqa: F401
    CANONICAL_FIELDS, DOMAIN_STATUS_VERIFIED, DOMAIN_STATUS_UNRESOLVED,
    ADP_CONFIRMED, ADP_NOT_FOUND, ADP_NOT_CHECKED,
    CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
    PRODUCT_ONBOARD, PRODUCT_WORKMATES, PRODUCT_ONBOARD_WORKMATES,
    Signal, LeadRecord, make_row, make_row_from_dict,
)
