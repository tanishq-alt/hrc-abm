# RFP/RFQ Scanner — Complete Guide

## Why RFPs Are the Highest-Intent Signal Possible

An organization that has published an RFP for HR software has:
1. ✅ Budget approved
2. ✅ Decision made to buy
3. ✅ Timeline established
4. ✅ Stakeholder alignment done
5. ✅ Published contact information for the procurement officer

This is as close to a guaranteed sale as you get in B2B. The only question is whether you respond in time.

---

## Where Government RFPs Are Published

| Source | URL | Who Posts |
|--------|-----|-----------|
| SAM.gov | sam.gov/search | Federal agencies |
| State procurement portals | See list below | State agencies |
| BidNet | bidnet.com | Counties, municipalities, schools |
| DemandStar | demandstar.com | Local governments |
| Public Purchase | publicpurchase.com | Schools, cities |
| Periscope S1 | bidding.co | Texas, other states |
| OpenGov | opengov.com/procurement | Progressive municipalities |

### State-Specific Portals
- Texas: esbd.cpa.texas.gov
- California: caleprocure.ca.gov
- Florida: myfloridamarketplace.com
- Georgia: doas.ga.gov/state-purchasing
- New York: ogs.ny.gov/procurement
- Ohio: procure.ohio.gov
- Pennsylvania: emarketplace.state.pa.us

---

## What to Search For

```
"request for proposal" "HRIS" site:.gov 2025
"RFP" "human resources system" "school district" 2025
"request for proposal" "payroll" site:.gov 2025
"RFP" "onboarding" OR "HR software" 2025
"invitation to bid" "HRIS" OR "workforce management" 2025
site:sam.gov "human resources" "HRIS" 2025
site:bidnet.com "HR software" OR "payroll" 2025
```

---

## Reading an RFP — Key Fields to Extract

When you find an RFP, extract:
1. **Organization name** + contact name/email of procurement officer
2. **RFP number** (e.g., "RFP 2025-HR-001")
3. **Submission deadline** — you must respond before this date
4. **Scope of work** — exactly what system they want
5. **Incumbent vendor** — sometimes listed, sometimes you can infer ("replace existing system")
6. **Evaluation criteria** — price vs. features weighting
7. **Contract term** — 1 year? 3 years? (affects deal size)

---

## Response Strategy

### Option A: Submit a Vendor Response
If your product qualifies and the RFP allows it, submit a formal proposal. Government contracts are large ($50K–$500K) and multi-year.

### Option B: Outreach to Procurement Contact
For smaller orgs (school districts, counties), email the procurement officer directly:
> "We noticed your RFP [number] for HRIS/onboarding software. We've implemented similar systems for [3 similar orgs]. I'd love to send you a response package and schedule a demo before [deadline]."

### Option C: Pre-RFP Outreach (Best)
Find organizations **before** they publish an RFP by looking for:
- Budget approval announcements
- "We're evaluating HR software" social posts
- Old RFPs that are about to expire (3–5 year contracts)
- New leadership (new HR Director, new superintendent)

---

## Running the Scraper

```bash
python3 -u scrapers/rfp_rfq/rfp_finder.py 2>&1 | tee /tmp/rfp_finder.log &
tail -f /tmp/rfp_finder.log
```

Output: `data/rfp_rfq_leads.csv`

---

## Setting Up Automated RFP Alerts

Set up Google Alerts for:
- `"request for proposal" "HRIS" OR "HR software"`
- `"RFP" "onboarding software" filetype:pdf`
- `site:sam.gov "human resources" "software"`

Check weekly. RFPs move fast — deadline is often 3–6 weeks after posting.
