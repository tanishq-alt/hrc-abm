# Manual Onboarding Discovery — Complete Guide

## What We're Finding

Companies that still onboard new employees using physical paper packets, fax forms, printed I-9/W-4/direct deposit forms, or in-person HR day-one paperwork. These are companies that have **never digitized** their onboarding process — highest-intent prospects for any onboarding software.

---

## The Gold Standard Signal

A company hosting a PDF new hire packet at a public URL like:
- `company.org/hr/new-hire-packet.pdf`
- `district.k12.tx.us/cms/new_employee_forms.pdf`
- `cityof.gov/DocumentCenter/View/1234/New-Hire-Paperwork`

This is **undeniable evidence** — no HR tech company would host a paper packet publicly unless they're still using it.

---

## Best Query Formats

```
"new hire packet" filetype:pdf site:.k12.tx.us
"new employee packet" "school district" filetype:pdf
"new hire packet" "health system" filetype:pdf site:.org
"new hire packet" "county" filetype:pdf site:.gov
"new hire forms" "complete and return" filetype:pdf
"caregiver new hire packet" filetype:pdf site:.com
"new hire packet" "diocese" OR "archdiocese" filetype:pdf
```

The `filetype:pdf` operator is the single most important filter. It surfaces **actual documents**, not blog posts about best practices.

---

## Best Target Verticals (Ranked by Hit Rate)

| Vertical | Why They're Ideal | Query Pattern |
|----------|------------------|---------------|
| K12 School Districts | Public HR, .k12.XX.us domains, always paper | `site:.k12.tx.us filetype:pdf "new hire"` |
| Community Colleges | HR pages public, .edu domains, regional | `"new hire packet" "community college" filetype:pdf` |
| County/City Government | DocumentCenter, public HR docs | `site:.gov "new hire packet" filetype:pdf` |
| Home Care Agencies | Caregiver turnover → constant new hires | `"caregiver new hire packet" filetype:pdf` |
| Faith-Based Orgs | Diocese/church, no IT dept, always paper | `"new hire packet" "diocese" filetype:pdf` |
| Small Hospitals | Critical access, rural, under-resourced | `"new hire packet" "critical access hospital" filetype:pdf` |
| Nonprofits (.org) | Small teams, no HR tech budget until pain | `"new hire packet" site:.org filetype:pdf` |

---

## Signal Types

| Signal Type | Description | Confidence |
|-------------|-------------|------------|
| `paper_packets` | Hosts PDF new hire packet publicly | High |
| `fax_mail` | "Fax completed forms to HR" | High |
| `physical_files` | "Bring documents to HR office on day one" | High |
| `in_person_paperwork` | "Complete paperwork at orientation" | High |
| `manual_data_entry` | Job post: "enter new hire data into payroll" | Medium |

---

## Critical Filters (What to Exclude)

### Patient paperwork (false positives in healthcare)
Many clinic sites say "bring completed paperwork to your appointment" — this is for patients, not employees. Check for `employee|HR|new hire` context words before counting as a lead.

### CDN domains (garbled company names)
Skip: `s3.amazonaws.com`, `hubspotusercontent`, `static1.squarespace.com`, `uploads-ssl.webflow.com`, `wixsite.com` — these host PDFs for unknown companies.

### Vendor/competitor content
Skip if evidence quote contains: `bamboohr`, `gusto`, `rippling`, `workday`, `adp.com` — the page is about HR software, not using paper.

### Non-US sources
Skip if URL contains: `.co.uk`, `.ca`, `.au`, `.nz`, `.ie`, `.in`, `africa`, `ajiriwa`, `dohaj`

---

## Running the Scrapers

```bash
# Batch 1 — original 72 queries (broader)
python3 -u scrapers/manual_onboarding/nano_batch1.py 2>&1 | tee /tmp/batch1.log &

# Batch 2 — 86 queries, expanded industries
python3 -u scrapers/manual_onboarding/nano_batch2.py 2>&1 | tee /tmp/batch2.log &

# Batch 3 — 147 hyper-targeted queries (K12 by state, home care by state, etc.)
python3 -u scrapers/manual_onboarding/nano_batch3.py 2>&1 | tee /tmp/batch3.log &

# Merge all batches → MASTER.csv
python3 pipeline/build_master.py
```

---

## DDG Rate Limiting — What Works

- **4-second delay** between every query
- **Exponential backoff**: `20 * attempt` seconds on rate limit hit
- **4 retries** per query before skipping
- **`python3 -u`** flag for unbuffered output (otherwise logs appear empty)
- **Checkpoint saves** every 20 queries
- Run as background process: `python3 -u script.py 2>&1 | tee /tmp/log.txt &`

---

## Outreach Angles by Signal

| Signal | Opening Line |
|--------|-------------|
| PDF new hire packet hosted publicly | "I came across your new hire packet on your HR page — impressive that your team handles onboarding in-house. Many teams like yours are moving this process digital to save 3–4 hours per new hire." |
| Fax forms | "Saw your onboarding process still uses fax for new hire forms — we help HR teams go fully digital in under a week." |
| Job post: "prepare new hire packets" | "Saw you're hiring an HR coordinator to prepare new hire packets — we automate that entire process so your new HR person can focus on culture, not paperwork." |
| School district | "Your district processes a lot of new staff every semester — we work with 50+ school districts to cut paper onboarding from 2 days to 15 minutes." |
