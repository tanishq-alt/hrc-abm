# HR Cloud GTM Intelligence — Operating Model

## The Core Premise

These are not generic search prompts. Each one is an operating specification for an autonomous scraping and research agent. They define what to look for, where to look, how to score, and what to do with the results.

This toolkit exists because the best HR Cloud prospects don't raise their hand. They don't fill out forms. They show up in job postings, PDF documents, government databases, and procurement records — if you know where to look.

## Recommended Operating Model

### Run One Prompt at a Time
Each prompt is a focused intelligence operation. Running multiple simultaneously dilutes signal quality. Start with Prompt 1 (manual onboarding) to build your baseline, then use Prompt 4 (high-intent signals) for broad discovery before narrowing with vertical-specific prompts.

### Use Prompt 4 for Broad Discovery
Prompt 4 covers 18 signal families and is the best starting point when you don't know which vertical to target. Its signal families map to all of HR Cloud's ideal customer profiles.

### Vertical Depth: Prompts 6 and 7
Prompts 6 (healthcare) and 7 (education) go deepest in their verticals. Use them when you have a territory focused on those segments.

### Lookalike Expansion: Prompt 2
After identifying high-scoring leads from any prompt, feed them as seeds into Prompt 2 to find structurally similar companies you haven't found yet.

## Suggested Workflow

```
Discover → Resolve → Verify → Score → Reject Aggressively → Enrich → Write Outreach
```

1. **Discover**: Run the prompt scraper. Collect raw candidates.
2. **Resolve**: Verify every domain. Strip CDNs, job boards, and non-company URLs.
3. **Verify**: At least one Tier A or Tier B signal must exist. No guessing.
4. **Score**: Apply the prompt's scoring model. Be honest about gaps.
5. **Reject Aggressively**: If a lead doesn't hit the threshold, drop it. Quality over volume.
6. **Enrich**: Add employee count, LinkedIn company URL, HQ city, ADP status if unknown.
7. **Write Outreach**: Use only evidence you verified. No assumed pain.

## HR Cloud Positioning

### Strongest Fit (score aggressively)
- Frontline, hourly, or deskless workforce (healthcare, senior care, education, manufacturing, logistics)
- Distributed or multi-location operations
- Regulated industry with credentialing or documentation requirements
- High-volume or seasonal hiring
- Currently using ADP but lacking modern onboarding

### Moderate Fit (verify before pursuing)
- Single-location professional services
- SMB with < 50 employees
- Companies with BambooHR/Gusto already deployed (harder displacement)

### Poor Fit (reject)
- Tech companies with Workday or SuccessFactors already deployed
- Companies under 25 employees
- Companies outside US/Canada without strong evidence of HR Cloud expansion plans

## Onboard vs. Workmates Product Mapping

| Signal | Product | Rationale |
|--------|---------|-----------|
| Paper new hire packets | Onboard | Replace manual onboarding with digital workflow |
| ADP user + paper onboarding | Onboard | Complement ADP payroll with modern onboarding |
| Multi-location + frontline communication gap | Workmates | Bridge the last-mile communication problem |
| ADP user + multi-location frontline | Onboard + Workmates | Maximum cross-sell opportunity |
| No HRIS at all | Onboard | Greenfield — all-in-one entry point |

## ADP Complementary Positioning

HR Cloud does not compete with ADP for payroll. The positioning is:

> "ADP handles your payroll. HR Cloud handles the experience your employees have from the moment they're hired to the moment they feel like part of the team."

Never lead with "replace ADP." Always lead with what ADP doesn't do: digital onboarding, document management, I-9 e-verification workflow, frontline communication, employee engagement.

## Evidence Tier Definitions

| Tier | Description | Minimum Acceptable |
|------|-------------|-------------------|
| A | Company-hosted evidence (PDF, careers page, internal doc) | Confirms current state |
| B | Job posting on company domain or applicant tracking page | Reveals current workflow |
| C | DDG snippet, news article, press release | Must be corroborated |
| D | Inference from industry, size, or geography alone | Never sufficient alone |

## Rejection Rules

Reject any lead where:
- The only evidence is a job board listing (Indeed, LinkedIn, Glassdoor)
- The company explicitly names a competing onboarding platform already in use
- Employee count is confirmed below 50
- The domain resolves to a CDN, holding company, or generic host
- The signal is > 180 days old with no corroborating recent signal
