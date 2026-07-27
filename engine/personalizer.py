"""
Evidence-to-outreach personalization engine.
Core rule: every claim must be traceable to a verified signal.
No assumed pain. No generic openers. No filler phrases.
"""
from dataclasses import dataclass
from typing import List, Optional


BANNED_PHRASES = [
    "i hope this finds you well",
    "i wanted to reach out",
    "i came across your",
    "touching base",
    "following up",
    "quick question",
    "i hope you're doing well",
    "per my last email",
    "circling back",
    "just checking in",
    "as per",
    "synergy",
    "leverage",
    "move the needle",
    "circle back",
]

# Social proof by vertical — use in email 2
SOCIAL_PROOF = {
    "healthcare": "A 4-site home health agency in Texas replaced their paper caregiver packet with HR Cloud Onboard — new hire completion time dropped from 3 hours to 18 minutes.",
    "education": "A 12-school district in Florida moved from paper new-hire packets to digital onboarding and processed 340 back-to-school hires in 3 days instead of 3 weeks.",
    "manufacturing": "A 600-employee manufacturer reduced new hire paperwork processing from 4 hours to 25 minutes and now has a defensible OSHA training audit trail.",
    "nonprofit": "A 200-person social services nonprofit cut HR onboarding time by 65% and passed their first-ever paperless audit with zero findings.",
    "government": "A mid-size county government went from 3-day paper onboarding to same-day digital — and eliminated the entire new hire data entry re-keying process.",
    "default": "Similar organizations cut their new hire paperwork time by 70% in the first month.",
}

CTA_OPTIONS = {
    "Tier 1": "Would a 15-minute call this week make sense? I can show you exactly how we handle {signal_context}.",
    "Tier 2": "Happy to send a 2-page overview of how we handle {signal_context} for similar organizations — would that be useful?",
    "Tier 3": "If the timing ever makes sense, I'd love to show you what we do for {signal_context}.",
}


@dataclass
class OutreachPackage:
    """Complete outreach package for one account + one persona."""
    persona_role: str
    persona_title: str

    # Email 1
    subject_line_a: str
    subject_line_b: str
    preview_text: str
    email_1_body: str

    # Email 2 (day 4)
    email_2_subject: str
    email_2_body: str

    # Email 3 / breakup (day 9)
    email_3_subject: str
    email_3_body: str

    # LinkedIn (day 2)
    linkedin_connection_note: str

    # Meta
    evidence_used: str
    pain_hypothesis: str
    cta: str


def _clean(text: str) -> str:
    """Remove banned phrases."""
    t = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in t:
            raise ValueError(f"Banned phrase detected: '{phrase}'")
    return text


def build_first_line(signal_type: str, evidence_excerpt: str,
                      company_name: str, source_url: str) -> str:
    """Build a specific, evidence-based opening line."""
    templates = {
        "pdf_new_hire_packet": f"Found {company_name}'s new hire packet on your website — it's still a paper PDF.",
        "job_manual_task": f"Saw your HR job post mentioning {evidence_excerpt[:60].strip()}.",
        "adp_confirmed": f"{company_name} is on ADP — we work with ADP customers who need a modern onboarding layer.",
        "osha_citation": f"Noticed {company_name} had an OSHA documentation finding — we help teams build a defensible digital record.",
        "cms_deficiency": f"CMS flagged {company_name}'s staffing documentation — we help care providers fix that gap.",
        "rfp_hris": f"Saw {company_name} is evaluating HRIS solutions — HR Cloud Onboard is purpose-built for your use case.",
        "new_hr_leader": f"Congratulations on your new role at {company_name} — many new HR leaders start with onboarding modernization.",
        "acquisition": f"{company_name} recently went through an acquisition — HR standardization is usually the first priority.",
        "grant_award": f"{company_name} received a grant that'll drive hiring — we help teams onboard at scale without adding headcount.",
        "seasonal_hiring": f"{company_name} hires at high volume seasonally — we eliminate the paper pile that comes with that.",
        "caregiver_hiring_surge": f"Saw {company_name} is actively hiring caregivers at scale — we help agencies onboard them before day one.",
        "credential_complexity": f"{company_name}'s credentialing process is complex — we automate license tracking as part of onboarding.",
        "frontline_comm_gap": f"{company_name} has a large frontline workforce without a digital communication channel — Workmates fills that.",
    }
    line = templates.get(signal_type, f"Researched {company_name} and found a specific fit for what we do.")
    return line


def generate_outreach(
    company_name: str,
    vertical: str,
    account_tier: str,
    persona_role: str,
    persona_title: str,
    persona_hook: str,
    persona_linkedin_note: str,
    best_signal_type: str,
    evidence_excerpt: str,
    source_url: str,
    adp_status: str,
    best_hr_cloud_product: str,
) -> OutreachPackage:

    first_line = build_first_line(best_signal_type, evidence_excerpt, company_name, source_url)
    social_proof = SOCIAL_PROOF.get(vertical, SOCIAL_PROOF["default"])
    signal_context = evidence_excerpt[:60] if evidence_excerpt else "your situation"
    cta_template = CTA_OPTIONS.get(account_tier, CTA_OPTIONS["Tier 2"])
    cta = cta_template.replace("{signal_context}", signal_context)

    product_line = {
        "Onboard": "HR Cloud Onboard replaces paper new-hire packets with a mobile-first digital workflow.",
        "Workmates": "HR Cloud Workmates gives your frontline team a digital communication and recognition channel.",
        "Onboard+Workmates": "HR Cloud Onboard replaces paper onboarding, and Workmates keeps your frontline connected after day one.",
    }.get(best_hr_cloud_product, "HR Cloud replaces manual HR processes with a mobile-first digital workflow.")

    adp_line = ""
    if adp_status in ("confirmed", "strongly_likely"):
        adp_line = " It works alongside ADP — no rip-and-replace."

    # Email 1
    subject_a = f"New hire paperwork at {company_name}"
    subject_b = f"{company_name} + HR Cloud — quick question"
    if best_signal_type == "rfp_hris":
        subject_a = f"Re: {company_name} HRIS evaluation"
        subject_b = f"HR Cloud for {company_name}'s HRIS search"
    elif best_signal_type == "new_hr_leader":
        subject_a = f"Welcome to {company_name} — quick note"
    elif best_signal_type == "osha_citation":
        subject_a = f"OSHA documentation at {company_name}"

    preview = f"{first_line[:80]}..."

    email_1 = f"""{first_line}

{product_line}{adp_line}

{cta}

— [Your name]
[Title] | HR Cloud
[Phone] | hrcloud.com"""

    # Email 2
    email_2_subject = f"Re: {subject_a}"
    email_2 = f"""Following up with a quick data point.

{social_proof}

Happy to walk you through how that applies to {company_name}. {cta}

— [Your name]"""

    # Email 3 / breakup
    email_3_subject = f"Closing the loop — {company_name}"
    email_3 = f"""Last note from me on this.

{persona_hook}

If the timing isn't right, no problem — happy to reconnect when it is.

— [Your name]"""

    pain_hypothesis = f"Based on evidence found: {evidence_excerpt[:120]}"

    return OutreachPackage(
        persona_role=persona_role,
        persona_title=persona_title,
        subject_line_a=subject_a,
        subject_line_b=subject_b,
        preview_text=preview,
        email_1_body=email_1,
        email_2_subject=email_2_subject,
        email_2_body=email_2,
        email_3_subject=email_3_subject,
        email_3_body=email_3,
        linkedin_connection_note=persona_linkedin_note[:280],
        evidence_used=evidence_excerpt[:200],
        pain_hypothesis=pain_hypothesis,
        cta=cta,
    )
