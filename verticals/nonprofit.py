"""Nonprofit vertical — ICP config and query banks.

Targets: Social services nonprofits, faith-based organizations, community action
agencies, human services orgs, workforce development nonprofits.

Key insight: Grant award announcements are the highest-quality buying trigger.
A new federal/state grant means confirmed budget, confirmed headcount growth,
and funder compliance requirements that digital onboarding satisfies.
"""
from __future__ import annotations

DISCOVERY_QUERIES = [
    # Grant and funding signals
    '"{company}" "grant award" OR "awarded grant" OR "receives funding" 2024 2025',
    'site:sam.gov "{company}"',
    'site:usaspending.gov "{company}"',
    '"{company}" "federal grant" OR "HHS grant" OR "DOL grant" {state}',

    # Manual process signals
    'site:{domain} filetype:pdf "new hire" OR "new volunteer" packet forms',
    'site:indeed.com "{company}" HR coordinator "paper" OR "manual" OR "filing"',

    # ADP confirmation
    '"{company}" "ADP" payroll nonprofit {state}',

    # New leader hire
    '"{company}" "director of human resources" OR "HR director" hired 2024 2025',

    # Growth indicators
    '"{company}" "new program" OR "expanding services" OR "new site" {state} 2024 2025',
]

ICP_CONFIG = {
    "vertical": "nonprofit",
    "sweet_spot_employee_ranges": ["50-99", "100-249", "250-499"],
    "min_employees": 30,
    "max_employees": 1000,
    "multi_location_required": False,
    "frontline_workforce": True,
    "us_only": True,
}

SUB_VERTICALS = {
    "social_services": {
        "description": "Human services, case management, community action",
        "key_signal": "grant_award",
        "best_product": "Onboard",
        "specific_pain": "Funder audit requirements for documented onboarding — paper files don't cut it",
    },
    "faith_based": {
        "description": "Church-affiliated nonprofits, faith-based social services",
        "key_signal": "pdf_new_hire_packet",
        "best_product": "Onboard",
        "specific_pain": "Lean HR team + high volunteer/seasonal staff turnover = paper overload",
    },
    "workforce_development": {
        "description": "Job training, adult education, workforce development",
        "key_signal": "sam_contract_award",
        "best_product": "Onboard",
        "specific_pain": "DOL/WIA grants require participant documentation — similar to employee onboarding",
    },
    "community_health": {
        "description": "FQHCs, community health centers, rural health",
        "key_signal": "pdf_new_hire_packet",
        "best_product": "Onboard",
        "specific_pain": "HRSA grant compliance for clinical staff onboarding documentation",
    },
}

TARGET_STATES = ["TX", "FL", "CA", "OH", "IL", "PA", "NY", "NC", "GA", "MI"]

# 501(c)(3) search modifiers
NONPROFIT_SEARCH_MODIFIERS = [
    '"501(c)(3)"', '"non-profit"', '"nonprofit"',
    '"community organization"', '"community services"',
]
