# ADP Confirmed Users — Complete Guide

## Why ADP Users Are High-Intent Leads

ADP users are confirmed **HR system owners** with budget, an established HR workflow, and a pain point: ADP is complex, expensive, and notorious for poor UX — especially for small/mid-market teams. They're not starting from zero; they're ready to switch or supplement.

**Key insight**: A job posting that says "experience with ADP Workforce Now required" is a signed confession that they run payroll and HR on ADP today.

---

## ADP Product Tiers (Helps with Sizing)

| Product | Company Size | Notes |
|---------|-------------|-------|
| ADP Run | 1–49 employees | Small business payroll, highest churn |
| ADP Workforce Now | 50–1,000 employees | Mid-market, most common in job posts |
| ADP TotalSource | 10–500 employees | PEO model, ADP acts as co-employer |
| ADP Vantage HCM | 1,000+ employees | Enterprise, less likely to switch |

**Best targets**: ADP Run and ADP Workforce Now users. They have the most pain and the most to gain.

---

## Signal Sources

### 1. Job Postings (Highest Signal)
Search: `"ADP Workforce Now" "HR coordinator" job`

What to look for in the job description:
- "Experience with ADP Workforce Now required"
- "Process new hire paperwork in ADP"
- "Enter employee data into ADP"
- "Run payroll using ADP"
- "Maintain ADP records"

**Why this works**: Companies only put ADP in the job description if their current employees actually use it daily. This is a live, named-incumbent signal.

### 2. Company Website Mentions
Some companies list their tech stack in About/Careers pages. Search: `"we use ADP" OR "powered by ADP" site:companyname.com`

### 3. Switching Signals
Search: `"switching from ADP" OR "replacing ADP" HR software`

These are companies already in evaluation mode — **highest urgency**, reach out immediately.

### 4. G2/Capterra Reviews
ADP Workforce Now has 6,000+ reviews on G2. Filter by negative reviews mentioning manual processes, paper workflows, or poor UX. The reviewer's company is a named ADP user.

---

## Best Query Patterns

```
"ADP Workforce Now" "HR coordinator" job -site:adp.com
"ADP Run" "payroll" "small business" job
"experience with ADP" "HR" OR "payroll" job
"process payroll" "ADP" HR manager job posting
"enter new hires" "ADP" HR job
"ADP Workforce Now" "school district" HR
"ADP" "payroll" "healthcare" "HR coordinator" job
"switching from ADP" HR software
"replacing ADP" HRIS
```

---

## Outreach Strategy

### For Job Posting Signal
> "Saw you're hiring an HR coordinator familiar with ADP Workforce Now — that tells me your team runs payroll and onboarding there today. Many companies your size use [Product] alongside ADP to eliminate the manual data entry and paper new hire packets. Worth a 15-minute call to show you how?"

### For Switching Signal
> "Came across your post about replacing ADP — you're in the right place. Most teams switching from ADP come to us because [specific pain point]. We can have you live in a week. Want to see a demo tailored to your exact use case?"

### For Size-Matched Pitch
- **ADP Run users** (< 50 employees): Lead with simplicity and price vs. ADP
- **ADP Workforce Now users** (50–500): Lead with automation, less manual entry, better UX
- **ADP TotalSource users**: Lead with flexibility and ownership of your own HR data

---

## Running the Scraper

```bash
python3 -u scrapers/adp_confirmed/adp_finder.py 2>&1 | tee /tmp/adp_finder.log &
tail -f /tmp/adp_finder.log
```

Output: `data/adp_confirmed_leads.csv`
