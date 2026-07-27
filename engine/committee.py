"""
Buying Committee Mapper.
For every Tier 1/2 account, maps the likely buying committee and assigns
outreach priority. Multi-threading is non-negotiable for Tier 1 accounts.

Roles:
  Champion       — initiates/drives the evaluation (HR Director, CHRO, VP HR)
  Economic Buyer — budget authority (CFO, CEO, COO)
  Influencer     — daily user / internal advocate (HR Manager, Payroll Specialist)
  Blocker        — may slow or kill deal (IT Director, Legal/Compliance)
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class PersonaTarget:
    role: str                       # "champion", "economic_buyer", "influencer", "blocker"
    title_options: List[str]        # ordered by likelihood for this company type
    priority: int                   # 1=contact first, 2=second, etc.
    key_concerns: List[str]         # what they care about
    best_hook: str                  # one-sentence hook for this persona
    objection_to_prepare: str       # most likely pushback
    linkedin_note: str              # connection request note (< 300 chars)


# ── Persona definitions by vertical ──────────────────────────────────────────

COMMITTEE_TEMPLATES = {
    "healthcare": [
        PersonaTarget(
            role="champion",
            title_options=["Director of Human Resources", "VP of HR", "HR Director",
                           "Chief People Officer", "Director of People Operations"],
            priority=1,
            key_concerns=["caregiver turnover", "onboarding speed", "credential tracking",
                          "CMS compliance", "paper burden"],
            best_hook="Your caregiver new hire packet is still on paper — we move it to mobile, completed before day one.",
            objection_to_prepare="We already have ADP / We're implementing a new system",
            linkedin_note="Hi {first_name} — noticed {company} is actively hiring caregivers. I work with home health and senior care teams replacing paper new-hire packets with digital onboarding. Happy to share what similar orgs are doing.",
        ),
        PersonaTarget(
            role="economic_buyer",
            title_options=["Chief Executive Officer", "COO", "Chief Operating Officer",
                           "Administrator", "Executive Director"],
            priority=2,
            key_concerns=["turnover cost", "compliance risk", "operational efficiency",
                          "CMS star rating", "cost per hire"],
            best_hook="Every caregiver you lose in the first 90 days costs $3,000-5,000. Better onboarding cuts that in half.",
            objection_to_prepare="We don't have budget for new software",
            linkedin_note="Hi {first_name} — we help {industry} operators reduce caregiver first-90-day turnover through better digital onboarding. Worth a quick conversation?",
        ),
        PersonaTarget(
            role="influencer",
            title_options=["HR Manager", "HR Coordinator", "Recruiter", "Staffing Coordinator",
                           "HR Generalist"],
            priority=3,
            key_concerns=["paperwork time", "day-one readiness", "compliance checklists",
                          "background check tracking"],
            best_hook="Stop printing new hire packets. Your new caregivers complete everything on their phone before day one.",
            objection_to_prepare="My manager would need to approve this",
            linkedin_note="Hi {first_name} — I help HR coordinators at home health agencies eliminate paper new-hire packets. Would love to show you what it looks like.",
        ),
    ],

    "education": [
        PersonaTarget(
            role="champion",
            title_options=["Director of Human Resources", "Assistant Superintendent of HR",
                           "Chief Human Resources Officer", "HR Director"],
            priority=1,
            key_concerns=["back-to-school hiring surge", "substitute teacher onboarding",
                          "credential verification", "I-9 compliance"],
            best_hook="August is your highest-volume hiring month — HR Cloud moves teacher onboarding from 2 days to 20 minutes.",
            objection_to_prepare="We use Frontline / We're going through budget approval",
            linkedin_note="Hi {first_name} — I work with school district HR teams that process 200+ new hires in August. We replace the paper packet process with mobile onboarding. Happy to share a quick overview.",
        ),
        PersonaTarget(
            role="economic_buyer",
            title_options=["Superintendent", "Deputy Superintendent", "CFO",
                           "Assistant Superintendent of Finance", "Business Manager"],
            priority=2,
            key_concerns=["cost efficiency", "board accountability", "compliance", "ESSER spend"],
            best_hook="ESSER funds can cover HR modernization — most districts leave this on the table.",
            objection_to_prepare="We need board approval / We're in budget season",
            linkedin_note="Hi {first_name} — helping districts use ESSER and Title I funding for HR modernization before deadlines. Worth a 15-min conversation?",
        ),
        PersonaTarget(
            role="influencer",
            title_options=["HR Specialist", "HR Coordinator", "Payroll Specialist",
                           "Benefits Coordinator"],
            priority=3,
            key_concerns=["form collection", "fingerprint tracking", "data entry volume"],
            best_hook="Stop chasing paper W-4s and I-9s during back-to-school. All of it moves to digital.",
            objection_to_prepare="We have a process that works",
            linkedin_note="Hi {first_name} — I help HR coordinators at school districts automate the August onboarding surge. Happy to show you how.",
        ),
    ],

    "manufacturing": [
        PersonaTarget(
            role="champion",
            title_options=["VP of Human Resources", "Director of HR", "CHRO",
                           "HR Director", "Director of People Operations"],
            priority=1,
            key_concerns=["OSHA compliance", "turnover at the plant level", "multi-site HR",
                          "onboarding speed for hourly workers"],
            best_hook="Your OSHA training records are still on paper — HR Cloud creates a digital audit trail that survives any inspection.",
            objection_to_prepare="We have ADP / We handle this with our ERP",
            linkedin_note="Hi {first_name} — I work with plant HR teams that need OSHA-defensible onboarding documentation across multiple sites. Happy to share what others in {industry} are doing.",
        ),
        PersonaTarget(
            role="economic_buyer",
            title_options=["CEO", "COO", "VP of Operations", "Plant Manager (multi-site)"],
            priority=2,
            key_concerns=["OSHA fine exposure", "productivity loss from turnover",
                          "compliance risk", "cost per hire"],
            best_hook="An OSHA recordkeeping violation averages $15,000 per citation. Digital onboarding makes your training documentation inspection-proof.",
            objection_to_prepare="Our HR team handles compliance",
            linkedin_note="Hi {first_name} — helping manufacturing ops leaders eliminate OSHA recordkeeping risk through digital employee onboarding. Worth a quick call?",
        ),
        PersonaTarget(
            role="influencer",
            title_options=["HR Generalist", "HR Coordinator", "Safety Manager", "Payroll Specialist"],
            priority=3,
            key_concerns=["paper filing", "safety acknowledgment tracking", "I-9 compliance"],
            best_hook="Track safety acknowledgments, I-9s, and training completions in one place — no clipboards, no paper files.",
            objection_to_prepare="We're already doing this in ADP",
            linkedin_note="Hi {first_name} — I help HR generalists at manufacturing plants go paperless for new hire onboarding and safety docs. Happy to show you a quick demo.",
        ),
    ],

    "nonprofit": [
        PersonaTarget(
            role="champion",
            title_options=["Director of Human Resources", "HR Director", "VP of HR",
                           "Director of People", "Chief People Officer"],
            priority=1,
            key_concerns=["lean HR team", "grant compliance", "onboarding volume", "paper burden"],
            best_hook="You're a one or two-person HR team onboarding 50+ people a year — digital onboarding gets you 2 hours back per new hire.",
            objection_to_prepare="We don't have budget",
            linkedin_note="Hi {first_name} — I work with nonprofit HR teams that onboard at high volume with small staff. We eliminate the paper packet process. Worth a quick chat?",
        ),
        PersonaTarget(
            role="economic_buyer",
            title_options=["Executive Director", "CEO", "CFO", "COO"],
            priority=2,
            key_concerns=["grant compliance", "audit readiness", "cost efficiency"],
            best_hook="Grant funders increasingly require digital employee documentation. HR Cloud keeps your records audit-ready.",
            objection_to_prepare="We're a nonprofit — budget is tight",
            linkedin_note="Hi {first_name} — helping nonprofit leaders make the case for HR modernization as a grant compliance investment. Happy to share how others have funded it.",
        ),
        PersonaTarget(
            role="influencer",
            title_options=["HR Coordinator", "Operations Manager", "Office Manager"],
            priority=3,
            key_concerns=["admin burden", "new hire paperwork", "filing"],
            best_hook="Stop managing paper personnel files. Everything lives in one digital system your whole team can access.",
            objection_to_prepare="This would take time to set up",
            linkedin_note="Hi {first_name} — I help nonprofit coordinators ditch the paper HR file cabinet. Happy to show you a quick overview.",
        ),
    ],

    "government": [
        PersonaTarget(
            role="champion",
            title_options=["Director of Human Resources", "HR Director", "Civil Service Director",
                           "Personnel Director"],
            priority=1,
            key_concerns=["procurement compliance", "onboarding consistency", "audit trail",
                          "union documentation"],
            best_hook="We've helped county HR departments go from 3-day paper onboarding to same-day digital — within existing procurement frameworks.",
            objection_to_prepare="We need to go through procurement / RFP process",
            linkedin_note="Hi {first_name} — I work with county and municipal HR teams modernizing their onboarding process. We're on several state contract vehicles. Worth a quick conversation?",
        ),
        PersonaTarget(
            role="economic_buyer",
            title_options=["County Manager", "City Manager", "CAO", "CFO"],
            priority=2,
            key_concerns=["cost savings", "compliance risk", "constituent service efficiency"],
            best_hook="Digital onboarding reduces new hire processing time by 70% — measurable efficiency gain for your annual budget report.",
            objection_to_prepare="We have IT/procurement constraints",
            linkedin_note="Hi {first_name} — helping local government leaders build the efficiency case for HR modernization. Happy to share ROI data from similar entities.",
        ),
        PersonaTarget(
            role="influencer",
            title_options=["HR Specialist", "HR Generalist", "Payroll Coordinator"],
            priority=3,
            key_concerns=["paperwork processing", "compliance tracking", "data entry"],
            best_hook="Stop re-entering new hire data from paper forms into your payroll system. It flows automatically.",
            objection_to_prepare="Change is hard here / IT would need to approve",
            linkedin_note="Hi {first_name} — I help government HR specialists eliminate manual data entry from new hire onboarding. Happy to show you how.",
        ),
    ],
}

# Default template for unrecognized verticals
COMMITTEE_TEMPLATES["default"] = COMMITTEE_TEMPLATES["nonprofit"]


def map_buying_committee(vertical: str, company_name: str,
                          signals: list = None) -> List[PersonaTarget]:
    """Return ordered buying committee for an account."""
    template = COMMITTEE_TEMPLATES.get(vertical, COMMITTEE_TEMPLATES["default"])
    # Personalize the linkedin_note for this company
    personalized = []
    for persona in template:
        p = PersonaTarget(
            role=persona.role,
            title_options=persona.title_options,
            priority=persona.priority,
            key_concerns=persona.key_concerns,
            best_hook=persona.best_hook,
            objection_to_prepare=persona.objection_to_prepare,
            linkedin_note=persona.linkedin_note.replace(
                "{company}", company_name
            ).replace("{industry}", vertical),
        )
        personalized.append(p)
    return sorted(personalized, key=lambda x: x.priority)


def champion_title(vertical: str) -> str:
    committee = map_buying_committee(vertical, "")
    champs = [p for p in committee if p.role == "champion"]
    if champs:
        return champs[0].title_options[0]
    return "Director of Human Resources"


def economic_buyer_title(vertical: str) -> str:
    committee = map_buying_committee(vertical, "")
    buyers = [p for p in committee if p.role == "economic_buyer"]
    if buyers:
        return buyers[0].title_options[0]
    return "CEO"
