# Instruction Guide: Prompt 4 — High-Intent Signals

## What This Module Does

Prompt 4 is the broadest discovery module in the toolkit. It searches for companies showing behavioral buying signals across 18 signal families — before those companies ever announce an RFP or evaluation. This is the "early warning" layer of the GTM intelligence system.

## When to Use Prompt 4

- When starting a new territory without a clear vertical focus
- When Prompt 1 (manual onboarding) results are thin for a given industry
- When you want to find leads competitors have not yet identified
- When a sales territory has specific regulatory or event-driven triggers (OSHA, CMS, PE activity)

## How to Run

```bash
cd /Users/tanishqmac/hr-intel-toolkit
python3 -u scrapers/p04_high_intent/intent_signals.py 2>&1 | tee /tmp/p04_intent.log
```

Output: `data/high_intent_leads.csv`

## Signal Family Priority

Run Prompt 4 signals in this priority order for best ROI:

1. **Signal 8 (HR Leadership Hire)** — New HR leaders evaluate vendors within 90 days. Highest urgency.
2. **Signal 9 (Procurement Window)** — Active RFP means someone has budget. Close fastest.
3. **Signal 2 (Post-Acquisition)** — PE acquisition creates mandate to standardize. Predictable.
4. **Signal 1 (Manual Process Leakage)** — Same as Prompt 1 but broader industry scope.
5. **Signal 13 (Seasonal Calendar)** — Time-box these: reach school districts in June-July, retail in September-October.

## Source Enrichment Recommended

After Prompt 4 identifies leads, enrich with:
- OSHA establishment search (for Signal 5 — regulatory pressure)
- SAM.gov (for Signal 3 — government contracts)
- USAspending.gov (for Signal 3 — grants)
- LinkedIn (for Signal 8 — confirm new hire announcement)

## Outreach Notes

Signal 4 leads require the most personalized outreach because the signals are diverse. Always state:
1. What specific signal you found
2. Why that signal means they need HR Cloud now
3. What specific feature addresses their current situation
