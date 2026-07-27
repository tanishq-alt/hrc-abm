"""Manufacturing vertical — ICP config and query banks.

Targets: Plant-floor manufacturers, distribution centers, logistics operators,
food processing, automotive suppliers, packaging companies.

Key insight: OSHA citations are the strongest buying trigger for manufacturing.
A citation means HR is already under compliance pressure and documentation
accountability is a top-of-mind issue for the COO or plant manager.
"""
from __future__ import annotations

DISCOVERY_QUERIES = [
    # OSHA signals
    '"{company}" OSHA citation violation fine {state}',
    'site:osha.gov "{company}" inspection enforcement',

    # Manual process signals
    'site:indeed.com "{company}" HR "paper" OR "manual" OR "spreadsheet" manufacturing',
    'site:indeed.com "{company}" "safety sign-off" OR "training record" paper',

    # ADP confirmation
    '"{company}" "ADP WorkforceNow" OR "ADP payroll" manufacturing plant',
    'site:{domain} "adp.com" OR "workforcenow" payroll HR',

    # Growth/expansion
    '"{company}" "new facility" OR "plant expansion" OR "new warehouse" {state} 2024 2025',
    '"{company}" acquisition merger manufacturing 2024 2025',

    # PDF evidence
    'site:{domain} filetype:pdf "new hire" OR "new employee" orientation safety',
]

ICP_CONFIG = {
    "vertical": "manufacturing",
    "sweet_spot_employee_ranges": ["250-499", "500-999", "1000-1999"],
    "min_employees": 100,
    "max_employees": 5000,
    "multi_location_required": False,
    "frontline_workforce": True,
    "us_only": True,
}

SUB_VERTICALS = {
    "discrete_manufacturing": {
        "description": "Automotive parts, electronics, machinery manufacturing",
        "key_signal": "osha_citation",
        "best_product": "Onboard+Workmates",
        "specific_pain": "OSHA training documentation + frontline communication across shifts",
    },
    "food_processing": {
        "description": "Food and beverage manufacturing",
        "key_signal": "osha_citation",
        "best_product": "Onboard",
        "specific_pain": "FDA/OSHA compliance for food safety training documentation",
    },
    "distribution": {
        "description": "Distribution centers and 3PL",
        "key_signal": "caregiver_hiring_surge",
        "best_product": "Onboard+Workmates",
        "specific_pain": "High-volume seasonal hiring with frontline communication gap",
    },
    "construction": {
        "description": "Commercial and residential construction",
        "key_signal": "osha_citation",
        "best_product": "Onboard",
        "specific_pain": "OSHA safety training documentation for multi-site crews",
    },
}

TARGET_STATES = ["OH", "MI", "TX", "IL", "PA", "IN", "WI", "NC", "TN", "GA"]
