"""Education vertical — ICP config and query banks.

Targets: K-12 school districts, charter school networks, Head Start programs,
community colleges, vocational schools.

Key insight: K-12 school districts have the highest hit rate for paper new hire
packets. State k12.XX.us domains frequently host PDFs publicly. August is the
highest-signal month — massive hiring surge with paper process breakdowns.
"""
from __future__ import annotations

# Query bank for DDG signal discovery
DISCOVERY_QUERIES = [
    # Manual onboarding PDFs — K-12 districts are excellent sources
    'site:{domain} filetype:pdf "new hire" OR "new employee" packet',
    'site:k12.{state_lower}.us "{company}" filetype:pdf "new hire" packet',
    '"{company}" school district "new hire packet" filetype:pdf',
    '"{company}" "new employee orientation" forms packet {state}',

    # ADP confirmation
    '"{company}" "ADP WorkforceNow" OR "ADP Run" school district',
    'site:{domain} "workforcenow.adp.com" payroll',

    # Job postings
    'site:indeed.com "{company}" "HR" school district "paper" OR "manual" OR "spreadsheet"',
    'site:edjoin.org "{company}" human resources coordinator',

    # NCES data
    'site:nces.ed.gov "{company}" district enrollment',
    'site:nces.ed.gov school district {state} "{company}"',

    # Grant/funding triggers
    '"{company}" "ESSER" OR "Title I" OR "Head Start" grant 2024 2025',
    '"{company}" school district grant award federal funding',

    # Growth/expansion
    '"{company}" school district "new school" OR "opening" {state} 2024 2025',
]

# ICP targeting parameters
ICP_CONFIG = {
    "vertical": "education",
    "sweet_spot_employee_ranges": ["100-249", "250-499", "500-999"],
    "min_employees": 50,
    "max_employees": 5000,  # Large districts are still valid targets
    "multi_location_required": True,
    "frontline_workforce": False,
    "us_only": True,
}

# Education sub-verticals
SUB_VERTICALS = {
    "k12_district": {
        "description": "Traditional K-12 school district (ISD, USD, CSD, CUSD)",
        "key_signal": "pdf_new_hire_packet",
        "best_product": "Onboard",
        "specific_pain": "August hiring surge — 50-300 staff in 3 weeks with paper packets",
        "domain_pattern": r"\.k12\.[a-z]{2}\.us$",
    },
    "charter_network": {
        "description": "Charter school network (2+ schools)",
        "key_signal": "seasonal_hiring",
        "best_product": "Onboard",
        "specific_pain": "Multiple campuses, no centralized onboarding system",
        "domain_pattern": r"",
    },
    "head_start": {
        "description": "Head Start and Early Head Start programs",
        "key_signal": "grant_award",
        "best_product": "Onboard",
        "specific_pain": "HHS grant compliance requires documented onboarding",
        "domain_pattern": r"",
    },
    "community_college": {
        "description": "Community and junior colleges",
        "key_signal": "job_manual_task",
        "best_product": "Onboard",
        "specific_pain": "Adjunct faculty onboarding volume with paper-heavy credentialing",
        "domain_pattern": r"",
    },
}

# States with highest K-12 district density and paper onboarding evidence
TARGET_STATES = ["TX", "FL", "CA", "OH", "PA", "IL", "NY", "NC", "GA", "MI",
                 "AZ", "CO", "WA", "TN", "MO", "IN", "WI", "MN", "VA", "NJ"]

# Useful DDG operators for education discovery
DOMAIN_SUFFIXES = [
    ".k12.tx.us", ".k12.fl.us", ".k12.ca.us", ".k12.oh.us", ".k12.pa.us",
    ".k12.il.us", ".k12.ny.us", ".k12.nc.us", ".k12.ga.us", ".k12.mi.us",
]
