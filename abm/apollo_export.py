"""
Apollo.io export formatter.
Converts Account list to Apollo-compatible CSV for bulk import.
Also generates sequence step notes per account.
"""
import csv
from datetime import datetime
from pathlib import Path
from dataclasses import asdict
from typing import List

from abm.account import Account, ACCOUNT_CSV_FIELDS
from abm.tiers import TIER_ACTIONS

OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)


# Apollo CSV column mapping
APOLLO_FIELDS = [
    "Account Tier",
    "Company",
    "Website",
    "Industry",
    "# Employees",
    "State",
    "Country",
    "Signal Type",
    "Signal Evidence",
    "Signal URL",
    "ADP Status",
    "Composite Score",
    "ICP Score",
    "Best Product",
    "Champion Title",
    "Economic Buyer Title",
    "First Line",
    "Outreach Angle",
    "Email Subject A",
    "Email Subject B",
    "CTA",
    "Apollo Sequence",
    "Next Action",
    "Disqualified Reason",
    "Intent Score",
    "Confidence Score",
    "Contactability Score",
    "Signal Strength",
    "Signal Confidence",
    "Safe to Mention",
    "Why Now",
    "HRIS Fit Category",
    "Entity Type",
    "Parent Company",
    "Negative Evidence",
    "Audit Status",
    "Audit Score",
    "Next Research Action",
]


def account_to_apollo_row(account: Account) -> dict:
    tier_action = TIER_ACTIONS.get(account.account_tier, TIER_ACTIONS["Disqualified"])
    return {
        "Account Tier":        account.account_tier,
        "Company":             account.company_name,
        "Website":             f"https://{account.canonical_domain}" if account.canonical_domain else "",
        "Industry":            account.industry,
        "# Employees":         account.employee_range,
        "State":               account.hq_state,
        "Country":             account.country,
        "Signal Type":         account.primary_signal_type,
        "Signal Evidence":     account.primary_evidence_excerpt[:200],
        "Signal URL":          account.primary_evidence_url,
        "ADP Status":          account.adp_status,
        "Composite Score":     account.composite_score,
        "ICP Score":           account.icp_score,
        "Best Product":        account.best_hr_cloud_product,
        "Champion Title":      account.champion_title,
        "Economic Buyer Title": account.economic_buyer_title,
        "First Line":          account.safe_first_line,
        "Outreach Angle":      account.outreach_angle,
        "Email Subject A":     account.email_subject_a,
        "Email Subject B":     account.email_subject_b,
        "CTA":                 account.recommended_cta,
        "Apollo Sequence":     tier_action.get("apollo_sequence", "") or "",
        "Next Action":         account.next_action,
        "Disqualified Reason": account.rejection_reason,
        "Intent Score":          account.intent_score,
        "Confidence Score":      account.confidence_score,
        "Contactability Score":  account.contactability_score,
        "Signal Strength":       account.signal_strength,
        "Signal Confidence":     account.signal_confidence,
        "Safe to Mention":       str(account.signal_safe_to_mention),
        "Why Now":               account.why_now,
        "HRIS Fit Category":     account.hris_fit_category,
        "Entity Type":           account.entity_type,
        "Parent Company":        account.parent_company,
        "Negative Evidence":     "; ".join(n.get("label","") for n in (account.negative_evidence or [])),
        "Audit Status":          account.audit_status,
        "Audit Score":           account.audit_score,
        "Next Research Action":  account.next_research_action,
    }


def export_to_apollo(accounts: List[Account], label: str = "") -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    suffix = f"_{label}" if label else ""
    output_path = OUTPUT_DIR / f"apollo_import{suffix}_{ts}.csv"

    # Split by tier for separate Apollo sequence assignment
    tier1 = [a for a in accounts if a.account_tier == "Tier 1"]
    tier2 = [a for a in accounts if a.account_tier == "Tier 2"]
    disqualified = [a for a in accounts if a.account_tier == "Disqualified"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=APOLLO_FIELDS)
        writer.writeheader()
        # Write Tier 1 first (highest priority)
        for account in sorted(tier1, key=lambda a: -a.composite_score):
            writer.writerow(account_to_apollo_row(account))
        for account in sorted(tier2, key=lambda a: -a.composite_score):
            writer.writerow(account_to_apollo_row(account))
        for account in sorted(disqualified, key=lambda a: -a.composite_score):
            writer.writerow(account_to_apollo_row(account))

    print(f"\nApollo export: {output_path}", flush=True)
    print(f"  Tier 1: {len(tier1)} accounts", flush=True)
    print(f"  Tier 2: {len(tier2)} accounts", flush=True)
    print(f"  Disqualified: {len(disqualified)} accounts", flush=True)
    return output_path


def export_sequences(accounts: List[Account], label: str = "") -> Path:
    """Export full email sequences per account for mail merge."""
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    suffix = f"_{label}" if label else ""
    output_path = OUTPUT_DIR / f"sequences{suffix}_{ts}.csv"

    fields = [
        "account_tier", "composite_score", "company_name", "canonical_domain",
        "champion_title", "safe_first_line",
        "email_subject_a", "email_1_body",
        "email_subject_b_followup", "email_2_body",
        "email_3_subject", "email_3_body",
        "linkedin_note",
    ]

    qualified = [a for a in accounts if a.account_tier in ("Tier 1", "Tier 2")]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for a in sorted(qualified, key=lambda x: -x.composite_score):
            writer.writerow({
                "account_tier":           a.account_tier,
                "composite_score":        a.composite_score,
                "company_name":           a.company_name,
                "canonical_domain":       a.canonical_domain,
                "champion_title":         a.champion_title,
                "safe_first_line":        a.safe_first_line,
                "email_subject_a":        a.email_subject_a,
                "email_1_body":           a.email_1_body,
                "email_subject_b_followup": a.email_subject_b,
                "email_2_body":           a.email_2_body,
                "email_3_subject":        f"Closing the loop — {a.company_name}",
                "email_3_body":           a.email_3_body,
                "linkedin_note":          a.linkedin_note,
            })

    print(f"Sequence export: {output_path} ({len(qualified)} accounts)", flush=True)
    return output_path
