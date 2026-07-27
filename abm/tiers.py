"""
Account tier classification and action routing.

Tier 1 (score ≥ 80): Signal-confirmed, ICP-perfect.
  → Personalized 1:1 sequence. Multi-thread immediately.
  → Contact champion + economic buyer within 48 hours.

Tier 2 (score 60-79): Good fit, directional signal.
  → Semi-personalized sequence. Contact champion only.
  → Needs one more confirming signal before Tier 1 upgrade.

Tier 3 (score 40-59): Weak signal or fit gap.
  → Monitor only. Add to nurture list. Re-score in 30 days.
  → Do NOT send cold outreach yet.

Disqualified (< 40 or hard gate fails):
  → Drop from pipeline. Log reason.
"""
from dataclasses import dataclass


TIER_ACTIONS = {
    "Tier 1": {
        "outreach_type": "personalized_1to1",
        "sequence_length": 3,
        "linkedin": True,
        "contacts_to_target": ["champion", "economic_buyer"],
        "urgency": "within 48 hours",
        "next_action": "Send personalized email to champion + economic buyer. Multi-thread.",
        "apollo_sequence": "ABM Tier 1 — Personalized",
    },
    "Tier 2": {
        "outreach_type": "semi_personalized",
        "sequence_length": 3,
        "linkedin": True,
        "contacts_to_target": ["champion"],
        "urgency": "within 1 week",
        "next_action": "Send semi-personalized email to champion. Find second confirming signal.",
        "apollo_sequence": "ABM Tier 2 — Semi-Personalized",
    },
    "Tier 3": {
        "outreach_type": "nurture_only",
        "sequence_length": 0,
        "linkedin": False,
        "contacts_to_target": [],
        "urgency": "re-score in 30 days",
        "next_action": "Add to nurture list. Set 30-day re-score reminder.",
        "apollo_sequence": "ABM Nurture",
    },
    "Disqualified": {
        "outreach_type": "none",
        "sequence_length": 0,
        "linkedin": False,
        "contacts_to_target": [],
        "urgency": "N/A",
        "next_action": "Log rejection reason. Do not contact.",
        "apollo_sequence": None,
    },
}


@dataclass
class TierDecision:
    tier: str
    outreach_type: str
    sequence_length: int
    linkedin: bool
    contacts_to_target: list
    urgency: str
    next_action: str
    apollo_sequence: str | None


def classify(composite_score: int, rejection_reason: str = "") -> TierDecision:
    if rejection_reason:
        tier = "Disqualified"
    elif composite_score >= 80:
        tier = "Tier 1"
    elif composite_score >= 60:
        tier = "Tier 2"
    elif composite_score >= 40:
        tier = "Tier 3"
    else:
        tier = "Disqualified"

    action = TIER_ACTIONS[tier]
    return TierDecision(
        tier=tier,
        outreach_type=action["outreach_type"],
        sequence_length=action["sequence_length"],
        linkedin=action["linkedin"],
        contacts_to_target=action["contacts_to_target"],
        urgency=action["urgency"],
        next_action=action["next_action"],
        apollo_sequence=action["apollo_sequence"],
    )
