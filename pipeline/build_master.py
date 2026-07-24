"""
Build master CSV from all batches. Deduplicates by canonical domain.
Applies full cleaning: fixes names, industries, states, removes noise.
Output: /Users/tanishqmac/nano_onboarding_MASTER.csv
"""
import csv
import re
from pathlib import Path
from urllib.parse import urlparse

CSV_FIELDS = [
    "Company Name", "Verified Company Domain", "Official Website", "Country",
    "State or Province", "Industry", "Estimated Employee Count",
    "Exact Manual-Onboarding Signal", "Exact Evidence Quote",
    "Reason This Indicates Manual Onboarding", "Signal Type",
    "Evidence Source Title", "Verified Evidence Link", "Evidence Date",
    "Confidence Level", "Recommended Outreach Angle",
]

# ── Hard excludes ──────────────────────────────────────────────────────────────
EXCLUDE_DOMAINS = {
    # CDN / generic hosting
    "cdn.websites.hibu.com", "uploads-ssl.webflow.com", "static1.squarespace.com",
    "core-docs.s3.amazonaws.com", "6398505.fs1.hubspotusercontent-na1.net",
    "asupowc.wixsite.com", "paper.ula.edu.pe", "mn.gov",
    # Competitors / vendors
    "workbright.com", "xemplo.com", "signnow.com", "sourcetable.com",
    "getdianahr.com", "tryharmony.ai", "eddy.com", "joinhomebase.com",
    "vectortechnicalinc.com", "yourohionews.com", "udemy.com", "youtube.com",
    "employersresource.com", "hron-call.com", "keyhro.com", "servanthr.com",
    "documentation.infinite.com",
    # Content / blog sites
    "barandrestaurant.com", "numerico.com", "twistedsifter.com", "carecade.org",
    "creai.mx", "reddit.com", "quora.com",
    "brighthub.com", "bizappln.com", "fresh-catalog.com", "thecapable.io",
    "ltcmconsulting.com", "mass-ala.org",
    # Social / video platforms
    "pinterest.com", "vimeo.com",
    # CDN domains
    "rackcdn.com",
    # Non-US job boards
    "ngojobsinafrica.com", "ajiriwa.net", "dohaj.com", "welcometothejungle.com",
    # Patient/non-employee form signals
    "seafamilyhealth.org", "communityfirsthc.org", "eastpointfootandankle.com",
    "nebraskacitypt.com", "tannanplasticsurgery.com", "thunderbasinortho.com",
    "msproseburg.net", "dottiemillerpsychotherapy.com",
    "oppclinic.com", "frankenmuthmedical.com",
    # Non-employee government forms (voter reg, tax — not HR)
    "yorkny.gov", "tarrantcountytx.gov",
    # Wisconsin state portal (medical school forms, not employee onboarding)
    "wi.us",
    # Payroll/HR vendors — not prospects
    "compasspayroll.com",
    # Duplicates (same org under different domain)
    "welcometowellstar.com",   # same as wellstar.org
    "my.clevelandclinic.org",  # same as mercy.com
}

# Patient-only signal keywords — skip if quote only has these in patient context
PATIENT_SIGNALS = re.compile(
    r"(appointment|patient|clinic visitor|bring.*to your appointment|"
    r"your appointment|new patient|patient registration)",
    re.I
)

# Noise names
NOISE_NAMES = {
    "free printable", "home based business", "hire packet", "mn",
    "how to create", "what is a", "sample new hire", "template",
    "the new hire", "a new hire packet",
}

# ── Name / domain / industry / state corrections ───────────────────────────────
NAME_CORRECTIONS = {
    "montefioreeinstein.org": "Montefiore Einstein Medical Center",
    "hratexas.org": "Helping Restore Ability (HRA Texas)",
    "employerflexible.com": "Employer Flexible (PEO)",
    "cfocolorado.biz": "CFO Colorado",
    "gavilan.edu": "Gavilan College",
    "rcc.edu": "Riverside City College",
    "nau.edu": "Northern Arizona University",
    "arizona.edu": "University of Arizona",
    "unl.edu": "University of Nebraska–Lincoln",
    "oswego.edu": "SUNY Oswego",
    "seattleu.edu": "Seattle University",
    "oregon.gov": "State of Oregon (HR Division)",
    "oregonmetro.gov": "Metro Regional Government (Oregon)",
    "hawaii.gov": "DOD Hawaii / Hawaii National Guard HR",
    "wellstar.org": "WellStar Health System",
    "inova.org": "Inova Health System",
    "fluidmgmt.com": "Fluid Management",
    "pallcarenj.org": "NJ Community Palliative Care Collaborative",
    "lssmn.org": "Lutheran Social Service of Minnesota",
    "mercy.com": "Mercy Medical Center",
    "wou.edu": "Western Oregon University",
    "mmyerscpa.com": "Michael J. Myers CPA PC",
    # Batch 2
    "nyc.gov": "New York City Government (NYCAPS)",
    "apsd1.org": "Aitkin Public Schools (ISD 1, MN)",
    "northlandchristian.org": "Northland Christian School",
    "idaho-dea.org": "Idaho District Employees Association",
    "towson.edu": "Towson University",
    "ttu.edu": "Texas Tech University",
    "natlm.com": "National Merchandising Services (NATLM)",
    "thetintstitute.com": "The Tint Institute",
}

DOMAIN_CORRECTIONS = {
    "ww1.oswego.edu": "oswego.edu",
    "in.nau.edu": "nau.edu",
    "law.seattleu.edu": "seattleu.edu",
    "anthropology.arizona.edu": "arizona.edu",
    "businesscentral.unl.edu": "unl.edu",
    "dod.hawaii.gov": "hawaii.gov",
}

WEBSITE_CORRECTIONS = {
    "oswego.edu": "https://www.oswego.edu",
    "nau.edu": "https://www.nau.edu",
    "seattleu.edu": "https://www.seattleu.edu",
    "arizona.edu": "https://www.arizona.edu",
    "unl.edu": "https://www.unl.edu",
    "hawaii.gov": "https://dod.hawaii.gov",
    "oregon.gov": "https://www.oregon.gov",
    "oregonmetro.gov": "https://www.oregonmetro.gov",
    "hratexas.org": "https://www.hratexas.org",
}

INDUSTRY_FIXES = {
    "montefioreeinstein.org": "Healthcare",
    "hratexas.org": "Healthcare / Home Care",
    "employerflexible.com": "Staffing / PEO",
    "cfocolorado.biz": "Construction",
    "gavilan.edu": "Education",
    "rcc.edu": "Education",
    "nau.edu": "Education",
    "arizona.edu": "Education",
    "unl.edu": "Education",
    "oswego.edu": "Education",
    "seattleu.edu": "Education",
    "oregon.gov": "Government",
    "oregonmetro.gov": "Government",
    "hawaii.gov": "Government / Military",
    "wellstar.org": "Healthcare",
    "inova.org": "Healthcare",
    "fluidmgmt.com": "Manufacturing",
    "pallcarenj.org": "Nonprofit / Healthcare",
    "lssmn.org": "Nonprofit / Social Services",
    "mercy.com": "Healthcare",
    "wou.edu": "Education",
    "mmyerscpa.com": "Professional Services",
    # Batch 2
    "nyc.gov": "Government",
    "apsd1.org": "Education",
    "northlandchristian.org": "Education / Faith-Based",
    "idaho-dea.org": "Government / Education",
    "towson.edu": "Education",
    "ttu.edu": "Education",
    "natlm.com": "Retail Merchandising",
    "thetintstitute.com": "Retail / Automotive",
}

STATE_FIXES = {
    "montefioreeinstein.org": "NY",
    "hratexas.org": "TX",
    "employerflexible.com": "TX",
    "cfocolorado.biz": "CO",
    "gavilan.edu": "CA",
    "rcc.edu": "CA",
    "nau.edu": "AZ",
    "arizona.edu": "AZ",
    "unl.edu": "NE",
    "oswego.edu": "NY",
    "seattleu.edu": "WA",
    "oregon.gov": "OR",
    "oregonmetro.gov": "OR",
    "hawaii.gov": "HI",
    "wellstar.org": "GA",
    "inova.org": "VA",
    "pallcarenj.org": "NJ",
    "lssmn.org": "MN",
    "mercy.com": "OH",
    "wou.edu": "OR",
    "mmyerscpa.com": "PA",
    # Batch 2
    "nyc.gov": "NY",
    "apsd1.org": "MN",
    "northlandchristian.org": "TX",
    "idaho-dea.org": "ID",
    "towson.edu": "MD",
    "ttu.edu": "TX",
    "natlm.com": "GA",
    "thetintstitute.com": "IN",
}

HEADCOUNT = {
    "wellstar.org": "20,000–25,000",
    "mercy.com": "2,000–5,000",
    "inova.org": "18,000–20,000",
    "montefioreeinstein.org": "10,000–15,000",
    "lssmn.org": "2,000–4,000",
    "wou.edu": "500–1,000",
    "hratexas.org": "100–500",
    "employerflexible.com": "500–1,000",
    "gavilan.edu": "500–1,000",
    "rcc.edu": "1,000–3,000",
    "pallcarenj.org": "50–200",
    "oregonmetro.gov": "1,000–2,000",
    "oregon.gov": "10,000+",
    "hawaii.gov": "1,000–5,000",
    "nau.edu": "5,000–10,000",
    "arizona.edu": "15,000–20,000",
    "unl.edu": "5,000–10,000",
    "oswego.edu": "1,000–3,000",
    "seattleu.edu": "1,000–3,000",
    "cfocolorado.biz": "50–200",
    # Batch 2
    "nyc.gov": "300,000+",
    "apsd1.org": "100–500",
    "northlandchristian.org": "100–500",
    "idaho-dea.org": "50–200",
    "towson.edu": "3,000–5,000",
    "ttu.edu": "10,000–15,000",
    "natlm.com": "1,000–5,000",
    "thetintstitute.com": "50–200",
}

def get_canonical_domain(raw: str) -> str:
    return DOMAIN_CORRECTIONS.get(raw, raw)

def is_patient_paperwork(quote: str, signal_type: str) -> bool:
    """Return True if the evidence is clearly about patient check-in, not employee onboarding."""
    if signal_type == "in_person_paperwork" and PATIENT_SIGNALS.search(quote):
        # Check if there's any employee/HR context
        employee_context = re.search(
            r"(employee|new hire|hr|human resources|payroll|first day of work|start date|onboarding)",
            quote, re.I
        )
        return not employee_context
    return False

def clean_row(row: dict, raw_domain: str) -> dict | None:
    domain = get_canonical_domain(raw_domain)

    if domain in EXCLUDE_DOMAINS or raw_domain in EXCLUDE_DOMAINS:
        return None

    company_name = NAME_CORRECTIONS.get(raw_domain, NAME_CORRECTIONS.get(domain,
                   row.get("Company Name", "").strip()))

    # Skip noise names
    if any(n in company_name.lower() for n in NOISE_NAMES):
        return None

    quote = row.get("Exact Evidence Quote", "").replace("\n", " ").replace("\r", " ").strip()
    signal_type = row.get("Signal Type", "")

    # Skip patient-only paperwork
    if is_patient_paperwork(quote, signal_type):
        return None

    industry = INDUSTRY_FIXES.get(raw_domain, INDUSTRY_FIXES.get(domain, row.get("Industry", "")))
    state = STATE_FIXES.get(raw_domain, STATE_FIXES.get(domain, row.get("State or Province", "")))
    website = WEBSITE_CORRECTIONS.get(domain, row.get("Official Website", f"https://www.{domain}"))
    headcount = HEADCOUNT.get(domain, HEADCOUNT.get(raw_domain, row.get("Estimated Employee Count", "")))

    return {
        "Company Name": company_name,
        "Verified Company Domain": domain,
        "Official Website": website,
        "Country": "US",
        "State or Province": state,
        "Industry": industry,
        "Estimated Employee Count": headcount,
        "Exact Manual-Onboarding Signal": row.get("Exact Manual-Onboarding Signal", ""),
        "Exact Evidence Quote": quote,
        "Reason This Indicates Manual Onboarding": row.get("Reason This Indicates Manual Onboarding", ""),
        "Signal Type": signal_type,
        "Evidence Source Title": row.get("Evidence Source Title", ""),
        "Verified Evidence Link": row.get("Verified Evidence Link", ""),
        "Evidence Date": row.get("Evidence Date", ""),
        "Confidence Level": row.get("Confidence Level", ""),
        "Recommended Outreach Angle": row.get("Recommended Outreach Angle", ""),
    }


SOURCE_FILES = [
    Path("/Users/tanishqmac/lead-intel/manual_onboarding_leads_clean.csv"),
    Path("/Users/tanishqmac/lead-intel/scripts/nano_onboarding_leads_expanded.csv"),
    Path("/Users/tanishqmac/lead-intel/scripts/nano_batch2_leads.csv"),
    Path("/Users/tanishqmac/lead-intel/scripts/direct_probe_leads.csv"),
]

seen_domains: set[str] = set()
master: list[dict] = []

for f in SOURCE_FILES:
    if not f.exists():
        print(f"  Skipping (not found): {f.name}")
        continue
    batch_count = 0
    with open(f, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            raw_domain = row.get("Verified Company Domain", "").strip().lower()
            if not raw_domain:
                continue
            canonical = get_canonical_domain(raw_domain)
            if canonical in seen_domains:
                continue
            cleaned = clean_row(row, raw_domain)
            if not cleaned:
                continue
            seen_domains.add(canonical)
            master.append(cleaned)
            batch_count += 1
    print(f"  {f.name}: +{batch_count} companies")

# Sort: signal type priority, then confidence, then industry
CONFIDENCE_ORDER = {"High": 0, "Medium": 1, "Low": 2}
SIGNAL_ORDER = {
    "fax_mail": 0, "physical_files": 1, "in_person_paperwork": 2,
    "manual_data_entry": 3, "paper_packets": 4, "email_forms": 5, "spreadsheet": 6,
}
master.sort(key=lambda r: (
    CONFIDENCE_ORDER.get(r["Confidence Level"], 9),
    SIGNAL_ORDER.get(r["Signal Type"], 9),
    r.get("Industry", ""),
    r.get("Company Name", ""),
))

out = Path("/Users/tanishqmac/nano_onboarding_MASTER.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerows(master)

print(f"\n{'='*70}")
print(f"MASTER CSV: {len(master)} unique verified companies → {out}")
print(f"{'='*70}")
print(f"\n{'#':<4} {'Company Name':<46} {'Domain':<32} {'Signal':<22} {'Industry':<28} {'St':<4} {'Conf'}")
print("-" * 145)
for i, r in enumerate(master, 1):
    print(f"{i:<4} {r['Company Name'][:45]:<46} {r['Verified Company Domain'][:31]:<32} "
          f"{r['Signal Type']:<22} {r['Industry'][:27]:<28} {r['State or Province']:<4} {r['Confidence Level']}")
