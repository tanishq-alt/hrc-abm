"""Government vertical — ICP config and query banks.

Targets: County government, municipalities, special districts, transit authorities,
housing authorities, utility districts.

Key insight: Government procurement cycles are long but RFPs are public signals.
An RFP for HRIS is the highest-value trigger — they're actively evaluating.
SAM.gov contract awards signal budget and headcount activity.
"""
from __future__ import annotations

DISCOVERY_QUERIES = [
    # RFP signals — highest quality trigger
    '"{company}" RFP HRIS OR "HR software" OR "human resources system" {state}',
    'site:sam.gov "{company}" HRIS OR "human resources" solicitation',
    '"{company}" county "request for proposal" HR payroll {state}',

    # Contract awards
    'site:sam.gov "{company}" contract award',
    'site:usaspending.gov "{company}" {state}',

    # Manual process signals
    'site:{domain} filetype:pdf "new employee" OR "new hire" packet forms',
    'site:indeed.com "{company}" HR specialist "paper" OR "manual" OR "filing" government',

    # ADP confirmation
    '"{company}" "ADP" payroll county OR municipality {state}',

    # Growth/new headcount
    '"{company}" county "budget approved" OR "new positions" OR "hiring" 2024 2025',
]

ICP_CONFIG = {
    "vertical": "government",
    "sweet_spot_employee_ranges": ["100-249", "250-499", "500-999"],
    "min_employees": 50,
    "max_employees": 3000,
    "multi_location_required": False,
    "frontline_workforce": True,
    "us_only": True,
}

SUB_VERTICALS = {
    "county_government": {
        "description": "County governments (commission, administrator structure)",
        "key_signal": "rfp_hris",
        "best_product": "Onboard",
        "specific_pain": "Paper-based HR process across departments with no central system",
    },
    "municipality": {
        "description": "City and town governments",
        "key_signal": "sam_contract_award",
        "best_product": "Onboard",
        "specific_pain": "Separate onboarding for police, fire, public works — no unified process",
    },
    "special_district": {
        "description": "Transit authorities, utility districts, housing authorities",
        "key_signal": "job_manual_task",
        "best_product": "Onboard",
        "specific_pain": "Small HR team, specialized compliance requirements, paper-based",
    },
}

TARGET_STATES = ["TX", "FL", "GA", "NC", "OH", "TN", "AZ", "CO", "VA", "SC"]

# Government-specific procurement vehicles (useful for sales context)
PROCUREMENT_VEHICLES = [
    "NASPO", "TIPS", "SOURCEWELL", "E&I Cooperative",
    "DIR (Texas)", "WSCA-NASPO", "state contract vehicle",
]
