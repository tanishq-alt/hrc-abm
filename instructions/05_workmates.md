# Instruction Guide: Prompt 5 — Workmates Frontline Communication

## What Workmates Is

HR Cloud Workmates is a frontline employee communication and engagement platform. It enables:
- Targeted announcements by location, role, shift, or department
- Mandatory-read flows with tracked acknowledgment
- Peer-to-peer and manager recognition
- Two-way communication between HQ and field employees
- Mobile-first delivery — no corporate email required

## Structural Fit Criteria

An organization is a strong Workmates prospect if it has ALL of these:

1. 100+ employees total
2. 50%+ of workforce is frontline, hourly, or deskless
3. Operations across multiple locations, shifts, or sites
4. No current digital channel that reaches field/frontline staff

High-fit industries: Home health, senior living, manufacturing, retail chains, distribution, hospitality, franchise networks, construction with field staff.

## Intent Signal Hierarchy

| Priority | Signal | Why It Matters |
|----------|--------|----------------|
| 1 | ADP user + multi-location + frontline | ADP does not have a Workmates equivalent — easiest cross-sell |
| 2 | Internal comms manager job posting | Someone is budgeted to solve this right now |
| 3 | Policy acknowledgment + distributed employees | Pain is documented and compliance-driven |
| 4 | Caregiver retention + communication initiative | Urgency is financial (turnover cost) |
| 5 | Employee app evaluation or RFP | Active shopping — respond immediately |

## How to Run

```bash
cd /Users/tanishqmac/hr-intel-toolkit
python3 -u scrapers/p05_workmates/workmates_finder.py 2>&1 | tee /tmp/p05_workmates.log
```

Output: `data/workmates_leads.csv`

## Combining With Other Prompts

Workmates leads are often also Onboard leads. A company that is:
- Multi-location + ADP user + paper onboarding = **Onboard + Workmates** opportunity

Always check Prompt 1 and Prompt 3 results for overlap before outreach.

## Outreach Examples

**Opening line (internal comms role):**
"I saw you're hiring an Internal Communications Manager — HR Cloud Workmates gives your team the platform to reach every frontline employee on day one, no corporate email needed."

**Opening line (caregiver retention):**
"Caregiver turnover is a $15K-per-person problem. One of the top drivers is feeling disconnected from the organization — Workmates fixes that for your field staff."

**Opening line (ADP cross-sell):**
"You're on ADP Workforce Now for payroll. HR Cloud Workmates adds the frontline communication layer ADP doesn't have — targeted announcements, mandatory reads, peer recognition."

## Recommended Buyer Titles

- Chief People Officer / CHRO
- VP of Human Resources
- Director of Internal Communications
- Director of Employee Engagement
- SVP Operations (when HR is ops-led)
- Chief Nursing Officer (senior care)
- VP Field Operations (logistics, home health)
