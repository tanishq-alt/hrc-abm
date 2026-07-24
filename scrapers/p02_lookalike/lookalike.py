"""
Prompt 2: Lookalike / Seed-DNA Prospect Finder

Takes a list of seed domains (known HR Cloud customers or high-quality targets),
builds a Seed DNA model across 7 dimensions, then runs DDG to find similar organizations.

Seed DNA dimensions (with playbook weights):
  1. Operating model (20%) — multi-location, distributed, franchise, seasonal
  2. Workforce composition (20%) — frontline/hourly ratio, deskless %, licensed roles
  3. Hiring/onboarding motion (20%) — volume hiring, seasonal bursts, high turnover
  4. Compliance complexity (15%) — regulated industry, certifications, union
  5. Technology environment (10%) — ADP/legacy payroll, paper-based processes
  6. Economics/change capacity (10%) — PE-backed, recently funded, growth stage
  7. Buying-trigger pattern (5%) — new leader, acquisition, expansion

Scoring:
  similarity_score 0-100 (with penalties)
  current_intent_score 0-25
  total = (similarity * 0.75) + intent

Qualification:
  85-100: Elite — reach out immediately
  78-84: Strong — reach out with light qualification
  70-77: Needs stronger timing signal
  < 70: Reject

Output: data/lookalike_leads.csv (canonical 25-column schema)

Run:
  python3 -u lookalike.py --seeds acme.com,bestcare.org 2>&1 | tee /tmp/lookalike.log
"""

import argparse
import csv
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scrapers.shared.ddg import ddg_search
from scrapers.shared.fetcher import fetch_text
from scrapers.shared.schema import CANONICAL_FIELDS, make_row_from_dict
from scrapers.shared.verifier import verify_domain

OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "lookalike_leads.csv"
OUTPUT_FILE.parent.mkdir(exist_ok=True)

# Default seed domains (HR Cloud reference accounts)
DEFAULT_SEEDS = [
    "sunrisehomecare.com",
    "brightspringhealth.com",
    "accentcare.com",
]

# ── DNA dimension keywords ────────────────────────────────────────────────────
DNA_DIMENSIONS = {
    "operating_model": {
        "weight": 0.20,
        "keywords": ["multi-location", "multiple locations", "distributed", "franchise",
                     "multi-site", "branches", "regional offices", "24/7 operations",
                     "shift-based", "seasonal workforce"],
    },
    "workforce_composition": {
        "weight": 0.20,
        "keywords": ["frontline", "hourly", "deskless", "caregiver", "aide", "technician",
                     "shift worker", "part-time", "no corporate email", "licensed",
                     "certified", "credentialed"],
    },
    "hiring_onboarding_motion": {
        "weight": 0.20,
        "keywords": ["high volume hiring", "continuous hiring", "seasonal hiring",
                     "new hire packet", "onboarding paperwork", "high turnover",
                     "always hiring", "now hiring", "mass hire"],
    },
    "compliance_complexity": {
        "weight": 0.15,
        "keywords": ["OSHA", "CMS", "DOL", "E-Verify", "I-9", "background check",
                     "fingerprint", "union", "collective bargaining", "JCAHO",
                     "state licensing", "credential verification", "audit"],
    },
    "technology_environment": {
        "weight": 0.10,
        "keywords": ["ADP", "Paychex", "Kronos", "paper-based", "manual process",
                     "excel spreadsheet", "physical files", "fax", "legacy system",
                     "no HRIS", "first HR hire"],
    },
    "economics_change_capacity": {
        "weight": 0.10,
        "keywords": ["private equity", "PE-backed", "recently acquired", "merger",
                     "Series B", "Series C", "growth stage", "expansion",
                     "new funding", "recently funded"],
    },
    "buying_trigger_pattern": {
        "weight": 0.05,
        "keywords": ["new HR director", "new superintendent", "new CHRO",
                     "new VP of HR", "acquisition", "new location opening",
                     "new campus", "RFP", "board approved", "evaluation"],
    },
}

SKIP_DOMAINS = {
    "linkedin", "indeed", "glassdoor", "ziprecruiter", "monster",
    "careerbuilder", "simplyhired", "reddit", "quora", "youtube",
    "bamboohr", "gusto", "rippling", "adp", "paychex", "workday",
    "shrm", "forbes", "businessinsider", "medium", "blogspot",
    "hrcloud", "hrdive", "aihr",
}


def should_skip(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return True
    return any(skip in host for skip in SKIP_DOMAINS)


def extract_seed_dna(seed_domain: str) -> dict:
    """Phase 1-2: Fetch seed page and score each DNA dimension."""
    print(f"  Extracting DNA from seed: {seed_domain}", flush=True)
    url = f"https://{seed_domain}"
    text = fetch_text(url)
    if not text:
        # Try search
        results = ddg_search(f"site:{seed_domain}", max_results=3)
        if results:
            text = results[0].get("body", "") + " " + results[0].get("title", "")

    dna = {}
    t = text.lower()
    for dim, info in DNA_DIMENSIONS.items():
        hits = sum(1 for kw in info["keywords"] if kw.lower() in t)
        max_hits = len(info["keywords"])
        dna[dim] = hits / max_hits if max_hits > 0 else 0.0
    dna["raw_text"] = text[:2000]
    return dna


def build_seed_dna_model(seed_domains: list) -> dict:
    """Phase 3: Average DNA across all seeds to build composite model."""
    all_dna = []
    for seed in seed_domains:
        dna = extract_seed_dna(seed)
        all_dna.append(dna)
        time.sleep(2)

    if not all_dna:
        return {dim: 0.5 for dim in DNA_DIMENSIONS}

    composite = {}
    for dim in DNA_DIMENSIONS:
        scores = [d.get(dim, 0.0) for d in all_dna]
        composite[dim] = sum(scores) / len(scores) if scores else 0.0

    # Cluster: identify dominant DNA traits (top 3 dimensions)
    sorted_dims = sorted(composite.items(), key=lambda x: -x[1])
    composite["dominant_traits"] = [dim for dim, _ in sorted_dims[:3]]
    return composite


def generate_candidate_queries(seed_dna: dict) -> list:
    """Phase 4: Generate search queries based on dominant DNA traits."""
    queries = []
    dominant = seed_dna.get("dominant_traits", list(DNA_DIMENSIONS.keys())[:3])

    trait_queries = {
        "operating_model": [
            '"multi-location" "new hire packet" filetype:pdf site:.com',
            '"multiple locations" "employee onboarding" "paper" OR "forms"',
            '"distributed workforce" "HR coordinator" "new hire"',
        ],
        "workforce_composition": [
            '"frontline" "new hire packet" filetype:pdf',
            '"caregiver" "new hire packet" filetype:pdf site:.com',
            '"hourly workers" "onboarding" "paper" OR "manual"',
        ],
        "hiring_onboarding_motion": [
            '"high volume hiring" "onboarding" "manual" OR "paper"',
            '"always hiring" "new hire packet" site:.com',
            '"seasonal hiring" "new hire forms" "complete and return"',
        ],
        "compliance_complexity": [
            '"OSHA" "new hire" "documentation" "manual" company',
            '"E-Verify" "I-9" "new hire" "paper" OR "manual" HR',
            '"background check" "new hire packet" "complete and return"',
        ],
        "technology_environment": [
            '"ADP Workforce Now" "new hire" "paper" OR "manual" HR',
            '"paper-based onboarding" "currently using" company',
            '"excel" "track new hires" HR coordinator job',
        ],
        "economics_change_capacity": [
            '"private equity" "portfolio" "HR" "onboarding" "standardize"',
            '"acquired" "HR" "integration" "onboarding" 2025',
            '"growth stage" "HR" "first hire" OR "scaling"',
        ],
        "buying_trigger_pattern": [
            '"new HR director" "onboarding" "initiative" 2025',
            '"new CHRO" OR "new VP HR" announcement 2025',
            '"RFP" "HRIS" OR "onboarding software" 2025',
        ],
    }

    for trait in dominant:
        queries.extend(trait_queries.get(trait, []))

    # Always add core lookalike queries
    queries.extend([
        '"new hire packet" filetype:pdf site:.com',
        '"employee onboarding" "paper" OR "manual" "multi-location"',
        '"caregiver" OR "frontline" "new hire" "forms" "complete"',
    ])
    return queries


def calculate_similarity(candidate_text: str, seed_dna: dict) -> tuple[int, int]:
    """Phase 5-6: Calculate similarity score and intent overlay."""
    t = candidate_text.lower()

    # Similarity score (0-100)
    weighted_sum = 0.0
    for dim, info in DNA_DIMENSIONS.items():
        hits = sum(1 for kw in info["keywords"] if kw.lower() in t)
        max_hits = len(info["keywords"])
        dim_score = (hits / max_hits) if max_hits > 0 else 0.0
        seed_score = seed_dna.get(dim, 0.0)
        # Similarity = 1 - |candidate - seed| for each dimension
        similarity = 1.0 - abs(dim_score - seed_score)
        weighted_sum += similarity * info["weight"]

    similarity_score = int(weighted_sum * 100)

    # Penalty for missing core traits
    core_kws = ["new hire packet", "onboarding", "employees", "HR", "payroll"]
    missing_core = sum(1 for kw in core_kws if kw not in t)
    similarity_score = max(0, similarity_score - (missing_core * 3))

    # Intent overlay (0-25)
    intent_kws = ["now hiring", "looking for software", "evaluating", "RFP",
                  "new HR director", "acquisition", "2025", "expansion"]
    intent_hits = sum(1 for kw in intent_kws if kw in t)
    intent_score = min(25, intent_hits * 4)

    # Total = (similarity * 0.75) + intent
    total = int(similarity_score * 0.75 + intent_score)

    return similarity_score, total


def find_nearest_seed_neighbor(candidate_text: str, seed_domains: list) -> str:
    """Phase 7: Explain which seed this candidate most resembles."""
    if not seed_domains:
        return ""
    # Simple heuristic: which seed's domain keyword appears most in text
    t = candidate_text.lower()
    best_seed = ""
    best_count = 0
    for seed in seed_domains:
        brand = seed.split(".")[0].replace("-", " ").replace("_", " ")
        words = brand.split()
        count = sum(1 for w in words if len(w) > 3 and w in t)
        if count > best_count:
            best_count = count
            best_seed = seed
    return best_seed or seed_domains[0]


def extract_company_name(title: str, url: str) -> str:
    if title:
        m = re.search(r'\bat\s+([^|–\-]{3,60})', title, re.I)
        if m:
            name = m.group(1).strip()
            if 3 < len(name) < 60:
                return name
        parts = re.split(r'[|–\-]', title)
        if len(parts) >= 2:
            candidate = parts[-1].strip()
            if 3 < len(candidate) < 70:
                return candidate
    host = urlparse(url).netloc.replace("www.", "").split(".")[0]
    return host.replace("-", " ").title()


def main():
    parser = argparse.ArgumentParser(description="Lookalike Prospect Finder — Prompt 2")
    parser.add_argument("--seeds", default=",".join(DEFAULT_SEEDS),
                        help="Comma-separated seed domains")
    parser.add_argument("--min-score", type=int, default=70,
                        help="Minimum total score to include (default: 70)")
    args = parser.parse_args()

    seed_domains = [s.strip() for s in args.seeds.split(",") if s.strip()]
    print("Lookalike Prospect Finder — Prompt 2", flush=True)
    print(f"Seeds: {seed_domains}", flush=True)
    print(f"Min total score: {args.min_score}", flush=True)
    print("=" * 70, flush=True)

    # Phase 1-3: Build seed DNA model
    print("\n[Phase 1-3] Building Seed DNA model...", flush=True)
    seed_dna = build_seed_dna_model(seed_domains)
    dominant = seed_dna.get("dominant_traits", [])
    print(f"Dominant traits: {dominant}", flush=True)

    # Phase 4: Generate candidate queries
    queries = generate_candidate_queries(seed_dna)
    print(f"\n[Phase 4] Generated {len(queries)} candidate queries", flush=True)

    seen_domains: set = set()
    leads: list = []

    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] {query[:80]}...", flush=True)
        results = ddg_search(query, max_results=10)
        print(f"  DDG: {len(results)} results", flush=True)

        for r in results[:5]:
            url = r.get("href", "")
            if not url or should_skip(url):
                continue

            canonical, domain_status = verify_domain(url)
            if not canonical or canonical in seen_domains:
                continue

            title = r.get("title", "")
            snippet = r.get("body", "")

            print(f"  Fetching: {url[:80]}...", flush=True)
            page_text = fetch_text(url)
            combined = snippet + " " + page_text

            # Phase 5-6: Calculate similarity and intent
            similarity_score, total_score = calculate_similarity(combined, seed_dna)

            if total_score < args.min_score:
                continue

            # Phase 7: Find nearest seed neighbor
            nearest_seed = find_nearest_seed_neighbor(combined, seed_domains)

            has_adp = bool(re.search(r"ADP\s+(Workforce\s+Now|Run|TotalSource)", combined, re.I))
            company_name = extract_company_name(title, url)

            # Qualification tier
            if total_score >= 85:
                confidence = "confirmed"
                tier_label = "Elite"
            elif total_score >= 78:
                confidence = "high"
                tier_label = "Strong"
            else:
                confidence = "medium"
                tier_label = "Needs timing"

            row = make_row_from_dict({
                "company_name": company_name,
                "canonical_domain": canonical,
                "country": "US",
                "primary_signal_category": f"lookalike_of_{nearest_seed}",
                "strongest_signal_summary": f"Similarity {similarity_score}/100 to seed {nearest_seed} — {tier_label}",
                "strongest_signal_url": url,
                "adp_status": "confirmed" if has_adp else "not_checked",
                "best_hr_cloud_product": "Onboard+Workmates" if has_adp else "Onboard",
                "fit_score": similarity_score,
                "intent_score": 0,
                "evidence_score": similarity_score,
                "timing_score": 0,
                "uniqueness_score": 0,
                "total_score": total_score,
                "confidence": confidence,
                "outreach_angle": f"Your org shares key traits with {nearest_seed} — similar workforce, similar onboarding complexity.",
                "recommended_buyer_titles": "VP HR, CHRO, Director of Human Resources, COO",
                "disqualifiers_or_risks": "Verify operational similarity to seed. Confirm hiring activity and workforce size.",
            })

            seen_domains.add(canonical)
            leads.append(row)
            print(f"  ✓ {company_name} [{canonical}] score={total_score} nearest={nearest_seed}", flush=True)

        if i % 5 == 0 and leads:
            _save(leads)
            print(f"  ── checkpoint: {len(leads)} leads ──", flush=True)

        time.sleep(2)

    _save(leads)
    print(f"\n{'='*70}", flush=True)
    print(f"Total lookalike leads: {len(leads)} → {OUTPUT_FILE}", flush=True)
    print("\nQualification breakdown:", flush=True)
    elite = sum(1 for l in leads if l.get("total_score", 0) >= 85)
    strong = sum(1 for l in leads if 78 <= l.get("total_score", 0) < 85)
    print(f"  Elite (85+): {elite}", flush=True)
    print(f"  Strong (78-84): {strong}", flush=True)
    print(f"  Needs timing (70-77): {len(leads) - elite - strong}", flush=True)


def _save(leads: list):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()
        writer.writerows(leads)


if __name__ == "__main__":
    main()
