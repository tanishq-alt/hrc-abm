---
name: buying-committee-mapper
title: HR Cloud Buying Committee Mapper
description: "Use this skill after an account passes qualification to map the smallest useful buying committee for the relevant HR Cloud workflow. It prioritizes known relationships, maps champion/economic buyer/influencer/blocker roles, uses vertical-specific title aliases, avoids indiscriminate contact enrichment, and returns why each person belongs."
category: Prospecting
---

# HR Cloud Buying Committee Mapper

## Purpose

Find the people who own, feel, approve, evaluate, or can block the workflow
identified by the signal.

The job is not to collect every HR title.

## Inputs

- qualified account;
- primary signal;
- primary HR Cloud product;
- company size;
- vertical;
- relationship history;
- CRM suppression;
- available people sources.

## Order of Operations

1. Search known relationships.
2. Search former customers or champions.
3. Search current account contacts.
4. Search current employees by persona.
5. Enrich only the selected contacts.
6. Deduplicate against active sequences and open deals.

## Buying Roles

### Champion

Initiates or owns evaluation.

Common titles:

- HR Director;
- VP HR;
- Head of People;
- Director of People;
- Director of Talent;
- Talent Acquisition Director;
- HRIS Director;
- Onboarding Manager;
- Credentialing Director;
- L&D Director;
- Employee Experience Director.

### Economic Buyer

Approves budget or strategic change.

Common titles:

- CHRO;
- Chief People Officer;
- COO;
- CFO;
- CEO;
- Administrator;
- VP Operations;
- superintendent or district executive;
- CIO for technical governance.

### Influencer or User

Feels the operational pain.

Common titles:

- HR Manager;
- HR Generalist;
- HR Coordinator;
- Recruiter;
- Payroll Manager;
- Onboarding Specialist;
- Credentialing Specialist;
- Training Manager;
- Internal Communications;
- People Operations.

### Evaluator or Blocker

Controls technical, legal, compliance, procurement, or security approval.

Common titles:

- HRIS;
- IT Director;
- CIO;
- Information Security;
- Legal;
- Compliance;
- Procurement;
- Payroll;
- Data Privacy.

## Product-Specific Persona Map

### Recruit

- Champion: TA Director, Recruiting Manager
- Economic buyer: VP Talent, CHRO
- User: Recruiter, Coordinator
- Evaluator: HRIS, IT

### Onboard and Maya

- Champion: HR Director, People Operations, Onboarding Manager
- Economic buyer: CHRO, COO
- User: HR Manager, Generalist, Coordinator
- Evaluator: HRIS, IT, Legal/Compliance

### Credential Tracking and Train

- Champion: Compliance, Credentialing, L&D, HR
- Economic buyer: CHRO, COO, Administrator
- User: Credentialing Specialist, Training Manager
- Evaluator: Legal, Compliance, Operations

### Workmates

- Champion: Employee Experience, Internal Communications, HR
- Economic buyer: CHRO, COO
- User: HR Manager, Communications, Location Managers
- Evaluator: IT, Security

### People and Time Products

- Champion: HRIS, HR Operations, Payroll
- Economic buyer: CHRO, CFO, COO
- User: HR Manager, Payroll, Supervisors
- Evaluator: IT, Finance, Legal

## Vertical-Specific Titles

### Healthcare

- Administrator;
- Director of Nursing where operationally relevant;
- HR Director;
- VP People;
- Credentialing Manager;
- Clinical Compliance;
- Talent Acquisition;
- Workforce Operations.

### Manufacturing

- Plant HR Manager;
- Regional HR;
- VP Operations;
- Safety and Training;
- Workforce Development;
- HRIS;
- Plant Manager as influencer.

### Education

- Chief Human Resources Officer;
- Assistant Superintendent HR;
- Director of Human Resources;
- Director of Talent;
- Certification;
- Payroll;
- IT;
- Procurement.

### Government

- HR Director;
- HRIS Project Manager;
- Procurement Officer;
- CIO;
- Finance Director;
- City/County Administrator.

### Retail and Hospitality

- VP People;
- Regional HR;
- Director of Field HR;
- Talent Acquisition;
- Learning;
- Internal Communications;
- Operations.

## Contact Caps

### Tier 1

Map three to five:

- champion;
- economic buyer;
- optional user/influencer;
- optional evaluator/blocker.

### Tier 2

Map one champion. Add the economic buyer only after upgrade or manual
selection.

### Tier 3

Do not pay for contact enrichment. Store title hypotheses only.

## Relationship Priority

Highest to lowest:

1. proven customer champion who moved;
2. prior buyer or responder;
3. prior meeting attendee;
4. mutual relationship or referral;
5. new-in-role buyer;
6. net-new contact.

Record relationship strength and last touch.

## Output

```yaml
contacts:
  - full_name:
    title:
    linkedin_url:
    email:
    email_status:
    buying_role:
    persona_fit:
    relationship_strength:
    last_touch:
    inclusion_reason:
    relevant_signal_angle:
    likely_objection:
    duplicate_or_suppression:
role_gaps:
recommended_first_contact:
multithread_plan:
```

## Hard Rules

- Account passes before people search.
- Every contact has an inclusion reason.
- No broad title dump.
- No more than five contacts per account.
- No duplicate outreach.
- No enrichment of Tier 3 contacts.
- Former contacts who moved are retained as high-value paths.
- Warm and cold contacts are never treated the same.
