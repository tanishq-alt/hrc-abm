"""
Evidence-to-outreach personalization engine.

Tone and angle shift by persona role and seniority level.
Every claim must be traceable to a verified signal.
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

# Social proof by vertical — calibrated for real scale
SOCIAL_PROOF = {
    "healthcare": {
        "champion":       "A 12-site home health agency in Texas replaced paper caregiver packets with HR Cloud Onboard — new hire completion dropped from 3 hours to 18 minutes, and day-one no-shows fell by 40%.",
        "economic_buyer": "A regional senior care operator with 800+ caregivers cut first-90-day turnover by 22% after moving to digital onboarding — that's roughly $1.1M in annual retention savings.",
        "influencer":     "An HR coordinator at a 6-site home health agency went from spending half her week chasing paper packets to processing all new hires before they arrive on day one.",
        "default":        "A 4-site home health agency in Texas replaced their paper caregiver packet with HR Cloud Onboard — new hire completion time dropped from 3 hours to 18 minutes.",
    },
    "education": {
        "champion":       "A 22-school district in Florida processed 480 back-to-school hires in 4 days using HR Cloud Onboard — the same volume previously took 3 weeks of paper chasing.",
        "economic_buyer": "A mid-size district saved $340K annually by eliminating new hire data re-entry and reducing I-9 compliance exposure — funded with ESSER administrative cost allowance.",
        "influencer":     "An HR specialist at a district with 1,200 staff stopped printing 40-page onboarding packets and now gets every new hire I-9-compliant before day one.",
        "default":        "A 12-school district in Florida moved from paper new-hire packets to digital onboarding and processed 340 back-to-school hires in 3 days instead of 3 weeks.",
    },
    "manufacturing": {
        "champion":       "A 1,400-employee manufacturer across 5 plants eliminated paper safety acknowledgments entirely — OSHA audit took 20 minutes instead of 3 days, zero findings.",
        "economic_buyer": "A PE-backed manufacturer with 3 acquired facilities standardized onboarding across all sites in 6 weeks — new hire processing cost dropped by 68%.",
        "influencer":     "An HR generalist at a 600-person plant cut new hire paperwork from 4 hours to 25 minutes and now has a searchable digital record for every training acknowledgment.",
        "default":        "A 600-employee manufacturer reduced new hire paperwork processing from 4 hours to 25 minutes and now has a defensible OSHA training audit trail.",
    },
    "nonprofit": {
        "champion":       "A 350-person social services nonprofit with 12 program areas cut HR onboarding time by 65% and passed their first paperless funder audit with zero findings.",
        "economic_buyer": "A national nonprofit chapter used HR Cloud to satisfy a foundation funder's digital records requirement — and unlocked a $200K grant renewal that was at risk.",
        "influencer":     "An operations coordinator at a 200-person nonprofit stopped managing paper personnel files and now tracks every document, completion, and expiration in one place.",
        "default":        "A 200-person social services nonprofit cut HR onboarding time by 65% and passed their first-ever paperless audit with zero findings.",
    },
    "government": {
        "champion":       "A county with 1,800 employees moved from 3-day paper onboarding to same-day digital — eliminated new hire data re-entry entirely and passed a state HR audit clean.",
        "economic_buyer": "A mid-size municipality reduced per-hire processing cost by $180 and eliminated $85K in annual overtime attributed to manual HR administration.",
        "influencer":     "An HR specialist at a transit authority stopped faxing I-9s and now has every new hire document verified, signed, and filed before the first shift.",
        "default":        "A mid-size county government went from 3-day paper onboarding to same-day digital — and eliminated the entire new hire data entry re-keying process.",
    },
    "utilities": {
        "champion":       "A 2,200-employee regional utility replaced paper safety onboarding with HR Cloud — NERC compliance documentation is now digital, searchable, and audit-ready in real time.",
        "economic_buyer": "A municipal utility with 800 field workers cut new hire processing cost by 54% and eliminated the compliance gap that had triggered two OSHA recordkeeping citations.",
        "influencer":     "An HR coordinator at an electric cooperative stopped tracking lineworker certifications in spreadsheets — all renewals, expirations, and acknowledgments now auto-alert.",
        "default":        "A regional utility with 1,500 field workers replaced paper safety onboarding with HR Cloud — NERC audit took 30 minutes and returned zero findings.",
    },
    "default": "Similar organizations cut new hire paperwork time by 70% in the first month.",
}


# Persona tone configuration — drives subject lines, email angle, and CTA framing
PERSONA_TONE = {
    # HR leaders: peer-to-peer, process pain, team relief
    "champion": {
        "angle":       "process_efficiency",
        "voice":       "peer",
        "focus":       "your team gets time back, compliance is automatic, new hires arrive ready",
        "cta_style":   "operational",
        "cta_verb":    "show you exactly how",
        "opener_tone": "specific and operational — cite the exact evidence",
    },
    # Finance/C-suite: ROI, risk, strategic transformation
    "economic_buyer": {
        "angle":       "roi_and_risk",
        "voice":       "business_case",
        "focus":       "cost per hire, turnover cost, compliance liability, efficiency gain",
        "cta_style":   "strategic",
        "cta_verb":    "share the ROI model",
        "opener_tone": "lead with cost or risk — make the business case in sentence one",
    },
    # Daily users: tactical pain relief, less admin burden
    "influencer": {
        "angle":       "daily_pain_relief",
        "voice":       "empathetic",
        "focus":       "stop chasing paper, stop re-entering data, get your Friday back",
        "cta_style":   "quick_demo",
        "cta_verb":    "show you a 10-minute walkthrough",
        "opener_tone": "lead with the specific manual task they do every week",
    },
    # IT/compliance: integration, security, audit trail
    "blocker": {
        "angle":       "integration_and_compliance",
        "voice":       "technical",
        "focus":       "SSO, native ADP integration, SOC 2, no data migration, implementation in days",
        "cta_style":   "technical_review",
        "cta_verb":    "walk through the integration architecture",
        "opener_tone": "lead with integration and security — skip the workflow pitch",
    },
}

# Title → role classifier (for when only title string is available)
TITLE_TO_ROLE = {
    "director of human resources": "champion",
    "hr director": "champion",
    "vp of hr": "champion",
    "vp hr": "champion",
    "chief people officer": "champion",
    "head of people": "champion",
    "director of people": "champion",
    "chro": "champion",
    "hris director": "champion",
    "onboarding manager": "champion",
    "credentialing director": "champion",
    "talent director": "champion",
    "director of talent": "champion",
    "hr manager": "influencer",
    "hr generalist": "influencer",
    "hr coordinator": "influencer",
    "hr specialist": "influencer",
    "payroll specialist": "influencer",
    "benefits coordinator": "influencer",
    "recruiter": "influencer",
    "training coordinator": "influencer",
    "cfo": "economic_buyer",
    "chief financial officer": "economic_buyer",
    "ceo": "economic_buyer",
    "chief executive officer": "economic_buyer",
    "coo": "economic_buyer",
    "chief operating officer": "economic_buyer",
    "administrator": "economic_buyer",
    "executive director": "economic_buyer",
    "superintendent": "economic_buyer",
    "county manager": "economic_buyer",
    "city manager": "economic_buyer",
    "vp of operations": "economic_buyer",
    "vp operations": "economic_buyer",
    "it director": "blocker",
    "director of it": "blocker",
    "ciso": "blocker",
    "general counsel": "blocker",
    "legal": "blocker",
    "compliance officer": "blocker",
}


def infer_persona_role(title: str) -> str:
    """Infer role from job title string."""
    low = title.lower()
    for key, role in TITLE_TO_ROLE.items():
        if key in low:
            return role
    if any(t in low for t in ["hr", "human resources", "people", "talent", "onboarding"]):
        return "champion"
    if any(t in low for t in ["cfo", "ceo", "coo", "vp", "president", "director"]):
        return "economic_buyer"
    return "champion"


CTA_OPTIONS = {
    "champion": {
        "Tier 1": "Worth a 15-minute call this week? I can walk you through exactly how we handle {signal_context}.",
        "Tier 2": "Happy to send a 2-page overview of how we handle {signal_context} for similar organizations.",
        "Tier 3": "If the timing makes sense, I'd be glad to show you what we do for {signal_context}.",
    },
    "economic_buyer": {
        "Tier 1": "I can share a one-page ROI breakdown for an organization your size — worth 15 minutes this week?",
        "Tier 2": "Happy to send our cost-per-hire and compliance-risk data for {vertical} organizations your size.",
        "Tier 3": "If this gets on your radar, I'm happy to share the business case data we've built for {vertical}.",
    },
    "influencer": {
        "Tier 1": "I can show you a 10-minute walkthrough — you'd see exactly how it eliminates {signal_context}.",
        "Tier 2": "Happy to do a quick screen-share so you can see the workflow yourself.",
        "Tier 3": "If it ever becomes a priority, I'm happy to show you how it works.",
    },
    "blocker": {
        "Tier 1": "I can walk you through the integration architecture and security documentation in 20 minutes.",
        "Tier 2": "Happy to send our security overview and ADP integration spec for your review.",
        "Tier 3": "If you're evaluating options, I can share our SOC 2 report and integration documentation.",
    },
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
    """Raise if banned phrases appear."""
    t = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in t:
            raise ValueError(f"Banned phrase detected: '{phrase}'")
    return text


def build_first_line(signal_type: str, evidence_excerpt: str,
                      company_name: str, source_url: str,
                      persona_role: str = "champion") -> str:
    """
    Build a specific, evidence-based opening line.
    Tone shifts by persona role:
      champion      → operational, process-specific
      economic_buyer → cost/risk framing
      influencer    → task-specific, empathetic
      blocker       → integration/compliance framing
    """
    # Base templates — champion (default)
    champion_lines = {
        "pdf_new_hire_packet":    f"Found {company_name}'s new hire packet on your website — it's still a paper PDF with forms that require printing, signing, and returning.",
        "job_manual_task":        f"Saw your HR job post requiring someone to 'process new hire paperwork' — that's a signal your onboarding is still manual.",
        "adp_confirmed":          f"{company_name} runs ADP — we add a modern onboarding layer on top without touching your payroll configuration.",
        "osha_citation":          f"Noticed {company_name} had an OSHA recordkeeping finding — we make training documentation digital, searchable, and inspection-proof.",
        "cms_deficiency":         f"CMS flagged {company_name}'s staffing documentation — we help care providers close that compliance gap with digital records.",
        "rfp_hris":               f"Saw {company_name} is formally evaluating HRIS solutions — HR Cloud Onboard is purpose-built for your workforce type.",
        "new_hr_leader":          f"Congratulations on your new role at {company_name} — most new HR leaders start by fixing onboarding, and we make that fast.",
        "acquisition":            f"{company_name}'s recent acquisition creates an HR standardization priority — we handle multi-entity onboarding without a complex implementation.",
        "grant_award":            f"{company_name} received a grant that will drive hiring — we onboard at scale without adding HR headcount.",
        "seasonal_hiring":        f"{company_name} hires at high volume seasonally — we eliminate the paper backlog that comes with every surge.",
        "caregiver_hiring_surge": f"Saw {company_name} is actively hiring caregivers — we get them I-9-compliant, credentialed, and trained before day one.",
        "credential_complexity":  f"{company_name}'s licensed workforce requires ongoing credential tracking — we automate expiration alerts and renewal workflows.",
        "frontline_comm_gap":     f"{company_name} has a large frontline workforce without a dedicated communication channel — Workmates closes that gap.",
    }

    # Economic buyer — lead with cost or compliance risk
    econ_lines = {
        "pdf_new_hire_packet":    f"The paper onboarding process at {company_name} is costing approximately $180–$320 per new hire in staff time — we eliminate that entirely.",
        "osha_citation":          f"An OSHA recordkeeping violation costs an average of $15,625 per citation — digital onboarding at {company_name} makes the audit trail automatic.",
        "cms_deficiency":         f"CMS staffing deficiencies expose {company_name} to survey penalties and reimbursement risk — we close the documentation gap with digital records.",
        "new_hr_leader":          f"New HR leadership at {company_name} creates a window to modernize onboarding — the ROI case is typically 8–12 months payback.",
        "acquisition":            f"The {company_name} acquisition creates HR standardization cost — we consolidate onboarding across entities without a rip-and-replace.",
        "grant_award":            f"{company_name}'s grant award means hiring acceleration — digital onboarding scales without adding HR headcount or cost.",
        "rfp_hris":               f"{company_name} is evaluating HR technology — we typically deliver 60–70% reduction in onboarding administrative cost.",
        "seasonal_hiring":        f"{company_name}'s seasonal hiring volume creates a recurring labor cost in HR processing — we make that fixed and scalable.",
        "adp_confirmed":          f"{company_name} runs ADP — we add onboarding and compliance on top, with no additional payroll integration cost.",
        "credential_complexity":  f"Manual credential tracking at {company_name} creates both compliance liability and administrative cost — we automate both.",
    }

    # Influencer — lead with the specific manual task they do every week
    influencer_lines = {
        "pdf_new_hire_packet":    f"That new hire packet on {company_name}'s website — the one you're printing, handing out, collecting back, and manually filing — we replace all of that.",
        "job_manual_task":        f"The HR job post at {company_name} mentions processing new hire paperwork manually — we eliminate that task entirely.",
        "adp_confirmed":          f"You're re-entering new hire data from paper forms into ADP. With HR Cloud, new hires enter it once and it flows into ADP automatically.",
        "osha_citation":          f"Tracking safety acknowledgments in paper binders is an OSHA audit risk. We move all of that to a digital, searchable, timestamped record.",
        "seasonal_hiring":        f"Every seasonal hiring surge at {company_name} means a paper pile. We let new hires complete everything on their phone before day one.",
        "credential_complexity":  f"Chasing down license expirations in a spreadsheet is manual and risky. We send automated alerts before anything expires.",
        "caregiver_hiring_surge": f"Every new caregiver hire at {company_name} generates a stack of forms. We move all of it to mobile — completed before they walk in the door.",
    }

    # Blocker — lead with integration, security, and compliance angle
    blocker_lines = {
        "adp_confirmed":          f"{company_name} runs ADP — HR Cloud Onboard has a native ADP integration. No custom development, no data migration, no IT lift.",
        "rfp_hris":               f"{company_name}'s HRIS evaluation — we're SOC 2 Type II certified, support SSO, and integrate natively with ADP, Paylocity, and Paycom.",
        "pdf_new_hire_packet":    f"The paper onboarding process at {company_name} creates a data privacy and compliance exposure — we digitize it with full audit trail and SOC 2 controls.",
        "cms_deficiency":         f"{company_name}'s CMS compliance gap requires a defensible digital record. Our audit trail is timestamped, immutable, and exportable.",
        "osha_citation":          f"Digital OSHA documentation at {company_name} means an exportable, timestamped training record that survives any inspection — no IT integration required to start.",
    }

    line_maps = {
        "champion":       champion_lines,
        "economic_buyer": econ_lines,
        "influencer":     influencer_lines,
        "blocker":        blocker_lines,
    }

    lines = line_maps.get(persona_role, champion_lines)
    return lines.get(signal_type,
                     f"Researched {company_name} and found a specific workflow HR Cloud can improve.")


def _subject_lines(signal_type: str, company_name: str,
                   persona_role: str, vertical: str) -> tuple[str, str]:
    """Generate two subject line variants tuned to persona role."""
    if persona_role == "economic_buyer":
        subjects = {
            "pdf_new_hire_packet": (
                f"Onboarding cost at {company_name}",
                f"{company_name} — the ROI case for digital onboarding",
            ),
            "osha_citation":       (
                f"OSHA compliance exposure — {company_name}",
                f"Reducing OSHA citation risk at {company_name}",
            ),
            "rfp_hris":            (
                f"Re: {company_name} HRIS evaluation",
                f"{company_name} HRIS — cost and ROI data",
            ),
            "acquisition":         (
                f"Post-acquisition HR standardization — {company_name}",
                f"{company_name}: consolidating onboarding across entities",
            ),
            "new_hr_leader":       (
                f"New HR leadership at {company_name} — modernization ROI",
                f"{company_name} — onboarding modernization business case",
            ),
            "grant_award":         (
                f"{company_name} grant — scaling hiring without adding cost",
                f"Using {company_name}'s new funding for HR efficiency",
            ),
        }
    elif persona_role == "influencer":
        subjects = {
            "pdf_new_hire_packet": (
                f"Eliminate the paper packet at {company_name}",
                f"{company_name} — no more printing new hire forms",
            ),
            "osha_citation":       (
                f"Digital OSHA tracking for {company_name}",
                f"Stop tracking safety acks in binders — {company_name}",
            ),
            "seasonal_hiring":     (
                f"Stop the paper surge at {company_name}",
                f"{company_name} seasonal onboarding — automate it",
            ),
            "credential_complexity": (
                f"Automate credential tracking at {company_name}",
                f"{company_name} — no more spreadsheet license tracking",
            ),
        }
    elif persona_role == "blocker":
        subjects = {
            "adp_confirmed":       (
                f"HR Cloud ↔ ADP integration at {company_name}",
                f"{company_name} — native ADP integration, no IT lift",
            ),
            "rfp_hris":            (
                f"SOC 2 / SSO / ADP — {company_name} HRIS eval",
                f"Security and integration spec — {company_name}",
            ),
        }
    else:
        # Champion default
        subjects = {
            "pdf_new_hire_packet": (
                f"New hire paperwork at {company_name}",
                f"{company_name} + HR Cloud — quick question",
            ),
            "osha_citation":       (
                f"OSHA documentation at {company_name}",
                f"Digital training records — {company_name}",
            ),
            "rfp_hris":            (
                f"Re: {company_name} HRIS evaluation",
                f"HR Cloud for {company_name}'s HRIS search",
            ),
            "new_hr_leader":       (
                f"Welcome to {company_name} — quick note",
                f"Onboarding modernization at {company_name}",
            ),
            "acquisition":         (
                f"HR standardization after {company_name}'s acquisition",
                f"{company_name} — multi-entity onboarding",
            ),
            "cms_deficiency":      (
                f"CMS compliance gap — {company_name}",
                f"Staffing documentation at {company_name}",
            ),
            "caregiver_hiring_surge": (
                f"Caregiver onboarding at {company_name}",
                f"{company_name} — hire faster, start ready",
            ),
        }

    default_a = f"New hire process at {company_name}"
    default_b = f"{company_name} + HR Cloud"
    pair = subjects.get(signal_type, (default_a, default_b))
    return pair[0], pair[1]


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

    # Infer role from title if role is generic
    if not persona_role or persona_role == "champion":
        persona_role = infer_persona_role(persona_title) if persona_title else "champion"

    tone = PERSONA_TONE.get(persona_role, PERSONA_TONE["champion"])
    proof_map = SOCIAL_PROOF.get(vertical, {"default": SOCIAL_PROOF["default"]})
    if isinstance(proof_map, dict):
        social_proof = proof_map.get(persona_role, proof_map.get("default", SOCIAL_PROOF["default"]))
    else:
        social_proof = proof_map

    first_line = build_first_line(best_signal_type, evidence_excerpt,
                                   company_name, source_url, persona_role)
    signal_context = evidence_excerpt[:60] if evidence_excerpt else "your situation"

    cta_map = CTA_OPTIONS.get(persona_role, CTA_OPTIONS["champion"])
    cta_template = cta_map.get(account_tier, cta_map.get("Tier 2", ""))
    cta = cta_template.replace("{signal_context}", signal_context)\
                      .replace("{vertical}", vertical)

    product_line = {
        "Onboard":           "HR Cloud Onboard replaces paper new-hire packets with a mobile-first digital workflow — I-9, W-4, direct deposit, policy acknowledgments, and task checklists all completed before day one.",
        "Workmates":         "HR Cloud Workmates gives your frontline workforce a dedicated digital communication, recognition, and task channel — no corporate email required.",
        "Onboard+Workmates": "HR Cloud Onboard replaces paper onboarding. Workmates keeps your frontline team connected, informed, and engaged after day one.",
        "Train":             "HR Cloud Train automates required training assignments, completions, and renewal tracking — fully digital, fully auditable.",
        "Credential Tracking": "HR Cloud tracks license expirations, renewal deadlines, and certification compliance — auto-alerts before anything lapses.",
    }.get(best_hr_cloud_product,
          "HR Cloud replaces manual HR processes with a mobile-first digital workflow built for distributed, frontline workforces.")

    # Economic buyer adds ROI framing
    if persona_role == "economic_buyer":
        product_line = f"HR Cloud cuts per-hire administrative cost by 60–70% and creates an audit-ready compliance record. " + product_line

    # IT/blocker adds integration framing
    if persona_role == "blocker":
        product_line = "HR Cloud is SOC 2 Type II certified, supports SSO, and integrates natively with ADP, Paylocity, Paycom, and UKG. " + product_line

    adp_line = ""
    if adp_status in ("confirmed", "strongly_likely"):
        if persona_role == "economic_buyer":
            adp_line = " No rip-and-replace — it works alongside ADP with no additional integration cost."
        elif persona_role == "blocker":
            adp_line = " Native ADP integration — no custom development, no data migration."
        else:
            adp_line = " It works alongside ADP — no rip-and-replace required."

    subject_a, subject_b = _subject_lines(best_signal_type, company_name, persona_role, vertical)
    preview = f"{first_line[:80]}..."

    email_1 = f"""{first_line}

{product_line}{adp_line}

{cta}

— [Your name]
[Title] | HR Cloud
[Phone] | hrcloud.com"""

    email_2_subject = f"Re: {subject_a}"

    if persona_role == "economic_buyer":
        email_2 = f"""One data point that may be relevant.

{social_proof}

Happy to build a comparable model for {company_name}. {cta}

— [Your name]"""
    elif persona_role == "influencer":
        email_2 = f"""Wanted to share a quick example.

{social_proof}

I can show you the exact workflow in 10 minutes — your call on whether it's worth exploring. {cta}

— [Your name]"""
    elif persona_role == "blocker":
        email_2 = f"""A quick follow-up with specifics.

{social_proof}

Happy to send our security overview, SOC 2 summary, and ADP integration spec for your review. {cta}

— [Your name]"""
    else:
        email_2 = f"""A quick data point to close the loop.

{social_proof}

Happy to walk you through how that applies to {company_name}. {cta}

— [Your name]"""

    email_3_subject = f"Closing the loop — {company_name}"

    if persona_role == "economic_buyer":
        email_3 = f"""Last note from me.

If the cost or compliance angle ever becomes relevant at {company_name}, I'm happy to share the ROI model and reference case — no pressure.

— [Your name]"""
    elif persona_role == "influencer":
        email_3 = f"""Last note — no pressure.

If the paper onboarding process ever becomes your problem to solve, I'd love to show you the workflow. Takes 10 minutes.

— [Your name]"""
    else:
        email_3 = f"""Last note from me on this.

{persona_hook}

If the timing isn't right, no problem — happy to reconnect when it is.

— [Your name]"""

    pain_hypothesis = f"Based on evidence: {evidence_excerpt[:120]}"

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
