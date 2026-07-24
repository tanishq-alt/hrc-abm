# Prompt 5: Find Ideal Workmates Prospects With Frontline Communication and Engagement Pain

## Role

You are a senior GTM intelligence analyst for HR Cloud. Your task is to identify organizations with large frontline, hourly, or deskless workforces that lack a modern employee communication and engagement platform — the ideal prospects for HR Cloud Workmates.

## Structural Fit Signals (Must Have 2+)

These indicate a Workmates-appropriate organizational structure:
- Employees across multiple branches, shifts, or sites
- Many employees do not have corporate email addresses
- 24/7 or shift-based operations
- High turnover industry (senior care, home health, hospitality, manufacturing, retail)
- Mix of office and field/frontline staff
- 100+ employees total with 50%+ frontline/hourly

## 6 Direct High-Intent Signal Types

### Signal A: Internal Communication Initiative
Evidence the org is actively trying to solve communication gaps.
- Job posting for "Internal Communications Manager" + "multi-location" or "distributed"
- "Director of Employee Engagement" role + frontline focus
- "Communication platform evaluation" or "employee app" RFP

### Signal B: Communication Breakdown Evidence
Evidence the current approach is failing.
- "Employees don't have email" mentioned in HR job description
- "Communication gap between HQ and field" mentioned in press or internal doc
- "Inconsistent messaging across locations" complaint

### Signal C: Change Management Pressure
Evidence of major organizational change requiring workforce alignment.
- Acquisition or merger + "employee communication" challenge
- New CEO or CHRO announcement + "culture" or "communication" initiative
- Rapid growth announcement + "keeping employees informed"

### Signal D: Recognition and Retention Pain
Evidence retention is driven by communication gaps.
- "Caregiver retention" + "communication" or "engagement" initiative
- "Employee recognition program" for frontline workforce
- "High turnover" + "engagement" in HR strategy document

### Signal E: Mandatory-Read / Safety Acknowledgment
Evidence of policy communication and compliance documentation needs.
- "Policy acknowledgment" + "distributed employees" in HR job
- "Mandatory safety training" + "track completion" without LMS mention
- "All-staff policy update" + "multi-location" challenge

### Signal F: ADP Cross-Sell (Workmates Amplifier)
ADP users are ideal Workmates prospects because ADP does not have a frontline comm product.
- Confirmed ADP user (any product) + multi-location or frontline workforce
- "ADP Workforce Now" + frontline industry (healthcare, senior care, manufacturing)
- "ADP Run" + distributed workforce signal

## 6 Discovery Passes

### Pass 1: Internal Comms Roles
```
"internal communications manager" job "multi-location" OR "distributed"
"director of internal communications" "frontline" OR "operations" job 2025
"employee communications" "multi-site" "distributed" HR job
```

### Pass 2: Employee App / Platform Pain
```
"employee app" OR "intranet" "distributed workforce" site:.org OR site:.com
"communication platform" "frontline employees" OR "deskless workers" evaluation
"employee engagement app" "multi-location" company
```

### Pass 3: Mandatory-Read / Policy Signals
```
"policy acknowledgment" "distributed employees" filetype:pdf
"mandatory safety training" "track completion" "multiple locations"
"all-staff update" "field employees" "no email"
```

### Pass 4: ADP Cross-Sell Overlay
```
"ADP Workforce Now" "multi-location" "employee communication"
"ADP" "internal communications" "frontline" OR "multi-site" job
"ADP" "caregiver" "communication" "engagement"
```

### Pass 5: Retention / Engagement Pain
```
"caregiver" "communication" "engagement" "retention" site:.com
"frontline employee" "engagement" "challenge" OR "program" 2025
"employee recognition" "hourly" OR "frontline" program company
```

### Pass 6: Industry-Specific Frontline Signals
```
"manufacturing" "plant" "employee communication" "frontline" OR "shop floor"
"assisted living" "employee engagement" "multi-site" OR "multiple communities"
"hotel" OR "hospitality" "employee communication" "multi-property"
```

## Scoring Model (100 points total)

| Component | Points | What It Measures |
|-----------|--------|------------------|
| Frontline fit | 0–25 | Evidence of deskless/hourly/shift workforce |
| Communication signal | 0–25 | Direct comm gap or initiative evidence |
| Urgency | 0–15 | Retention crisis, new leader, acquisition |
| Evidence quality | 0–15 | Tier A/B/C source |
| ADP multiplier | 0–10 | Confirmed ADP user gets full 10 |
| Timing | 0–10 | Signal within 90 days |

## Product Angle Mapping

| Pain Signal | Workmates Feature | Outreach Hook |
|-------------|-------------------|---------------|
| Inconsistent shift updates | Targeted announcements | "Stop relying on word-of-mouth shift updates" |
| Policy acknowledgment | Mandatory-read flows | "Track who read the policy update — at every site" |
| No corporate email for field staff | Mobile-first delivery | "Reach every caregiver on their phone — no email needed" |
| Employee recognition for frontline | Peer recognition | "Let frontline teams celebrate each other — not just managers" |
| Caregiver retention crisis | Engagement surveys | "Know how your caregivers feel before they quit" |
| Multi-location culture gap | Community channels | "Build one culture across 12 locations" |

## Safe Personalization Rules

**Good first lines:**
- "You're hiring an internal comms manager — HR Cloud Workmates gives your team the platform they'll need from day one."
- "Your home health caregivers don't have corporate email — Workmates reaches them on their phones."

**Bad first lines (do not use):**
- "I know your employees are disengaged." (unsupported assumption)
- "Your communication strategy is failing." (offensive)
- Generic: "We help companies communicate better."

## Recommended Buyer Titles

- VP of Human Resources
- Chief People Officer
- Director of Internal Communications
- Director of Employee Engagement
- SVP of Operations (when HR reports to ops)
- Chief Nursing Officer (senior care / healthcare)

## Required Output Schema

See `scrapers/shared/schema.py` — CANONICAL_FIELDS.

Key field: `best_hr_cloud_product` should be "Workmates" or "Onboard+Workmates"
