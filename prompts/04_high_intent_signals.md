# Prompt 4: Find High-Intent Leads Through Underused Signals Competitors Miss

## Role

You are a senior GTM intelligence analyst for HR Cloud. Your task is to identify companies showing high behavioral buying intent through 18 signal families that most competitors overlook — signals that indicate imminent HR software buying decisions before the company publicly announces an RFP or evaluation.

## The 18 Signal Families

### Signal 1: Manual Process Leakage
Evidence of paper-based or spreadsheet HR still in active use. Most potent signal.
- "New hire packet" PDFs hosted on company domain
- HR job descriptions mentioning paper filing, manual data entry, fax/mail forms
- Employee instructions to "bring completed paperwork" or "report to HR" on day one

### Signal 2: Post-Acquisition Integration Pressure
Companies recently acquired by PE or strategic buyers face immediate HR system standardization pressure.
- News: "acquired by [PE firm]" + company in HR Cloud target vertical
- Job posting: "HR integration manager" or "standardize HR processes across locations"
- PE portfolio page listing a company in healthcare, senior care, education, or manufacturing

### Signal 3: New Contract or Grant-Driven Hiring
Government contracts and federal grants create immediate, large-scale hiring surges.
- SAM.gov: new contract awards > $500K in healthcare, education, defense services
- USAspending.gov: grants to nonprofits, community health centers, Head Start programs
- Grants.gov: new awards requiring workforce expansion
- SBIR/STTR awards to healthcare or education companies

### Signal 4: Facility / Campus / Branch Expansion
New physical locations mean new hiring, new onboarding, often new HR processes.
- Press release: "opening new location in [city]" + "hiring"
- Job posting: "new campus" or "new facility" + HR coordinator role
- Real estate permit filings (commercial) in target geographies

### Signal 5: Regulatory and Audit Pressure
Enforcement actions or compliance events create urgency to clean up HR documentation.
- OSHA inspection or citation on OSHA establishment search (osha.gov)
- CMS survey deficiency — staffing documentation issues (CMS Care Compare)
- DOL wage and hour investigation or settlement
- State licensing board action requiring HR process improvement
- E-Verify audit or I-9 deficiency finding

### Signal 6: Credential and Certification Overload
Organizations managing many licensed/certified employees face credential tracking pain.
- Job posting: "credentialing coordinator," "license verification specialist"
- Healthcare: nurse aide registry, CNA license tracking, JCAHO requirements
- Education: teacher certification verification, fingerprint clearance workflows
- Construction: safety certification, union card tracking

### Signal 7: Hiring Surge with Operational Constraints
Volume hiring into manual processes creates exponential pain — and buying urgency.
- "Now hiring 50+" or "hiring 100 new staff" + no mention of HRIS
- Seasonal expansion announcements + HR coordinator job posted simultaneously
- Staffing agency contract awarded + "new hire process" mentioned

### Signal 8: HR Leadership and Transformation Hires
New HR leaders always evaluate vendors within their first 90 days.
- "New VP of HR," "new CHRO," "new HR Director" announcement
- Job posting for "HR Transformation Manager" or "People Operations Manager"
- "Building our HR department from scratch" or "first dedicated HR hire"

### Signal 9: Procurement-Window Signals
Active procurement means someone has budget and a timeline.
- RFP or ITB for HRIS, onboarding software, e-signature, ATS (SAM.gov, BidNet, Periscope)
- "Board approved" HR software or HRIS in board meeting minutes
- School district or county budget document listing HR system line item

### Signal 10: Employee Communication Breakdown
Companies where frontline employees are not reached by current communication tools.
- "Internal communications manager" job + "multi-location" or "distributed workforce"
- "No corporate email for field staff" or "deskless workers" + communication initiative
- "Policy rollout" challenge mentioned in HR job description

### Signal 11: Safety and Mandatory-Acknowledgment Pressure
Safety-driven documentation requirements create Workmates buying signals.
- "Policy acknowledgment" + "distributed employees" or "multi-location"
- "Mandatory safety training" + "track completion" + no mention of LMS
- OSHA 300 log or safety incident requiring better workforce documentation

### Signal 12: Union, Labor, Workforce-Relations Complexity
Union environments require precise onboarding and communication documentation.
- "Union contract" + "new hire orientation" in HR job
- "CBA compliance" + "onboarding" mentioned
- NLRB filing or union election petition (nlrb.gov)

### Signal 13: Seasonal Calendar Pressure
Seasonal industries face concentrated onboarding windows — HR software buying is seasonal too.
- School districts: July-August hiring surge (hire before terms start)
- Healthcare / senior care: Q1 and Q3 volume hiring
- Hospitality: spring and summer pre-season hiring
- Retail: fall (October-November) hiring surge

### Signal 14: Public Funding for Modernization
Federal and state grant programs for HR modernization create funded buying events.
- SLFRF (State and Local Fiscal Recovery Funds) grants for workforce modernization
- ARPA workforce investment grants to nonprofits and healthcare
- DOL WIOA grants to workforce development organizations

### Signal 15: Incumbent-System Friction Without Replacement Intent
Companies stuck on a legacy system but not yet shopping — surfacing pain early.
- ADP user + separate "manual onboarding" signal
- Paychex user + paper new hire packet found
- "We use [legacy system] for payroll but still do everything else manually"

### Signal 16: Vendor or Contract Failure
Incumbent vendor failure creates an urgent replacement window.
- "Our previous onboarding vendor" + negative language
- Review site mention of switching: "we left [vendor]" + industry match
- Contract expiration date visible in public procurement records

### Signal 17: Multi-Language and Distributed-Workforce Complexity
Organizations with non-English-speaking or widely distributed employees face elevated onboarding pain.
- "Spanish-speaking staff" or "bilingual" + "new hire" in job description
- "Multiple states" or "nationwide" + "HR coordinator" + no HRIS mentioned
- "Remote and in-person" workforce + "onboarding" mentioned

### Signal 18: Customer or Accreditation Commitments
Third-party accreditation bodies require HR documentation standards.
- JCAHO or Joint Commission accreditation + HR documentation requirements
- ISO 9001 or other quality certification + "employee records" mentioned
- Head Start program quality standards + "new employee orientation" documentation

## Source Map — Competitors Underuse These

| Source | What It Surfaces | URL |
|--------|-----------------|-----|
| OSHA Establishment Search | Safety citations → compliance urgency | osha.gov/data |
| DOL Wage & Hour | Labor violations → HR modernization pressure | dol.gov/agencies/whd |
| CMS Care Compare | Nursing home/home health deficiencies | medicare.gov/care-compare |
| NPPES / NPI Registry | Healthcare org size and type | npiregistry.cms.hhs.gov |
| NCES CCD | K-12 district size, teacher count | nces.ed.gov/ccd |
| NLRB Case Search | Union elections → labor complexity | nlrb.gov/cases-decisions |
| State Licensing Boards | License requirements → credential pain | (state-specific) |
| PE Portfolio Pages | Post-acquisition targets | (PE firm websites) |
| USAspending.gov | Federal contract awards → hiring surges | usaspending.gov |
| Grants.gov | New grant awards → expansion hiring | grants.gov |
| SAM.gov | Active government procurement | sam.gov |
| SEC EDGAR | Public company HR disclosures | sec.gov/edgar |

## Scoring

Apply Prompt 1 scoring model (100 points total). For high-intent signals:
- Signal families 1, 8, 9, 13: add +10 timing bonus if within 60 days
- Signal families 3, 4, 7: add +15 urgency bonus if expansion is imminent
- Signal families 5, 12: add +10 compliance-urgency bonus

## Required Output Schema

See `scrapers/shared/schema.py` — CANONICAL_FIELDS.

Additional JSON field: `signal_family_number` (1–18) for each signal detected.
