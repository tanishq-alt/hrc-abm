"""Healthcare vertical — ICP config and query banks.

Targets: Home health agencies, hospice, SNF, ALF, behavioral health,
substance abuse treatment, adult day programs, personal care agencies.

Key insight: Healthcare has the highest density of paper onboarding evidence
because caregivers must complete state-mandated paper forms (CPR cards, TB tests,
I-9s) and companies often host these as PDFs on their public websites.
"""
from __future__ import annotations

# Query bank for DDG signal discovery
DISCOVERY_QUERIES = [
    # Manual onboarding PDFs
    'site:{domain} filetype:pdf "new hire" caregiver packet',
    'site:{domain} "new caregiver packet" OR "new employee packet" filetype:pdf',
    '"{company}" "caregiver new hire packet" filetype:pdf {state}',
    '"{company}" home health "new employee orientation" paper forms',

    # ADP confirmation
    '"{company}" "ADP WorkforceNow" OR "ADP payroll" home health',
    'site:{domain} "workforcenow.adp.com" OR "adp.com/workforce"',

    # Job postings with manual tasks
    'site:indeed.com "{company}" HR "paper files" OR "manual entry" OR "spreadsheet"',
    'site:indeed.com "{company}" payroll "ADP" experience required',

    # CMS/regulatory
    '"{company}" CMS deficiency survey {state}',
    '"{company}" Medicare survey citation findings',

    # Growth/expansion
    '"{company}" "new location" OR "opens" home health {state} 2024 2025',
    '"{company}" acquisition merger home health agency',
]

# ICP targeting parameters
ICP_CONFIG = {
    "vertical": "healthcare",
    "sweet_spot_employee_ranges": ["100-249", "250-499", "500-999"],
    "min_employees": 50,
    "max_employees": 2000,
    "multi_location_required": True,
    "frontline_workforce": True,
    "us_only": True,
}

# Healthcare sub-verticals with specific nuances
SUB_VERTICALS = {
    "home_health": {
        "description": "Home health and personal care agencies",
        "key_signal": "caregiver_hiring_surge",
        "best_product": "Onboard",
        "specific_pain": "Caregiver onboarding packet is paper — takes 2-3 weeks to complete",
        "npi_taxonomy": "251E00000X",  # Home Health Agency NPI
    },
    "hospice": {
        "description": "Hospice and palliative care providers",
        "key_signal": "pdf_new_hire_packet",
        "best_product": "Onboard",
        "specific_pain": "Interdisciplinary team onboarding with paper credentialing",
        "npi_taxonomy": "251G00000X",
    },
    "snf_alf": {
        "description": "Skilled nursing and assisted living facilities",
        "key_signal": "cms_deficiency",
        "best_product": "Onboard+Workmates",
        "specific_pain": "CMS survey documentation gaps + frontline communication",
        "npi_taxonomy": "314000000X",
    },
    "behavioral_health": {
        "description": "Mental health, substance abuse, behavioral health",
        "key_signal": "credential_complexity",
        "best_product": "Onboard",
        "specific_pain": "Counselor credentialing and licensure onboarding is complex and paper-heavy",
        "npi_taxonomy": "261QM0801X",
    },
}

# State-specific query modifiers (states with highest healthcare density)
TARGET_STATES = ["TX", "FL", "CA", "OH", "PA", "IL", "NY", "NC", "GA", "MI"]

# Disqualifying indicators for healthcare accounts
DISQUALIFIERS = [
    "workforce management system implemented",
    "using workday",
    "using dayforce",
    "using ukg",
    "fully automated onboarding",
]
