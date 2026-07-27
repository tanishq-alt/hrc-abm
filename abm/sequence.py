"""Outreach sequence generator.

Generates a complete 3-email + LinkedIn touch sequence for each account.

Sequence structure:
  Day 1  — Email 1: evidence-based opener + single value prop + low-friction CTA
  Day 2  — LinkedIn: connection request with personalized note
  Day 4  — Email 2: different angle, social proof from same vertical/size/geo
  Day 9  — Email 3: break-up email — "last note" + 2-sentence value prop

Rules:
  - One pain per sequence. Pick the strongest signal. Don't list multiple pains.
  - Every opener cites specific evidence. No generic "I hope this finds you well."
  - CTA is always low-friction: "15-min call" or "send you a 2-page overview"
  - Break-up email is warm and honest — no guilt, no desperation
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SequenceStep:
    """One step in the outreach sequence."""
    step_number: int
    day: int                  # day in sequence (1, 2, 4, 9)
    channel: str              # "email", "linkedin"
    subject: str              # email subject or linkedin message title
    body: str                 # full message body
    notes: str = ""           # rep notes (not sent to prospect)


@dataclass
class OutreachSequence:
    """Complete outreach sequence for one account + persona."""
    company_name: str
    persona_role: str
    persona_title: str
    account_tier: str
    primary_signal: str
    steps: List[SequenceStep] = field(default_factory=list)

    def to_dict_list(self) -> List[dict]:
        """Serialize steps for CSV/Apollo export."""
        return [
            {
                "company_name": self.company_name,
                "persona_role": self.persona_role,
                "persona_title": self.persona_title,
                "account_tier": self.account_tier,
                "primary_signal": self.primary_signal,
                "step_number": s.step_number,
                "day": s.day,
                "channel": s.channel,
                "subject": s.subject,
                "body": s.body,
                "notes": s.notes,
            }
            for s in self.steps
        ]


class OutreachSequenceGenerator:
    """
    Generates a complete multi-touch outreach sequence.

    Usage:
        gen = OutreachSequenceGenerator(vertical="healthcare")
        seq = gen.generate(account, outreach_package, persona)
    """

    def __init__(self, vertical: str = "healthcare"):
        self.vertical = vertical

    def generate(
        self,
        *,
        company_name: str,
        persona_role: str,
        persona_title: str,
        account_tier: str,
        primary_signal: str,
        evidence_excerpt: str,
        source_url: str,
        safe_first_line: str,
        pain_hypothesis: str,
        proof_point: str,
        recommended_cta: str,
        follow_up_angle: str,
        linkedin_note: str,
        email_subject_a: str,
        email_subject_b: str,
        adp_status: str = "",
        best_product: str = "Onboard",
    ) -> OutreachSequence:
        """Generate the full sequence."""

        product_line = {
            "Onboard": "HR Cloud Onboard replaces paper new-hire packets with a mobile-first digital workflow.",
            "Workmates": "HR Cloud Workmates gives your frontline team a digital communication and engagement channel.",
            "Onboard+Workmates": "HR Cloud Onboard digitizes onboarding, and Workmates keeps frontline employees connected after day one.",
        }.get(best_product, "HR Cloud replaces manual HR processes with a mobile-first digital workflow.")

        adp_line = ""
        if adp_status in ("confirmed", "strongly_likely"):
            adp_line = " It works alongside ADP — no payroll migration or rip-and-replace."

        steps = []

        # ── Step 1: Email 1 (Day 1) ──
        email_1_body = self._build_email_1(
            safe_first_line=safe_first_line,
            product_line=product_line,
            adp_line=adp_line,
            cta=recommended_cta,
        )
        steps.append(SequenceStep(
            step_number=1,
            day=1,
            channel="email",
            subject=email_subject_a,
            body=email_1_body,
            notes=(
                f"Tier: {account_tier}. Signal: {primary_signal}. "
                f"Source: {source_url or 'see CRM'}. "
                "Personalize [YOUR NAME] and [YOUR TITLE] before sending."
            ),
        ))

        # ── Step 2: LinkedIn touch (Day 2) ──
        steps.append(SequenceStep(
            step_number=2,
            day=2,
            channel="linkedin",
            subject=f"Connection request — {persona_title} at {company_name}",
            body=linkedin_note,
            notes=(
                f"Send connection request to {persona_title} at {company_name}. "
                "Customize {{first_name}} before sending. Keep under 300 chars."
            ),
        ))

        # ── Step 3: Email 2 (Day 4) ──
        email_2_body = self._build_email_2(
            company_name=company_name,
            proof_point=proof_point,
            follow_up_angle=follow_up_angle,
            cta=recommended_cta,
        )
        steps.append(SequenceStep(
            step_number=3,
            day=4,
            channel="email",
            subject=f"Re: {email_subject_a}",
            body=email_2_body,
            notes=(
                "Different angle from Email 1. Use social proof from same vertical. "
                "Do not repeat the Email 1 opener verbatim."
            ),
        ))

        # ── Step 4: Email 3 — Break-up (Day 9) ──
        email_3_body = self._build_email_3(
            company_name=company_name,
            product_line=product_line,
        )
        steps.append(SequenceStep(
            step_number=4,
            day=9,
            channel="email",
            subject=f"Closing the loop — {company_name}",
            body=email_3_body,
            notes=(
                "Break-up email. Warm but final. Compress to 2-3 sentences. "
                "No guilt. No desperation. Leave door open."
            ),
        ))

        return OutreachSequence(
            company_name=company_name,
            persona_role=persona_role,
            persona_title=persona_title,
            account_tier=account_tier,
            primary_signal=primary_signal,
            steps=steps,
        )

    def _build_email_1(
        self,
        safe_first_line: str,
        product_line: str,
        adp_line: str,
        cta: str,
    ) -> str:
        return (
            f"{safe_first_line}\n\n"
            f"{product_line}{adp_line}\n\n"
            f"{cta}\n\n"
            "— [YOUR NAME]\n"
            "[YOUR TITLE] | HR Cloud\n"
            "[PHONE] | hrcloud.com"
        )

    def _build_email_2(
        self,
        company_name: str,
        proof_point: str,
        follow_up_angle: str,
        cta: str,
    ) -> str:
        return (
            f"Wanted to share one quick data point before I follow up further.\n\n"
            f"{proof_point}\n\n"
            f"{follow_up_angle}\n\n"
            f"Applies directly to {company_name}. {cta}\n\n"
            "— [YOUR NAME]"
        )

    def _build_email_3(
        self,
        company_name: str,
        product_line: str,
    ) -> str:
        return (
            f"Last note from me on this.\n\n"
            f"{product_line} If the timing isn't right for {company_name} right now, "
            "completely understood — no response needed.\n\n"
            "When onboarding modernization becomes the priority, happy to pick this up.\n\n"
            "— [YOUR NAME]"
        )

    def generate_ab_subjects(self, primary_signal: str, company_name: str) -> tuple:
        """Generate A/B subject line variants."""
        subject_pairs = {
            "pdf_new_hire_packet": (
                f"New hire packet at {company_name}",
                f"Paper onboarding → {company_name}",
            ),
            "manual_onboarding": (
                f"Manual HR onboarding at {company_name}",
                f"Onboarding process question — {company_name}",
            ),
            "adp_confirmed": (
                f"{company_name} + ADP → onboarding layer",
                f"Adding to your ADP setup at {company_name}",
            ),
            "osha_citation": (
                f"OSHA documentation at {company_name}",
                f"Safety recordkeeping → {company_name}",
            ),
            "cms_deficiency": (
                f"CMS documentation at {company_name}",
                f"Survey-readiness at {company_name}",
            ),
            "new_hr_leader": (
                f"Quick win for your first 90 days at {company_name}",
                f"Welcome to {company_name} — a note",
            ),
            "caregiver_hiring_surge": (
                f"Caregiver onboarding at {company_name}",
                f"High-volume hiring → {company_name}",
            ),
            "grant_award": (
                f"Grant compliance → {company_name}",
                f"HR documentation for {company_name}'s new grant",
            ),
        }
        default = (
            f"HR onboarding at {company_name}",
            f"New hire process question — {company_name}",
        )
        return subject_pairs.get(primary_signal, default)
