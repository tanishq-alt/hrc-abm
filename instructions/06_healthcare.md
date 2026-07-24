# Instruction Guide: Prompt 6 — Healthcare and Senior Care

## Why Healthcare Is HR Cloud's Best Vertical

Healthcare and senior care organizations have the highest density of HR Cloud fit signals:

- **Paper-heavy onboarding**: Most home health agencies and senior living communities still use paper new hire packets
- **Credential complexity**: CNA license tracking, nurse aide registry checks, OIG screening — all manual at most orgs
- **CMS oversight**: Staffing documentation deficiencies are common CMS survey findings
- **High caregiver turnover**: 60–80% annual turnover creates continuous onboarding pressure
- **Multi-site operations**: Most home health and senior living orgs operate multiple locations
- **No corporate email for caregivers**: Frontline caregivers don't have company email — Workmates is the solution

## Priority Segments

1. **Home health agencies (50–500 employees)**: Highest hit rate for paper new hire packets. Use `"new hire packet" filetype:pdf "home health"` as your first query.
2. **Hospice organizations**: Similar profile to home health. Often paper-heavy.
3. **Assisted living / senior living chains**: Multi-site, CMS-regulated, ADP common.
4. **Behavioral health**: Rapid expansion phase, licensing complexity, often first formal HR.
5. **Multi-site medical groups**: Credential verification automation is the key use case.

## Official Data Sources to Use

```bash
# CMS Home Health Compare — get list of all home health agencies
# Filter by state, then search for their domain + "new hire packet"
# URL: https://data.cms.gov/provider-data/dataset/6jpm-sxkc

# CMS Nursing Home Data — get staffing scores and deficiency flags
# Low staffing score = onboarding pain signal
# URL: https://data.cms.gov/provider-data/dataset/4pq5-n9py

# NPPES NPI Registry — find healthcare orgs with 5+ locations
# Search by organization_type + NPI count
# URL: https://npiregistry.cms.hhs.gov/
```

## How to Run

```bash
cd /Users/tanishqmac/hr-intel-toolkit
python3 -u scrapers/p06_healthcare/healthcare_finder.py 2>&1 | tee /tmp/p06_healthcare.log
```

Output: `data/healthcare_leads.csv`

## Entity Resolution (Critical)

Always resolve to the correct billing/contracting entity:

- A "Golden Years Memory Care" location is likely operated by "Golden Years Senior Living LLC"
- Target the LLC/management company — they make the HR buying decision
- PE-backed chains: contact the PE portfolio company HR team AND the PE firm's operating partner

## ADP Cross-Sell Priority

Home health and senior living organizations that use ADP are top-priority targets because:
1. ADP Workforce Now has poor onboarding features for mobile/frontline staff
2. ADP has no frontline communication product (no Workmates equivalent)
3. ADP users are familiar with monthly SaaS payroll costs — pricing conversation is easy

Query to find ADP healthcare users:
```
"ADP Workforce Now" "home health" OR "senior living" HR coordinator job
```

## CMS Deficiency Signal

When a home health or senior living organization has a CMS staffing deficiency citation:
- They are under pressure to improve documentation
- HR director is likely already aware of the problem
- Outreach: "CMS surveys increasingly cite staffing documentation — HR Cloud creates an audit-ready digital record for every new hire."

Find deficiency data at: https://medicare.gov/care-compare

## Outreach Examples

**Home health agency (paper packet):**
"Your caregiver new hire packet is still a PDF on your website. HR Cloud Onboard moves that entire process to a mobile link your new hires complete on their phone — before their first shift."

**Senior living (ADP cross-sell):**
"You're running [X] communities on ADP Workforce Now. HR Cloud adds the digital onboarding and caregiver communication layer ADP doesn't have."

**PE acquisition:**
"Just saw [PE Firm] acquired [Company]. Most PE-backed senior living roll-ups standardize HR processes in the first 90 days — HR Cloud is built for that."
