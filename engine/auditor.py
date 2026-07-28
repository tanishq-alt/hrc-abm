"""
Independent lead quality auditor.

Recomputes scores, validates traceability, checks entity identity,
freshness, and consistency. Returns AuditResult.
Never silently fixes evidence.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AuditResult:
    audit_status: str = "pass"           # pass / pass_with_warning / return_to_research / downgrade / reject
    audit_score: int = 100
    fatal_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    downgrade_reason: str = ""
    required_fix: str = ""
    rejection_reason: str = ""
    traceability_pass: bool = True
    identity_pass: bool = True
    freshness_pass: bool = True
    confidence_pass: bool = True
    persona_pass: bool = True
    product_fit_pass: bool = True
    export_integrity_pass: bool = True


def audit_account(account_dict: dict, evidence_list: list = None) -> AuditResult:
    """
    Audit an account record. account_dict is the dict representation of Account.
    evidence_list is a list of evidence dicts from EvidenceLedger.to_list().
    """
    result = AuditResult()
    evidence_list = evidence_list or []
    deductions = 0

    # ── Identity checks ───────────────────────────────────────────────────────
    if not account_dict.get("canonical_domain"):
        result.fatal_errors.append("No canonical domain")
        result.identity_pass = False

    domain_status = account_dict.get("domain_status", "unresolved")
    if domain_status == "unresolved":
        result.fatal_errors.append("Domain status is unresolved")
        result.identity_pass = False
    elif domain_status in ("non_employer_host",):
        result.fatal_errors.append(f"Non-employer domain: {domain_status}")
        result.identity_pass = False

    if not result.identity_pass:
        deductions += 15

    # ── Traceability checks ───────────────────────────────────────────────────
    if not account_dict.get("primary_evidence_url"):
        result.fatal_errors.append("No evidence URL for primary claim")
        result.traceability_pass = False
        deductions += 20

    if not account_dict.get("primary_evidence_excerpt"):
        result.fatal_errors.append("No exact excerpt for primary claim")
        result.traceability_pass = False
        deductions += 10

    # ── Source authority ──────────────────────────────────────────────────────
    primary_tier = account_dict.get("primary_signal_tier", "C")
    tier_score = {"A": 15, "B": 12, "C": 8, "D": 0}.get(primary_tier, 5)

    account_tier = account_dict.get("account_tier", "Disqualified")
    if account_tier == "Tier 1" and primary_tier not in ("A", "B"):
        result.fatal_errors.append("Tier 1 account lacks Tier A/B evidence source")
        result.confidence_pass = False
        deductions += 15

    # ── Freshness checks ──────────────────────────────────────────────────────
    freshness_ok = True
    if evidence_list:
        stale_count = sum(1 for e in evidence_list if not e.get("fresh", True))
        if stale_count == len(evidence_list):
            result.fatal_errors.append("All evidence is stale")
            result.freshness_pass = False
            freshness_ok = False
            deductions += 10

    # ── Persona checks ────────────────────────────────────────────────────────
    if account_tier == "Tier 1":
        if not account_dict.get("champion_title"):
            result.fatal_errors.append("Tier 1 account has no champion title")
            result.persona_pass = False
            deductions += 7

    # ── Scoring consistency ───────────────────────────────────────────────────
    composite = int(account_dict.get("composite_score", 0) or 0)
    if account_tier == "Tier 1" and composite < 65:
        result.warnings.append(f"Tier 1 but composite score is {composite} — possible miscalculation")
        deductions += 5
    elif account_tier == "Tier 2" and composite < 45:
        result.warnings.append(f"Tier 2 but composite score is {composite} — possible miscalculation")
        deductions += 3

    # ── Product fit ───────────────────────────────────────────────────────────
    if not account_dict.get("best_hr_cloud_product"):
        result.warnings.append("No HR Cloud product recommended")
        result.product_fit_pass = False
        deductions += 5

    # ── Export integrity ──────────────────────────────────────────────────────
    if not account_dict.get("company_name"):
        result.fatal_errors.append("Company name missing")
        result.export_integrity_pass = False
        deductions += 5

    # ── Final audit score ─────────────────────────────────────────────────────
    result.audit_score = max(0, 100 - deductions)

    if result.fatal_errors:
        if result.audit_score < 70:
            result.audit_status = "reject"
            result.rejection_reason = "; ".join(result.fatal_errors[:2])
        else:
            result.audit_status = "return_to_research"
            result.required_fix = result.fatal_errors[0]
    elif result.audit_score < 80:
        result.audit_status = "pass_with_warning"
        result.downgrade_reason = "; ".join(result.warnings[:2])
    else:
        result.audit_status = "pass"

    return result


def audit_accounts(accounts: list, evidence_map: dict = None) -> dict:
    """
    Batch audit. accounts is a list of account dicts.
    evidence_map is {canonical_domain: [evidence dicts]}.
    Returns {canonical_domain: AuditResult}.
    """
    evidence_map = evidence_map or {}
    results = {}
    for a in accounts:
        domain = a.get("canonical_domain", "")
        evs = evidence_map.get(domain, [])
        results[domain] = audit_account(a, evs)
    return results
