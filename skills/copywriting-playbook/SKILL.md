# HR Cloud Signal-Led Personalized Outbound Copywriting Playbook

## Version

**Purpose:** Production-grade copywriting system for turning Apollo CSV exports into personalized HR Cloud outbound email sequences.

**Primary use:** Upload this playbook together with the broader HR Cloud GTM playbook and an Apollo CSV. The AI should use this document as the operating standard for research, personalization, message strategy, copy generation, quality control, and CSV output.

**Default sequence:** Three emails.

**Default channel:** Cold email.

**Default market:** United States and Canada.

**Default language:** English.

---

# 1. What This Playbook Is Designed to Prevent

Most AI-generated outbound fails for predictable reasons:

1. It mistakes a company description for personalization.
2. It invents signals that are not in the data.
3. It writes the same email to every lead.
4. It mentions every product instead of one relevant use case.
5. It uses a strategic message for an operational buyer, or vice versa.
6. It treats a weak lead as if clever copy can make the account valuable.
7. It asks for a meeting before earning interest.
8. It exposes tracking signals and sounds invasive.
9. It uses unsupported statistics, product claims, integrations, or customer results.
10. It produces a sample instead of completing the CSV.
11. It drops rows, changes original data, or corrupts multiline CSV cells.
12. It optimizes for open rates instead of positive replies and qualified conversations.

This playbook installs controls against every one of those failure modes.

---

# 2. The Copywriting Operating Doctrine

## 2.1 The Big Three

Campaign performance is determined in this order:

1. **List quality**
2. **Offer quality**
3. **Copy quality**

A useful operating model is:

- List: 40%
- Offer: 40%
- Copy: 20%

These percentages are directional, not scientific constants. Their purpose is to force correct diagnosis.

When a campaign performs poorly, investigate in this order:

1. Are these the right companies?
2. Are these the right people?
3. Is there a credible reason to contact them now?
4. Is the offer relevant and easy to evaluate?
5. Only then, is the copy weak?

Never use better wording to hide bad targeting.

## 2.2 Truth Over Personalization Theatre

A plain but accurate email is better than a highly personalized lie.

The system must never invent:

- A pain.
- A vendor.
- A technology.
- A hiring plan.
- A current initiative.
- A business event.
- A quote.
- A customer result.
- A benchmark.
- A location count.
- An employee count.
- A compliance issue.
- A manual process.
- A relationship.
- A product feature.
- An integration.
- A timeline.

When evidence is incomplete, write a question or a hypothesis.

**Bad:**

> Your team is manually transferring candidate data into onboarding.

**Better:**

> Once a candidate accepts, does the record move into onboarding automatically, or does HR still have to recreate parts of it?

## 2.3 One Person, One Problem, One Product, One Ask

Each email should do one job.

A strong email contains:

- One recipient.
- One reason it is relevant.
- One operational or strategic problem.
- One HR Cloud product or workflow.
- One credible outcome.
- One CTA.

Do not turn an email into a product catalogue.

## 2.4 Give Before Asking

The recipient should gain something useful from the message even if they never reply.

Useful value can include:

- A specific observation.
- A relevant workflow insight.
- A short benchmark from approved source material.
- A checklist.
- A two-minute walkthrough.
- A workflow map.
- A mini-audit.
- A relevant case study.
- A short implementation example.
- A three-month pilot.

Weak “value” includes:

- “I would love to show you our platform.”
- “We have a few ideas.”
- “Can I tell you more?”
- “Can we schedule 30 minutes?”

## 2.5 Relevance Beats Volume

A signal-led message to a well-matched account should outperform a generic message sent at scale.

The purpose of automation is not to send the same email faster. It is to produce controlled variation around real account context.

## 2.6 Specific Beats Clever

Prefer:

- “move accepted candidates directly into onboarding”
- “track license expirations alongside employee records”
- “let frontline hires complete forms from a phone”
- “confirm important announcements were read”

Avoid:

- “transform your HR”
- “revolutionize employee experience”
- “unlock efficiency”
- “leverage cutting-edge AI”
- “seamless end-to-end ecosystem”

---

# 3. How to Use This Playbook

The AI receives three input types.

## 3.1 Required Inputs

1. **The HR Cloud GTM playbook**
2. **This copywriting playbook**
3. **An Apollo CSV**

## 3.2 Optional Inputs

- Campaign objective.
- Target industry.
- Target persona.
- Product focus.
- Approved offer.
- Customer proof.
- Exclusions.
- Geography.
- Employee range.
- Required sequence length.
- Word-count requirements.
- Tone rules.
- Signature rules.
- Trial eligibility.
- ADP-specific instructions.

## 3.3 Source-of-Truth Order

When information conflicts, use this order:

1. Current user instruction.
2. HR Cloud GTM playbook.
3. This copywriting playbook.
4. Verified CSV data.
5. Verified public evidence.
6. Approved HR Cloud industry hypotheses.
7. Conservative fallback.

---

# 4. Campaign Brief Template

Before writing, construct this campaign brief internally.

## 4.1 Campaign Definition

- Campaign name:
- Primary objective:
- Product focus:
- Offer:
- Primary industry:
- Secondary industries:
- Employee range:
- Geography:
- Primary persona:
- Secondary personas:
- Signal requirement:
- Account tier:
- Sequence length:
- Send platform:
- Signature policy:
- CTA style:
- Proof points allowed:
- Claims prohibited:
- Customer names allowed:
- ADP mention allowed:
- Pilot eligibility:
- Links allowed:
- Manual review threshold:

## 4.2 Campaign Thesis

Complete this sentence:

> Companies showing **[observable situation]** are likely dealing with **[operational consequence]**. HR Cloud helps **[persona]** reach **[credible outcome]** through **[specific product or workflow]**.

Example:

> Multi-location healthcare companies hiring licensed staff are likely dealing with document collection and credential follow-up across separate workflows. HR Cloud helps HR teams collect onboarding documents, track expiration dates, and alert employees and managers before credentials lapse.

## 4.3 False-Positive Definition

Before generating copy, define what would make a company look relevant but actually be a bad target.

Examples:

- A healthcare company with no employees and only independent practitioners.
- A company hiring one employee, not experiencing a hiring surge.
- A job posting that mentions ADP as a desired skill but does not prove current ADP use.
- A multi-location brand where locations are franchises and HR is decentralized.
- A company that is already an HR Cloud customer.
- A payroll consultant rather than an employer.
- A current vendor, partner, competitor, student, or job seeker.

---

# 5. Apollo CSV Processing Standard

## 5.1 Preserve the Source

The final CSV must:

- Preserve every original row.
- Preserve original row order.
- Preserve every original column.
- Preserve original values.
- Add new columns to the right.
- Never merge two leads.
- Never remove a row silently.
- Never change an email address.
- Never overwrite source fields with generated fields.

Input and output row counts must match.

## 5.2 Detect Common Apollo Columns

Map variations automatically.

| Canonical field | Common Apollo columns |
|---|---|
| First name | First Name, first_name, Contact First Name |
| Last name | Last Name, last_name |
| Full name | Name, Full Name, Contact Name |
| Title | Title, Job Title, Position |
| Company | Company, Company Name, Organization |
| Domain | Website, Domain, Company Website |
| Industry | Industry, Company Industry |
| Employees | Employees, Employee Count, Company Headcount |
| Email | Email, Work Email, Business Email |
| Person LinkedIn | Person LinkedIn URL, LinkedIn URL |
| Company LinkedIn | Company LinkedIn URL, Organization LinkedIn |
| Location | City, State, Country, Contact Location |
| Technologies | Technologies, Tech Stack, Company Technologies |
| Description | Company Description, Short Description, Keywords |
| Intent | Intent, Buying Intent, Signal, Topic |
| Funding | Funding, Total Funding, Latest Funding |
| Seniority | Seniority, Management Level |
| Department | Department, Function |

## 5.3 Required Generated Columns

### Research and strategy

- `hrc_persona`
- `hrc_buying_role`
- `hrc_seniority`
- `hrc_message_altitude`
- `hrc_account_tier`
- `hrc_icp_fit`
- `hrc_industry_segment`
- `hrc_workforce_type`
- `hrc_primary_product`
- `hrc_secondary_product`
- `hrc_primary_pain`
- `hrc_pain_confidence`
- `hrc_signal_type`
- `hrc_signal_strength`
- `hrc_signal_evidence`
- `hrc_signal_source_url`
- `hrc_signal_date`
- `hrc_signal_safe_to_mention`
- `hrc_personalization_bucket`
- `hrc_personalization_depth`
- `hrc_personalization_hook`
- `hrc_offer_angle`
- `hrc_proof_point`
- `hrc_copy_framework`
- `hrc_research_summary`

### Copy

- `hrc_subject_1`
- `hrc_email_1`
- `hrc_subject_2`
- `hrc_email_2`
- `hrc_subject_3`
- `hrc_email_3`

### QA and routing

- `hrc_copy_score`
- `hrc_copy_confidence`
- `hrc_do_not_send`
- `hrc_manual_review`
- `hrc_qa_flags`

## 5.4 Missing Data Rules

- Missing first name: omit greeting.
- Missing company: mark do-not-send unless the domain or email clearly resolves it.
- Missing employee count: continue only if industry, domain, and role provide enough fit evidence.
- Missing industry: infer only from verified company description or website evidence.
- Missing signal: use role and industry relevance, then mark `weak_signal`.
- Missing proof: omit proof rather than inventing it.
- Missing email: preserve row, mark do-not-send for email activation.

---

# 6. Lead Qualification Before Copywriting

## Gate 1: Contactability

Check:

- Person exists.
- Company exists.
- Email exists.
- Email is usable.
- Lead is not unsubscribed.
- Lead is not on a do-not-contact list.
- Lead is not a current customer unless the campaign is expansion.
- Lead is not a vendor or competitor.
- Lead is not a student or unrelated job seeker.

## Gate 2: ICP Fit

Evaluate:

- Industry.
- Employee count.
- Geography.
- Workforce type.
- Hiring volume.
- Multi-location complexity.
- Frontline or mobile workforce.
- HR workflow complexity.
- Product relevance.

Employee count alone is not ICP fit.

## Gate 3: Persona Fit

Determine whether the contact is:

- Economic buyer.
- Champion.
- Evaluator.
- User.
- Influencer.
- Passdown target.
- Wrong person.

## Gate 4: Signal Quality

Separate:

- Company fit.
- Signal strength.
- Contact quality.
- Contactability.

A strong signal cannot rescue a bad account.

## Gate 5: Product Fit

Choose one primary product with the shortest logical distance from the evidence.

## Gate 6: Approval Risk

Manual review is required for:

- Senior executives at large companies.
- Tier A accounts.
- Sensitive public events.
- Competitive displacement.
- Weak evidence combined with strong claims.
- Multiple contacts at the same account.
- Healthcare compliance claims.
- ADP partner-language uncertainty.
- Customer proof involving named brands.

---

# 7. HR Cloud Messaging Foundation

## 7.1 Master Positioning

HR Cloud extends the employee workflow around existing payroll and HR systems.

The message should usually focus on one of these outcomes:

- Connect recruiting to onboarding.
- Reduce manual new-hire follow-up.
- Standardize onboarding across locations.
- Support mobile and frontline completion.
- Track credentials and readiness.
- Improve employee communication and recognition.
- Centralize employee records and documents.
- Assign training and track completion.
- Improve visibility without replacing payroll.

## 7.2 Product Rule

Do not lead with “HR Cloud is an all-in-one HR platform.”

That framing is too broad.

Lead with the workflow the recipient owns.

## 7.3 Existing-System Rule

Never assume the current HRIS or payroll platform.

Use:

- “your existing payroll”
- “your current HRIS”
- “the systems you already use”
- “without replacing payroll”
- “alongside your current process”

Only name a vendor when verified.

---

# 8. Product-to-Pain Copy Map

## 8.1 HR Cloud Onboard

### Use when

- New-hire forms are manual.
- HR chases documents.
- Onboarding differs by location.
- Candidate data is recreated.
- Managers lack status visibility.
- Frontline hires need mobile access.
- Rehires or internal transfers create duplicate work.

### Buyer language

- “forms”
- “documents”
- “tasks”
- “new-hire status”
- “offer to Day 1”
- “manager follow-up”
- “mobile completion”
- “re-entering employee information”

### Desired outcomes

- One repeatable onboarding workflow.
- Faster completion.
- Better visibility.
- Less manager chasing.
- Fewer manual handoffs.
- Existing payroll stays in place.

### Avoid

- “fully autonomous onboarding”
- “guaranteed compliance”
- “replace your HRIS”
- “zero-touch HR”

## 8.2 Maya AI Onboarding Agent

### Use when

- New hires ask repetitive questions.
- Managers explain the same process.
- Employees do not use portals consistently.
- The workforce is frontline, mobile, or distributed.
- Day 1 through Day 30 guidance is inconsistent.

### Buyer language

- “new-hire questions”
- “text-led onboarding”
- “SMS or email guidance”
- “first 30 days”
- “mobile access”
- “approved company information”
- “task reminders”

### Desired outcomes

- A personal guide for each new hire.
- Fewer repetitive questions.
- More consistent guidance.
- Better completion without another complex login.

### Avoid

- “replaces HR”
- “makes employment decisions”
- “unrestricted AI advice”
- “handles PHI”
- “fully autonomous”

## 8.3 Recruit and AI Hiring Agent

### Use when

- Recruiting and onboarding are disconnected.
- Accepted candidates are recreated in another system.
- Candidate communication is slow.
- Interviews and offers are spread across tools.
- Hiring volume is increasing.

### Buyer language

- “candidate to new hire”
- “offer acceptance”
- “interview scheduling”
- “candidate communication”
- “offer letters”
- “hiring stages”
- “handoff into onboarding”

### Desired outcomes

- One process from application to Day 1.
- Faster candidate communication.
- No duplicate employee record creation.
- Better visibility across recruiting stages.

## 8.4 Workmates

### Use when

- Employees do not all use corporate email.
- Teams are distributed.
- Important announcements are missed.
- Recognition is inconsistent.
- Employee feedback is hard to collect.
- Locations feel disconnected.

### Buyer language

- “frontline communication”
- “mandatory read”
- “recognition”
- “employee feedback”
- “mobile announcements”
- “distributed teams”
- “engagement across locations”

### Desired outcomes

- Reach more employees.
- Confirm critical messages are read.
- Make recognition visible.
- Give employees one place to connect.

## 8.5 People HRIS

### Use when

- Employee records are scattered.
- Document access is inconsistent.
- HR uses spreadsheets.
- Permissions matter.
- Credential reminders are separate.
- Organization data is hard to maintain.

### Desired outcomes

- Central employee record.
- Role-based access.
- Better document visibility.
- Cleaner audit history.
- Less spreadsheet tracking.

## 8.6 Healthcare Credential Tracking

### Use when

- Licenses expire.
- Certifications are tracked manually.
- Employees work across states.
- Audit preparation is difficult.
- Scheduling depends on readiness.
- Onboarding and credentials are separate.

### Desired outcomes

- Collect credentials during onboarding.
- Alert managers and employees before expiration.
- Improve audit readiness.
- Give HR one view of readiness.

### Compliance caution

Do not claim HIPAA certification.

Do not imply AI workflows should contain protected health information.

## 8.7 HR Cloud Train

### Use when

- Training is assigned at hire.
- Policies require acknowledgement.
- Employees need recurring safety or compliance training.
- Managers need readiness visibility.
- Policy documents need to become learning content.

### Desired outcomes

- Auto-assign training.
- Track completion.
- Send renewal reminders.
- Connect onboarding and readiness.

## 8.8 Time Off, Time Clock, Shift Planner, Perform, Assets

Use only with direct relevance.

- **Time Off:** approval visibility, shared calendars, absence visibility.
- **Time Clock:** hourly employees, approvals, timesheets, overtime.
- **Shift Planner:** shift work, open shifts, credential-based assignments.
- **Perform:** reviews, goals, 9-box, peer feedback.
- **Assets:** devices, uniforms, equipment, onboarding and offboarding handoffs.

---

# 9. Persona and Buying-Committee Playbooks

## 9.1 CEO and COO

### Cares about

- Operating consistency.
- Scale.
- Risk.
- Workforce readiness.
- Growth without adding administrative headcount.
- Multi-location control.

### Message altitude

Strategic.

### Good angles

- Standardizing onboarding across locations.
- Supporting growth without creating more manual handoffs.
- Reducing operational dependence on individual managers.
- Creating one employee workflow around existing systems.

### Avoid

- Small form-level details.
- Feature lists.
- Asking about spreadsheet tabs.
- Overly technical product explanations.

### CTA

- “Worth comparing how other multi-location teams structure this?”
- “Open to the two-minute version?”

## 9.2 CHRO, Chief People Officer, VP HR, VP People

### Cares about

- Employee experience.
- Risk.
- Standardization.
- Compliance.
- Time-to-productivity.
- HR operating leverage.
- System strategy.

### Good angles

- Recruiting-to-onboarding connection.
- Consistent employee journey.
- AI with company-controlled knowledge.
- Mobile completion for frontline workforces.
- Workforce readiness and credential visibility.

### Avoid

- Minor administrative complaints.
- “Save three hours per week” unless verified.
- Implying they personally process forms.

## 9.3 HR Director

Classify as strategic or operational based on company size.

### Small or mid-sized company

Usually hands-on.

Focus on:

- Manager follow-up.
- New-hire status.
- Documents.
- System handoffs.

### Large company

More strategic.

Focus on:

- Standardization.
- governance.
- Location consistency.
- Reporting.
- Risk.

## 9.4 HR Manager, HR Generalist, People Operations

### Cares about

- Chasing people.
- Missing documents.
- Email threads.
- Data entry.
- Status visibility.
- Manager coordination.
- Repetitive questions.

### Best copy

Concrete, practical, immediate.

### CTA

- “Should I send the workflow?”
- “Would the checklist be useful?”
- “Worth seeing how the reminders work?”

## 9.5 Talent Acquisition and Recruiting

### Cares about

- Candidate experience.
- Interview scheduling.
- Hiring stages.
- Offer letters.
- Accepted-candidate handoff.
- Recruiter-to-HR coordination.

### Best products

Recruit and Onboard.

### Avoid

- Employee recognition.
- Performance reviews.
- Broad HRIS claims.

## 9.6 HRIS and IT

### Cares about

- Integrations.
- Data flow.
- Access control.
- Governance.
- Duplicate records.
- System ownership.
- Security.
- Implementation.

### Good angles

- Existing payroll stays in place.
- Controlled data handoff.
- Role-based access.
- Fewer manual transfers.
- Approved AI knowledge sources.
- Centralized controls.

### Avoid

- Vague culture language.
- Unverified technical claims.
- Claiming a specific integration unless approved.

## 9.7 Payroll

### Cares about

- Accurate employee data.
- Clean handoff.
- No duplicate entry.
- Payroll system stability.
- Fewer upstream errors.

### Good angle

HR Cloud improves the process before payroll without replacing payroll.

### Avoid

Attacking the payroll provider.

## 9.8 Operations

### Cares about

- Readiness.
- Location consistency.
- Manager execution.
- Staffing.
- Shift coverage.
- Frontline communication.
- Equipment and training.

### Best products

Onboard, Maya, Workmates, Train, Time Clock, Shift Planner, Assets.

## 9.9 Learning, Compliance, Credentialing

### Cares about

- Required training.
- Expiration.
- Renewal.
- Documentation.
- Audit preparation.
- Readiness.

### Best products

Train, Credential Tracking, Onboard, People.

## 9.10 Employee Experience and Internal Communications

### Cares about

- Reach.
- Engagement.
- Recognition.
- Employee feedback.
- Communication consistency.
- Frontline inclusion.

### Best product

Workmates.

---

# 10. ATL and BTL Message Altitude

## 10.1 Above the Line

Targets:

- C-suite.
- VP.
- Strategic heads.
- Budget-owning directors.

### Message rules

- Two to three sentences.
- 45 to 70 words.
- Focus on risk, scale, growth, standardization, and strategic outcomes.
- One proof point maximum.
- No feature list.

### Fatal mistake

Turning a strategic buyer’s message into an administrative complaint.

## 10.2 Below the Line

Targets:

- Managers.
- Specialists.
- Coordinators.
- Hands-on directors.
- Recruiters.
- HR generalists.

### Message rules

- Three to four short sentences.
- 60 to 85 words.
- Focus on daily work, repeated follow-up, status visibility, and manual tasks.
- Use concrete workflow language.

### Fatal mistake

Talking only about ROI, transformation, or board-level outcomes.

---

# 11. Signal System

## 11.1 Signal Hierarchy

### Level 1: Relationship and first-party signals

- Former customer at a new company.
- Known champion move.
- Direct reply.
- Demo request.
- Trial request.
- Pricing question.
- Owned webinar attendance.
- Prior conversation.
- Closed-lost re-engagement.
- Active opportunity activity.

### Level 2: Strong public business signals

- New HR leader.
- Hiring surge.
- New locations.
- Acquisition.
- Merger.
- Geographic expansion.
- Seasonal hiring.
- Verified HR technology change.
- Verified ADP use.
- Public manual-process evidence.
- Negative competitor review.
- Relevant job postings.

### Level 3: Moderate company signals

- General company growth.
- General funding.
- Relevant content.
- Industry event.
- Multi-location structure.
- Frontline workforce.
- Large employee base.
- Relevant company description.

### Level 4: Core-static relevance

- Role.
- Industry.
- Employee count.
- Workforce model.
- Likely process pattern.

## 11.2 Signal Strength

### High

- Direct buying behavior.
- Direct relationship.
- Public event with clear workflow implication.
- Multiple corroborating signals.
- Current and specific evidence.

### Medium

- Relevant but inferred implication.
- One credible company event.
- Strong role and company fit.
- Industry-specific operational pattern.

### Low

- Generic growth.
- Old news.
- Broad industry fit.
- Weak or unverified technographic evidence.
- Role-only relevance.

## 11.3 Signal Freshness

Recommended timing:

- Demo request: immediately.
- Website or high-intent engagement: within 24 to 48 hours, without exposing tracking.
- Webinar attendance: within 48 to 72 hours.
- Job change: days 14 to 45.
- Hiring pattern: within one to two weeks.
- Funding: two to four weeks after announcement.
- Product launch: one to two weeks.
- Acquisition: after immediate announcement noise, usually 30 to 90 days depending on the workflow.
- Competitor renewal: approximately 90 days before renewal when verified.

These are operating defaults, not laws.

## 11.4 Signal Disclosure

### Safe to mention

- Public leadership announcement.
- Public job posting.
- Public company expansion.
- Public acquisition.
- Public article or post.
- Owned webinar attendance.
- Direct form submission.
- Direct prior conversation.
- Content downloaded by the person.

### Use only as background

- Pricing-page visit.
- Anonymous website visit.
- Ad click.
- Intent-provider signal.
- Profile view.
- Email opens.
- Tracking-pixel activity.
- Competitor research inferred from intent tools.

Never expose surveillance.

---

# 12. Personalization System

## 12.1 The Six Buckets

### Bucket 1: Self-authored content

- LinkedIn posts.
- Articles.
- Webinars.
- Interviews.
- Podcasts.
- Conference talks.

Best for Tier A.

### Bucket 2: Engaged content

- Comments.
- Shares.
- Event questions.
- Relevant participation.

### Bucket 3: Self-identified professional traits

- Headline.
- About section.
- Role description.
- Stated initiative.

### Bucket 4: Professional background

- New role.
- Promotion.
- Tenure.
- Previous company.
- Board role.
- Relevant certification.

### Bucket 5: Company-level evidence

- Hiring.
- Growth.
- Expansion.
- Job posts.
- Product launches.
- Locations.
- Technology.
- Company language.
- Industry structure.

Best scalable bucket.

### Bucket 6: Core-static relevance

- Persona.
- Industry.
- Size.
- Geography.
- Technographics.
- Workforce type.

Fallback only.

## 12.2 Strong Hook

Use when there is specific, high-confidence evidence.

Pattern:

> In your recent [content], you mentioned [specific point]. That usually creates [relevant implication] for [persona].

Do not fabricate quotes.

## 12.3 Lite Hook

Use for scalable campaigns.

Patterns:

- “With {{company}} hiring across several locations…”
- “For a largely frontline workforce…”
- “With recruiting and onboarding under the same team…”
- “For healthcare teams managing licensed employees…”
- “As {{company}} expands across sites…”

## 12.4 Hook Test

A hook is useful only when it changes the message.

Ask:

1. Does it alter the pain?
2. Does it alter the product?
3. Does it alter the CTA?
4. Does it explain why this person receives the email?

If not, it is decorative personalization.

---

# 13. The Pain Hypothesis

Use this equation:

> **Signal + role + company type + workflow pattern = pain hypothesis**

Example:

- Signal: 20 open caregiver roles.
- Role: Director of HR.
- Company type: Multi-location home health.
- Workflow pattern: High-volume onboarding plus licenses.
- Pain hypothesis: HR may be collecting new-hire documents and tracking readiness in separate processes.

The hypothesis must be written as:

- A question.
- A pattern.
- A conditional statement.

Never state it as confirmed unless the evidence proves it.

---

# 14. Offer Architecture

## 14.1 Offer Ladder

From lowest friction to highest:

1. Share a checklist.
2. Share a two-minute video.
3. Share a workflow map.
4. Share a short case study.
5. Compare processes.
6. Set up a test account.
7. Run a three-month pilot.
8. Schedule a 15-minute setup call.
9. Schedule a full demo.

Email 1 should usually use levels 1 to 5.

Email 2 can introduce levels 6 or 7.

Email 3 can present level 8 as one option.

## 14.2 Three-Month Pilot Language

Preferred:

- “three months of no-commitment access”
- “a three-month pilot at no cost”
- “a three-month test account”
- “a three-month pilot before making a longer commitment”

Avoid:

- “risk-free”
- “guaranteed”
- “limited-time deal”
- “free forever”
- “special offer”

When eligibility is not universal:

- “We may be able to set up…”
- “We are offering selected teams…”
- “For qualifying teams…”

---

# 15. Proof Strategy

## 15.1 Proof Hierarchy

1. Same industry, same use case, similar scale.
2. Same industry, same use case.
3. Same workforce model.
4. Same company size.
5. Same product.
6. General HR Cloud proof.
7. No proof.

Omitting proof is better than using irrelevant proof.

## 15.2 Proof Rules

Never:

- Invent a number.
- Inflate a number.
- Combine two customer stories.
- Imply guaranteed results.
- Call an unrelated customer similar.
- Name a customer when approval requires anonymization.
- State a product result that is not in the source material.

## 15.3 Proof Placement

Email 1:

- One proof point maximum.

Email 2:

- Best place for case study or customer outcome.

Email 3:

- Usually no new proof.

---

# 16. ADP Copywriting Rules

ADP is a partner, not an enemy.

## 16.1 Approved Positioning

- HR Cloud works alongside ADP.
- Existing payroll stays in place.
- HR Cloud extends workflows before and around payroll.
- HR Cloud can connect recruiting, onboarding, forms, tasks, and employee communication with ADP-supported processes.

## 16.2 Prohibited Positioning

Never write:

- “ADP onboarding is broken.”
- “Replace ADP.”
- “ADP is outdated.”
- “ADP cannot handle onboarding.”
- “Move off ADP.”

## 16.3 Verification Rule

Mention ADP only when:

- CSV confirms it.
- Public evidence confirms it.
- The campaign specifically targets verified ADP users.
- The user instructs it.
- It is an ADP-sourced opportunity.

Do not treat a job posting requesting ADP experience as definitive proof by itself.

---

# 17. Email Anatomy

## 17.1 Subject Line

Purpose: earn the open.

Rules:

- Two to four words.
- Lowercase.
- Internal-looking.
- Relevant to the workflow.
- No hype.
- No emoji.
- No exclamation point.
- No fake “re:”
- No full pitch.
- Avoid “free.”

Examples:

- `new hire handoff`
- `credential follow-up`
- `frontline onboarding`
- `candidate to day one`
- `forms after offer`
- `employee readiness`
- `across locations`
- `mobile new hires`

## 17.2 Opening Line

Purpose: explain why this is about them.

Use:

- Signal.
- Company context.
- Workflow question.
- Industry pattern.
- Role responsibility.

Never open with:

- “I hope you are well.”
- “I wanted to reach out.”
- “My name is…”
- “We are HR Cloud.”
- Generic praise.

## 17.3 Problem Line

Purpose: name the workflow consequence.

Good:

- “That usually creates duplicate employee entry after the offer.”
- “The hard part is often seeing what is still incomplete across locations.”
- “Managers end up answering the same new-hire questions repeatedly.”

## 17.4 Value Line

Purpose: explain the outcome and mechanism.

Good:

- “HR Cloud moves accepted candidates into onboarding without recreating the record.”
- “Maya guides new hires through approved tasks and questions by SMS or email.”
- “Workmates gives HR a way to reach frontline employees and confirm important updates were read.”

## 17.5 CTA

Purpose: make replying easy.

Use:

- “Worth a look?”
- “Should I send the two-minute version?”
- “Would the checklist be useful?”
- “Open to comparing workflows?”
- “Is that something your team is working through?”

Avoid:

- “Can we schedule 30 minutes?”
- “Book a demo here.”
- Multiple options in Email 1.
- Two questions in one CTA.

---

# 18. Copy Framework Library

## 18.1 Trigger, Implication, Value, CTA

Use when the signal is strong.

Template:

> [Public signal or context].  
> That often creates [specific workflow implication].  
> HR Cloud helps [persona] [outcome].  
> [Low-friction CTA]?

## 18.2 Question, Pattern, Proof, CTA

Use when the pain is inferred.

Template:

> How is your team handling [workflow]?  
> Many [industry] teams still deal with [pattern].  
> HR Cloud helps [outcome or proof].  
> [CTA]?

## 18.3 Challenge of Similar Companies

Use for vertical campaigns.

Template:

> [Industry] teams with [workforce characteristic] often struggle with [problem].  
> HR Cloud helps them [specific outcome].  
> [CTA]?

## 18.4 Before, After, Bridge

Use when the change is visual.

Template:

> Before: [fragmented workflow].  
> After: [connected workflow].  
> Bridge: [HR Cloud mechanism].  
> [CTA]?

## 18.5 Problem, Agitate, Solve

Use carefully. Do not dramatize.

Template:

> [Problem].  
> [Practical cost or consequence].  
> [HR Cloud outcome].  
> [CTA]?

## 18.6 Upfront Value

Use for Tier A.

Template:

> I mapped the likely handoff from [current stage] to [next stage]. The gap is usually [specific issue].  
> HR Cloud handles [relevant workflow].  
> Want the short version?

## 18.7 Leader Responsibility

Use for executives.

Template:

> As [role], how are you standardizing [workflow] across [locations or employee group]?  
> HR Cloud helps teams [strategic outcome].  
> Worth comparing approaches?

## 18.8 Do the Math

Use only with verified inputs.

Never invent hours, costs, turnover, or error rates.

## 18.9 No-Oriented CTA

Use in later touches.

Examples:

- “Would it be a bad idea to send the workflow?”
- “Should I close the loop?”
- “Not a priority this quarter?”

Use sparingly. Do not manipulate.

## 18.10 Passdown

Use for a senior contact who may not own the workflow.

Template:

> I am not sure whether [topic] sits with you or someone on the HR operations team.  
> HR Cloud helps [company type] [outcome].  
> Who owns [workflow] at {{company}}?

---

# 19. Default Three-Email Sequence

## Email 1: Relevance

### Objective

Earn interest.

### Structure

1. Hook.
2. Problem or question.
3. One outcome or proof.
4. One CTA.

### Word count

- ATL: 45 to 70.
- BTL: 60 to 85.
- Hard maximum: 90.

### Prohibited

- Calendar link.
- Attachment.
- Image.
- Feature list.
- Multiple CTAs.
- Long signature.
- More than one question mark.
- Meeting-first ask.

## Email 2: New Angle and Pilot

### Timing

Approximately three days later.

### Subject

Blank to remain in thread.

### Objective

Add new value and reduce risk.

### Structure

1. New angle.
2. Proof or implementation point.
3. Three-month pilot.
4. One CTA.

### Word count

50 to 75.

### Important

Email 2 must not paraphrase Email 1.

Possible new angles:

- Mobile completion.
- Manager reminders.
- Data handoff.
- Credential tracking.
- Employee questions.
- Existing payroll stays.
- Implementation.
- Location consistency.
- Training readiness.
- Employee communication.

## Email 3: Close the Loop

### Timing

Four to seven days after Email 2.

### Subject

Blank by default.

### Objective

Make the reply easy.

### Word count

35 to 60.

### Structure

> I do not want to keep guessing about timing. Which is closest?

> 1. Not a priority right now  
> 2. Open to 15 minutes to set up the pilot  
> 3. Not relevant

### Rules

- No guilt.
- No urgency.
- No new feature dump.
- No passive aggression.
- Honor the close after sending.

---

# 20. Optional Four-Email Sequence

Use only when the user requests a longer cadence.

## Email 1

Trigger and relevance.

## Email 2

Proof.

## Email 3

New pain or persona angle.

## Email 4

Breakup.

Suggested spacing:

- Day 0.
- Day 3.
- Day 7.
- Day 14.

Never use “just bumping this.”

---

# 21. Industry Copy Playbooks

## 21.1 Healthcare, Home Health, Senior Care, Hospice

### Signals

- Caregiver hiring.
- Nurse hiring.
- New office.
- Multi-state expansion.
- Credentialing roles.
- Compliance hiring.
- Seasonal demand.
- High turnover.
- Public audit or readiness language.

### Pains

- License tracking.
- Missing credentials.
- Mobile onboarding.
- Repetitive manager follow-up.
- Audit preparation.
- Separate onboarding and readiness systems.

### Products

Onboard, Maya, Credential Tracking, Train, Shift Planner.

### Good opener

> For teams onboarding licensed employees across several locations, documents and expiration dates often end up in separate tracking processes.

### Avoid

- Patient-care claims without evidence.
- HIPAA certification claims.
- PHI claims.
- Fear-based compliance language.

## 21.2 Manufacturing

### Signals

- New plant.
- Expansion.
- Shift hiring.
- Safety hiring.
- Multi-location operations.
- Seasonal production increase.

### Pains

- Paper forms.
- Kiosk or mobile needs.
- Safety training.
- Plant-level inconsistency.
- Manager follow-up.
- Asset handoff.

### Products

Onboard, Maya, Workmates, Train, Time Clock, Assets.

### Good opener

> With plant employees rarely sitting at a desk, how are new hires completing forms, training, and required documents today?

## 21.3 Construction and Field Services

### Signals

- Project wins.
- New job sites.
- Field hiring.
- Safety roles.
- License requirements.
- Seasonal hiring.

### Pains

- Mobile document collection.
- Rehires.
- Site-specific onboarding.
- Certifications.
- Equipment handoff.
- Time and shift workflows.

### Products

Onboard, Maya, Credential Tracking, Train, Time Clock, Assets.

## 21.4 Education

### Signals

- Summer hiring.
- Campus expansion.
- New school year.
- Teacher recruiting.
- Substitute hiring.
- Multi-campus growth.

### Pains

- Seasonal hiring spikes.
- Background and certification documents.
- Campus consistency.
- Recruiting-to-onboarding handoff.
- Employee communication.

### Products

Recruit, Onboard, Maya, People, Workmates.

## 21.5 Retail, Hospitality, Restaurants

### Signals

- New locations.
- Seasonal hiring.
- High-volume job posts.
- Franchise growth.
- Frontline expansion.

### Pains

- High turnover.
- Inconsistent manager onboarding.
- No corporate email.
- Missed announcements.
- Recognition.
- Mobile forms.

### Products

Onboard, Maya, Workmates, Recruit, Train, Time Clock.

## 21.6 Staffing

### Signals

- Recruiter hiring.
- New client contracts.
- Geographic expansion.
- High placement volume.

### Pains

- Candidate-to-worker handoff.
- Document collection.
- Credentials.
- Rehires.
- Readiness.
- Communication.

### Products

Recruit, Onboard, Maya, Credential Tracking, Train.

## 21.7 Logistics and Field Operations

### Signals

- Driver hiring.
- Terminal expansion.
- Regional growth.
- Shift hiring.

### Pains

- Mobile onboarding.
- Credentials.
- Safety training.
- Shift readiness.
- Frontline communication.

### Products

Onboard, Maya, Workmates, Train, Time Clock, Shift Planner.

## 21.8 Professional Services

### Signals

- Hiring growth.
- M&A.
- New offices.
- Recruiting-team expansion.

### Pains

- Candidate handoff.
- Employee records.
- Documents.
- Time-off visibility.
- Performance workflows.

### Products

Recruit, Onboard, People, Time Off, Perform, Workmates.

---

# 22. Style Guide

## 22.1 Tone

- Direct.
- Human.
- Calm.
- Specific.
- Helpful.
- Confident.
- Low-pressure.

## 22.2 Reading Level

Approximately fifth grade.

Use short sentences and simple words.

## 22.3 Paragraphs

- Two to three lines.
- One blank line between paragraphs.
- No dense blocks.

## 22.4 Prohibited Language

- “I hope this email finds you well.”
- “I wanted to reach out.”
- “In today’s fast-paced world.”
- “Revolutionary.”
- “Cutting-edge.”
- “Game-changing.”
- “Synergy.”
- “Unlock.”
- “Seamless.”
- “Best-in-class.”
- “Special offer.”
- “Risk-free.”
- “Guaranteed.”
- “Act now.”
- “Limited time.”

## 22.5 Punctuation

Do not use em dashes or en dashes.

Use periods, commas, colons, and parentheses.

## 22.6 Pronoun Balance

The recipient’s world must dominate.

“You,” “your,” company context, and workflow references should outweigh “we,” “our,” and “HR Cloud.”

---

# 23. Deliverability Rules

Email 1 should be:

- Plain text.
- No image.
- No attachment.
- No HTML.
- No tracking language.
- No calendar link.
- Zero links preferred.
- One link maximum when required.
- Short signature or no signature.

Avoid:

- ALL CAPS.
- Multiple exclamation points.
- Spam-trigger words.
- Designed newsletter formatting.
- Repeated byte-identical copy across a large list.

Variation should be meaningful, not random.

---

# 24. Variation System

## 24.1 Vary These Elements

- Subject.
- Opening structure.
- Pain angle.
- Proof.
- CTA.
- Product mechanism.
- Industry context.
- Sentence rhythm.

## 24.2 Do Not Vary These Arbitrarily

- Core claim.
- Product capability.
- Customer result.
- Integration.
- Trial eligibility.
- Partner designation.
- Compliance language.

## 24.3 Repetition Limits

Recommended:

- Same subject: no more than 15% of list.
- Same first sentence: no more than 10%.
- Same CTA: no more than 25%.
- Same proof point: acceptable within a narrow industry segment, but rotate when alternatives exist.

## 24.4 Same-Company Multi-Threading

When two leads are at the same company:

- Executive: strategy and scale.
- Manager: workflow.
- Recruiter: candidate handoff.
- HRIS: data and control.
- Operations: readiness and execution.

Never send identical messages to multiple people at the same account.

---

# 25. QA Scoring Model

Score each eligible sequence out of 100.

## 25.1 Account Fit: 20 points

- Industry fit: 5.
- Employee/workforce fit: 5.
- Geography fit: 3.
- Workflow complexity: 4.
- Product relevance: 3.

## 25.2 Persona Fit: 15 points

- Correct department: 5.
- Correct seniority: 4.
- Owns or influences problem: 6.

## 25.3 Signal Quality: 15 points

- Current: 4.
- Specific: 4.
- Verifiable: 4.
- Safe to use: 3.

## 25.4 Pain Logic: 15 points

- Pain follows evidence: 6.
- Pain matches persona: 5.
- Pain is phrased honestly: 4.

## 25.5 Product and Offer Fit: 15 points

- Correct product: 5.
- Clear outcome: 4.
- Relevant offer: 3.
- CTA friction is appropriate: 3.

## 25.6 Proof: 10 points

- Verified: 4.
- Relevant industry/use case: 3.
- Correctly worded: 3.

## 25.7 Copy Quality: 10 points

- Clear: 2.
- Short: 2.
- Human: 2.
- Specific: 2.
- One CTA: 2.

## 25.8 Compliance and Deliverability: 10 points

- No unsupported claims: 3.
- No invasive wording: 2.
- No prohibited language: 2.
- ADP and compliance rules followed: 2.
- Formatting safe: 1.

## 25.9 Thresholds

- 90 to 100: High confidence.
- 75 to 89: Medium confidence.
- 60 to 74: Low confidence, manual review.
- Below 60: Do not send or rewrite.

---

# 26. QA Checklist

## Data

- Row preserved.
- Original columns preserved.
- Email unchanged.
- Company normalized.
- Signal source captured.
- Signal date captured.
- No invented data.

## Relevance

- Correct persona.
- Correct altitude.
- Correct industry.
- Correct product.
- Pain follows evidence.
- Offer follows pain.
- Copy could not go unchanged to an unrelated account.

## Copy

- Email 1 under 90 words.
- Email 2 shorter.
- Email 3 concise.
- One CTA.
- One question mark maximum.
- No em dash.
- No fake praise.
- No generic opener.
- No feature list.
- No hard meeting ask in Email 1.
- No calendar link in Email 1.
- No signature unless requested.
- No emoji.
- No markdown.
- No HTML.
- No bullets in Emails 1 and 2.

## Signal

- Tracking signal not exposed.
- Public signal used naturally.
- Old signal not framed as recent.
- Weak evidence not presented as fact.
- One job post not called a hiring surge.
- Funding not treated as automatic buying intent.

## HR Cloud

- ADP treated as partner.
- No payroll replacement.
- No unsupported integration.
- No unsupported AI claim.
- No HIPAA certification claim.
- No PHI implication.
- No competitor attack.
- One relevant product.

---

# 27. Standard QA Flags

Use semicolon-separated flags.

- `missing_first_name`
- `missing_company`
- `missing_email`
- `invalid_email`
- `wrong_persona`
- `out_of_icp`
- `employee_count_too_low`
- `employee_count_unknown`
- `industry_unknown`
- `company_domain_missing`
- `company_research_unavailable`
- `weak_signal`
- `stale_signal`
- `signal_not_safe_to_mention`
- `no_verified_proof`
- `possible_current_customer`
- `competitor`
- `vendor`
- `consultant`
- `student_or_unemployed`
- `do_not_contact`
- `unsubscribed`
- `manual_review_required`
- `executive_review_required`
- `adp_status_unverified`
- `technology_unverified`
- `low_personalization_confidence`
- `same_company_multithread`
- `unsupported_claim_removed`

---

# 28. Testing and Optimization

## 28.1 Test One Variable at a Time

Do not change subject, opener, offer, proof, and CTA simultaneously.

Recommended test order:

1. Segment.
2. Signal.
3. Offer.
4. Opening line.
5. Proof.
6. CTA.
7. Subject.

## 28.2 Metrics

Track:

- Delivery rate.
- Bounce rate.
- Positive reply rate.
- Neutral reply rate.
- Negative reply rate.
- Meeting rate.
- Pilot acceptance.
- Qualified opportunity rate.
- Unsubscribe rate.
- Spam complaints.
- Reply by signal type.
- Reply by persona.
- Reply by industry.
- Reply by product.
- Reply by proof point.

Do not rely heavily on open rate because privacy protections distort it.

## 28.3 Diagnosis

### Low delivery

Fix:

- List verification.
- Sender reputation.
- Domain setup.
- Volume.
- Spam language.

### Delivered but low replies

Fix:

1. ICP.
2. Signal.
3. Offer.
4. Relevance.
5. CTA.
6. Copy length.

### Replies but no meetings

Fix:

- Offer mismatch.
- Weak next step.
- Poor qualification.
- Slow response.
- Generic reply handling.

### High negative replies

Fix:

- Wrong ICP.
- Aggressive wording.
- Too many touches.
- Weak signal.
- Poor account exclusions.

---

# 29. Failure Modes

Reject or rewrite output that shows:

- Fake personalization.
- Generic company descriptions.
- Product dumping.
- Strategy language for a manager.
- Task-level language for a CHRO.
- Meeting-first CTA.
- “Just checking in.”
- Mentioning tracked behavior.
- Attacking ADP.
- Unsupported proof.
- Identical copy across same-company contacts.
- Old news written as recent.
- Company fit based only on size.
- A pilot offered as universally available when it is not.
- AI claims that imply autonomous decisions.
- Healthcare claims involving HIPAA certification or PHI.
- A completed sample instead of a completed CSV.
- Lost rows.
- Broken multiline cells.
- Changed original values.

---

# 30. Output Summary Standard

After producing the CSV, report:

- Input rows.
- Output rows.
- Eligible leads.
- Do-not-send leads.
- High-confidence sequences.
- Medium-confidence sequences.
- Low-confidence sequences.
- Manual-review leads.
- Top industries.
- Top personas.
- Top signals.
- Top products.
- Most common QA flags.
- Number of same-company multi-thread accounts.
- Number of ADP-verified accounts.
- Number of rows with no verified proof.

The input and output row counts must match.

---

# 31. Runtime Execution Prompt

Use this short prompt together with the two playbooks and the Apollo CSV.

## Prompt

You are processing an Apollo CSV for HR Cloud.

Read the HR Cloud GTM playbook and the HR Cloud Signal-Led Personalized Outbound Copywriting Playbook before writing.

Process every row in the CSV. Preserve every original row, column, value, and row order. Add all required `hrc_` research, strategy, copy, confidence, and QA columns defined in the copywriting playbook.

For each lead:

1. Apply contactability, ICP, persona, signal, product, and approval gates.
2. Select one primary HR Cloud workflow.
3. Use the strongest verified signal available.
4. Never invent a company fact, pain, system, vendor, technology, result, or quote.
5. Use a question or hypothesis when evidence is incomplete.
6. Match copy altitude to seniority.
7. Write a three-email sequence.
8. Keep Email 1 under 90 words.
9. Keep Email 2 shorter than Email 1 and introduce the three-month pilot.
10. Make Email 3 a concise close-the-loop message with three reply options.
11. Keep Email 2 and Email 3 subject cells blank so they remain in the same thread.
12. Use plain text, proper line breaks, one CTA, and no signatures.
13. Do not expose website visits, ad clicks, profile views, intent data, or email tracking.
14. Treat ADP as a partner and never position HR Cloud as a payroll replacement.
15. Flag weak, out-of-ICP, invalid, suppressed, or uncertain leads rather than forcing copy.
16. Run the 100-point QA score before finalizing each sequence.
17. Rewrite any sequence below 60 or mark it do-not-send.
18. Save the result as `HR_Cloud_Apollo_Personalized_Email_Sequences.csv`.

Do not stop after a sample. Complete the entire file.

Before claiming completion, verify:

- Input and output row counts match.
- All original columns are preserved.
- Required `hrc_` columns exist.
- Multiline email cells are valid CSV.
- The output file opens correctly.
- No original rows were removed.

Return the completed CSV and the standard output summary.

---

# 32. Final Standard

The goal is not to make every email look heavily researched.

The goal is to produce a credible, relevant, honest reason for the right HR Cloud message to reach the right person at the right company.

A useful email should make the recipient think:

> This person understands the workflow I own.

Not:

> This system scraped my profile.

Not:

> This is the same template everyone received.

Not:

> This vendor is trying to sell every feature at once.

Truth, relevance, and restraint win.
