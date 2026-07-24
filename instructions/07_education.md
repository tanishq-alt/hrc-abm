# Instruction Guide: Prompt 7 — Education

## Why Education Is a Strong HR Cloud Vertical

Education organizations have several structural advantages for HR Cloud:

- **Predictable seasonal buying**: Onboarding decisions happen in April-July for fall terms
- **Paper-heavy new hire packets**: K-12 districts, especially in smaller states, still host paper packets on their district websites
- **Credential complexity**: Teacher certification, background check, fingerprint clearance — all complex and often manual
- **ADP penetration**: Many districts use ADP Run or Workforce Now but lack onboarding automation
- **Substitute teacher volume**: Continuous, high-volume hiring with no onboarding system

## Priority Segments

1. **Public K-12 school districts (500–10,000 employees)**: Largest segment, board procurement, summer urgency window
2. **Charter school networks (5–50 campuses)**: Growing fast, often under-resourced HR, multi-site Workmates opportunity
3. **Head Start programs**: Federal compliance requirements, high turnover, paper-heavy
4. **Community colleges**: Adjunct instructor volume hiring, credential verification burden
5. **Private K-12 schools**: Often use ADP Run, no HRIS, paper packets common

## Seasonal Timing Rules

The education buying calendar is highly predictable. Plan outreach accordingly:

| Time Period | What Happens | Outreach Focus |
|-------------|-------------|----------------|
| March–April | Budgets set, evaluations begin | Plant seeds, request demos |
| May–June | Decisions finalized, contracts signed | Urgency plays, board approval |
| July–August | Massive onboarding surge for fall | Emergency response — "you need this now" |
| September–October | Post-term retrospective | Set up for spring planning |
| November–December | Budget planning for next year | "For next year" conversations |
| January–February | Spring hiring surge | Same urgency as July-August |

## Official Data Sources

```bash
# NCES Common Core of Data (CCD) — public K-12 universe
# Get district name, enrollment, teacher count, state
# URL: https://nces.ed.gov/ccd/districtsearch/

# Head Start Center Locator — all Head Start grantees
# URL: https://eclkc.ohs.acf.hhs.gov/center-locator

# NCES Private School Universe Survey
# URL: https://nces.ed.gov/surveys/pss/

# State Dept of Education teacher certification databases
# (state-specific URLs — search "[state] teacher certification lookup")
```

## How to Run

```bash
cd /Users/tanishqmac/hr-intel-toolkit
python3 -u scrapers/p07_education/education_finder.py 2>&1 | tee /tmp/p07_education.log
```

Output: `data/education_leads.csv`

## Finding Paper Packets on K-12 Domains

The most reliable signal in education is a new hire packet PDF hosted on the district's `.k12.[state].us` domain.

Run these queries directly for highest yield:
```
"new hire packet" site:.k12.tx.us filetype:pdf
"new hire packet" site:.k12.fl.us filetype:pdf
"new hire packet" site:.k12.ca.us filetype:pdf
"new hire packet" site:.k12.ga.us filetype:pdf
"new hire packet" site:.k12.nc.us filetype:pdf
```

Each result that links to a PDF on a district domain is a near-certain prospect. The existence of the packet proves paper-based onboarding.

## Entity and Buying Authority

Education has the most complex buying authority. Always resolve correctly:

- **District**: Superintendent approves, HR Director evaluates, Business Administrator signs contract
- **Charter network**: Chief of Staff or COO at the network level — not individual campus principals
- **Head Start**: Executive Director of the grantee organization (often a nonprofit)
- **Community college**: VP of Administration or HR Director — not department chairs

Never reach out to individual school principals for district-wide deals. Always go to district HR.

## ADP Cross-Sell in Education

Many districts run ADP Workforce Now or ADP Run for payroll. These are ideal targets because:
- ADP doesn't provide teacher credentialing workflows
- ADP doesn't provide a substitute teacher onboarding module
- ADP doesn't have a district-wide communication platform for staff

Query to find ADP education users:
```
"ADP Workforce Now" "school district" HR coordinator job
"ADP Run" "school district" payroll HR
```

## Outreach Examples

**District with paper packet:**
"Your new hire packet is still a PDF on your district website. HR Cloud Onboard moves that to a mobile-first link your new teachers complete before their first day — no paper, no HR appointments."

**Substitute teacher volume:**
"You're hiring substitute teachers continuously all year. HR Cloud Onboard gets them onboarded, fingerprint-cleared, and credentialed in one workflow — before they set foot in a classroom."

**Back-to-school urgency:**
"August is your highest-volume onboarding month. HR Cloud can cut your new teacher onboarding from 3 days to 20 minutes — for every hire, every building."

**ESSER funding:**
"ESSER III is driving new hires in districts across [state]. Make sure your onboarding process is ready before the surge hits."
