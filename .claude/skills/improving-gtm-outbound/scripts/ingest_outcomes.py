"""
Outcome ingestion script — normalises Apollo/HubSpot CSV exports to the
canonical outcome schema defined in DATA_CONTRACTS.md.

Usage:
  python3 .claude/skills/improving-gtm-outbound/scripts/ingest_outcomes.py \
      --input ~/Downloads/apollo_export.csv \
      --campaign-date 2026-08-01 \
      [--account-csv data/abm_accounts_healthcare_20260731_1200.csv]

Output: data/learning/outcomes/YYYY-MM-DD_outcomes.csv
        data/learning/audit/YYYY-MM-DD_audit.jsonl (appended)
"""

import argparse
import csv
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engine.personalizer import infer_persona_role

OUTCOMES_DIR = ROOT / "data" / "learning" / "outcomes"
AUDIT_DIR = ROOT / "data" / "learning" / "audit"
DATA_DIR = ROOT / "data"

OUTCOMES_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

VALID_OUTCOMES = {
    "reply", "meeting_booked", "disqualified", "bounced", "unsubscribed", "no_response"
}

CANONICAL_FIELDS = [
    "outcome_id", "canonical_domain", "company_name", "outreach_date",
    "contact_title", "contact_persona_role", "sequence_name", "sequence_step",
    "outcome", "outcome_date", "days_to_outcome", "email_subject_used",
    "account_tier_at_send", "icp_score_at_send", "intent_score_at_send",
    "signal_type_at_send", "vertical", "adp_status_at_send",
    "hris_fit_category_at_send", "campaign_batch",
]


# ── Column auto-detection ─────────────────────────────────────────────────────

APOLLO_COLUMN_MAP = {
    "Company":           "company_name",
    "Website":           "_website",
    "Title":             "contact_title",
    "Email Sequence":    "sequence_name",
    "Sequence Step #":   "sequence_step",
    "Replied":           "_replied",
    "Meeting Booked":    "_meeting_booked",
    "Bounced":           "_bounced",
    "Unsubscribed":      "_unsubscribed",
    "Email Subject":     "email_subject_used",
    "Sent At":           "outreach_date",
    "Last Activity":     "_last_activity",
}

HUBSPOT_COLUMN_MAP = {
    "Associated Company":    "company_name",
    "Website URL":           "_website",
    "Job Title":             "contact_title",
    "Enrollment name":       "sequence_name",
    "Step Number":           "sequence_step",
    "Latest email reply":    "_replied",
    "First meeting booked":  "_meeting_booked",
    "Email hard bounce":     "_bounced",
    "Unsubscribed":          "_unsubscribed",
    "Subject":               "email_subject_used",
    "Enrollment date":       "outreach_date",
    "Last email activity":   "_last_activity",
}


def detect_format(headers: list) -> dict:
    apollo_hits = sum(1 for h in headers if h in APOLLO_COLUMN_MAP)
    hubspot_hits = sum(1 for h in headers if h in HUBSPOT_COLUMN_MAP)
    return APOLLO_COLUMN_MAP if apollo_hits >= hubspot_hits else HUBSPOT_COLUMN_MAP


def normalise_domain(raw: str) -> str:
    if not raw:
        return ""
    raw = raw.strip().lower()
    if not raw.startswith("http"):
        raw = "https://" + raw
    try:
        host = urlparse(raw).netloc
        host = host.replace("www.", "")
        return host.split("/")[0]
    except Exception:
        return ""


def derive_outcome(row: dict) -> tuple[str, str]:
    """Returns (outcome, outcome_date) from raw row."""
    if row.get("_meeting_booked", "").strip().lower() in ("yes", "true", "1"):
        return "meeting_booked", row.get("_last_activity", "")
    if row.get("_replied", "").strip().lower() in ("yes", "true", "1"):
        return "reply", row.get("_last_activity", "")
    if row.get("_bounced", "").strip().lower() in ("yes", "true", "1"):
        return "bounced", row.get("_last_activity", "")
    if row.get("_unsubscribed", "").strip().lower() in ("yes", "true", "1"):
        return "unsubscribed", row.get("_last_activity", "")
    return "no_response", ""


def normalise_date(raw: str) -> str:
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw.strip()[:10]


def compute_days(outreach_date: str, outcome_date: str) -> str:
    if not outreach_date or not outcome_date:
        return ""
    try:
        d1 = datetime.strptime(outreach_date, "%Y-%m-%d").date()
        d2 = datetime.strptime(outcome_date, "%Y-%m-%d").date()
        return str((d2 - d1).days)
    except ValueError:
        return ""


def make_outcome_id(domain: str, outreach_date: str, contact_title: str) -> str:
    raw = f"{domain}|{outreach_date}|{contact_title.lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_existing_ids() -> set:
    seen = set()
    for f in OUTCOMES_DIR.glob("*.csv"):
        try:
            with open(f, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    oid = row.get("outcome_id", "")
                    if oid:
                        seen.add(oid)
        except Exception:
            pass
    return seen


def load_account_lookup() -> dict:
    """Build domain → account-level fields dict from most recent abm_accounts CSV."""
    lookup = {}
    csvs = sorted(DATA_DIR.glob("abm_accounts_*.csv"), key=lambda p: p.stat().st_mtime)
    if not csvs:
        return lookup
    with open(csvs[-1], newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            domain = row.get("canonical_domain", "").strip().lower()
            if domain:
                lookup[domain] = row
    return lookup


def append_audit(entry: dict):
    today = date.today().isoformat()
    audit_file = AUDIT_DIR / f"{today}_audit.jsonl"
    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run(input_path: str, campaign_date: str, account_csv: str = "") -> Path:
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    account_lookup = load_account_lookup()
    existing_ids = load_existing_ids()
    print(f"Loaded {len(account_lookup)} account records for joining")
    print(f"Existing outcome IDs to skip: {len(existing_ids)}")

    raw_rows: list[dict] = []
    with open(input_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        col_map = detect_format(headers)
        fmt_name = "Apollo" if col_map is APOLLO_COLUMN_MAP else "HubSpot"
        print(f"Detected format: {fmt_name}")

        for row in reader:
            mapped = {}
            for src_col, dst_col in col_map.items():
                if src_col in row:
                    mapped[dst_col] = row[src_col]
            raw_rows.append(mapped)

    print(f"Read {len(raw_rows)} rows from {input_file.name}")

    normalised = []
    skip_reasons: dict[str, int] = {}

    for row in raw_rows:
        domain = normalise_domain(row.get("_website", "") or row.get("company_name", ""))
        if not domain:
            skip_reasons["no_canonical_domain"] = skip_reasons.get("no_canonical_domain", 0) + 1
            continue

        outreach_date = normalise_date(row.get("outreach_date", ""))
        contact_title = row.get("contact_title", "")
        outcome_id = make_outcome_id(domain, outreach_date, contact_title)

        if outcome_id in existing_ids:
            skip_reasons["duplicate_outcome_id"] = skip_reasons.get("duplicate_outcome_id", 0) + 1
            continue

        outcome, outcome_date_raw = derive_outcome(row)
        outcome_date = normalise_date(outcome_date_raw)
        days_to = compute_days(outreach_date, outcome_date)
        persona_role = infer_persona_role(contact_title) if contact_title else "unknown"

        account = account_lookup.get(domain, {})
        vertical = account.get("vertical", "")
        if not vertical:
            skip_reasons["no_vertical_match"] = skip_reasons.get("no_vertical_match", 0) + 1

        out_row = {
            "outcome_id":              outcome_id,
            "canonical_domain":        domain,
            "company_name":            row.get("company_name", ""),
            "outreach_date":           outreach_date,
            "contact_title":           contact_title,
            "contact_persona_role":    persona_role,
            "sequence_name":           row.get("sequence_name", ""),
            "sequence_step":           row.get("sequence_step", ""),
            "outcome":                 outcome,
            "outcome_date":            outcome_date,
            "days_to_outcome":         days_to,
            "email_subject_used":      row.get("email_subject_used", ""),
            "account_tier_at_send":    account.get("account_tier", ""),
            "icp_score_at_send":       account.get("icp_score", ""),
            "intent_score_at_send":    account.get("intent_score", ""),
            "signal_type_at_send":     account.get("primary_signal_type", ""),
            "vertical":                vertical,
            "adp_status_at_send":      account.get("adp_status", ""),
            "hris_fit_category_at_send": account.get("hris_fit_category", ""),
            "campaign_batch":          campaign_date,
        }
        normalised.append(out_row)
        existing_ids.add(outcome_id)

    if not normalised:
        print("WARNING: No rows were normalised. Check input file and column mapping.")

    out_path = OUTCOMES_DIR / f"{campaign_date}_outcomes.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()
        writer.writerows(normalised)

    no_vertical = skip_reasons.get("no_vertical_match", 0)
    if no_vertical > len(normalised) * 0.5:
        print(f"WARNING: {no_vertical}/{len(normalised)} rows have no vertical match. "
              "Ensure account CSVs are present in data/.")

    print(f"\nIngestion complete")
    print(f"  Rows read:        {len(raw_rows)}")
    print(f"  Rows normalised:  {len(normalised)}")
    print(f"  Rows skipped:     {sum(skip_reasons.values())}")
    for reason, count in skip_reasons.items():
        print(f"    {reason}: {count}")
    print(f"  Output: {out_path}")

    append_audit({
        "ts": datetime.utcnow().isoformat() + "Z",
        "script": "ingest_outcomes.py",
        "action": "ingest",
        "input": input_file.name,
        "rows_read": len(raw_rows),
        "rows_normalised": len(normalised),
        "rows_skipped": sum(skip_reasons.values()),
        "skip_reasons": skip_reasons,
        "campaign_batch": campaign_date,
        "output": str(out_path),
    })

    return out_path


def main():
    parser = argparse.ArgumentParser(description="Ingest Apollo/HubSpot campaign outcomes")
    parser.add_argument("--input", required=True, help="Path to Apollo or HubSpot CSV export")
    parser.add_argument("--campaign-date", required=True,
                        help="Campaign date as YYYY-MM-DD (used for output filename and batch tag)")
    parser.add_argument("--account-csv", default="",
                        help="Override account CSV for joining (default: most recent abm_accounts_*.csv)")
    args = parser.parse_args()
    run(args.input, args.campaign_date, args.account_csv)


if __name__ == "__main__":
    main()
