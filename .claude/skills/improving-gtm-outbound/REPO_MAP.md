# Repository Map

## Naming Disambiguation

There are TWO `skills/` locations in this repo. They serve different purposes.

| Path | Type | Purpose |
|---|---|---|
| `skills/` (root) | GTM operating playbooks | Human-readable SKILL.md files describing how to use each scraper/engine module; NOT Claude Code skills |
| `.claude/skills/` | Claude Code skills | Invocable from Claude Code CLI; this learning system lives here |

---

## Pipeline Files

```
pipeline/run.py
  Entry point. Accepts --vertical, --state, --min-score, --lookalike.
  Produces: data/abm_accounts_{vertical}_{timestamp}.csv

pipeline/enrich.py
  Post-processor. Deduplicates domains, re-scores with multi-signal context.
  Reads:  data/abm_accounts_*.csv
  Writes: data/enriched_{label}_{timestamp}.csv
```

## Engine Files (scoring and analysis)

```
engine/icp.py
  ICP_PROFILES:           dict of vertical → ideal_employee_ranges, high_fit_signals, etc.
  EMPLOYEE_RANGE_SCORES:  bucket → points (hard floor at 100 employees)
  compute_icp_score():    returns ICPScore(firmographic, technographic, behavioral, buying_trigger)

engine/scorer.py
  QualificationResult.qualify():  4-dim scorer (ICP 0-35, intent 0-25, confidence 0-20, contact 0-20)
  Tier floors:
    Tier 1 = total ≥ 80 AND icp ≥ 26 AND intent ≥ 17 AND confidence ≥ 14 AND contact ≥ 12
    Tier 2 = total ≥ 65 AND icp ≥ 23 AND intent ≥ 11 AND confidence ≥ 11
    Tier 3 = total ≥ 45
  CompositeScore.compute():  legacy backward-compat wrapper

engine/signals.py
  SIGNAL_BASE_SCORES:  signal_type → max raw points
  Signal dataclass:    with freshness decay and tier weighting
  SignalAggregator:    deduplicates, computes aggregate signal_score (0-100)

engine/interpreter.py
  interpret_signal():  pure function, no side effects
  Returns: relevance_verdict, signal_strength, confidence, freshness_status,
           why_now, safe_to_mention, hris_fit_category

engine/evidence.py
  Evidence dataclass:   evidence_id, tier, claim_type, exact_excerpt, content_hash
  EvidenceLedger:       deduplication by excerpt-only content_hash

engine/committee.py
  COMMITTEE_TEMPLATES:  vertical → list[PersonaTarget]
  Verticals: healthcare, education, manufacturing, nonprofit, government, utilities
  map_buying_committee(vertical, company_name): returns ordered list

engine/personalizer.py
  PERSONA_TONE:       role → angle/voice/cta_style
  TITLE_TO_ROLE:      normalized title string → persona role
  infer_persona_role(): title → champion/economic_buyer/influencer/blocker
  build_first_line():   signal_type + persona_role → first sentence
  CTA_OPTIONS:        role + tier → recommended CTA
  SOCIAL_PROOF:       vertical + role → social proof sentence
  generate_outreach(): returns OutreachPackage(subject_a, subject_b, email_1-3, linkedin_note, cta)

engine/auditor.py
  audit_account(account_dict, evidence_list): returns AuditResult
  audit_accounts(accounts, evidence_map):     batch audit
  AuditResult: audit_status, audit_score, fatal_errors, warnings
```

## ABM Files

```
abm/account.py
  Account dataclass:    60+ fields covering identity, firmographics, signals,
                        scores, tier, outreach, hard gates, penalties, audit
  ACCOUNT_CSV_FIELDS:   ordered list of CSV export columns

abm/apollo_export.py
  account_to_apollo_row():  Account → Apollo-compatible dict
  APOLLO_FIELDS:            38 Apollo CSV columns
  export_to_apollo():       writes data/apollo_{label}_{ts}.csv
  export_sequences():       writes data/sequences_{label}_{ts}.csv

abm/tiers.py
  TIER_ACTIONS:   tier → outreach_type, sequence_length, urgency
  classify():     composite_score → TierDecision
```

## Scraper Files

```
scrapers/p01_manual_onboarding/  batch1.py, batch2.py, batch3.py
scrapers/p02_lookalike/          lookalike.py  (run_lookalike(seed_inputs, min_score))
scrapers/p03_adp_confirmed/      adp_finder.py
scrapers/p04_high_intent/        intent_signals.py
scrapers/p05_workmates/          workmates_finder.py
scrapers/p06_healthcare/         healthcare_finder.py
scrapers/p07_education/          education_finder.py
scrapers/shared/
  ddg.py       DDG search wrapper
  fetcher.py   HTTP page fetcher
  schema.py    CANONICAL_FIELDS (25 cols), LeadRecord, make_row()
  verifier.py  resolve_domain() → DomainResolution; verify_domain() (legacy)
```

## Data Files

```
data/
  nano_onboarding_MASTER.csv          Committed reference dataset (~100 accounts)
  abm_accounts_{vertical}_{ts}.csv   Pipeline output (not committed)
  enriched_{label}_{ts}.csv          Enriched output (not committed)
  lookalike_leads.csv                 Lookalike output (not committed)
  learning/
    outcomes/     Append-only raw outcome CSVs (one per campaign batch)
    analysis/     Segmented analysis snapshots (JSON)
    proposals/    Versioned YAML proposals awaiting human review
    canary/       Canary run result CSVs
    audit/        Immutable append-only audit trail (JSONL)
```

## Tests

```
tests/ (12 files, 118 passing as of 2026-07-31)
  test_evidence.py                    EvidenceLedger deduplication
  test_signal_interpreter.py          interpret_signal() purity
  test_scoring_floors.py              Tier floor enforcement
  test_hard_gates.py                  Hard gate override behavior
  test_modern_hris_rule.py            HRIS classification (not blanket penalty)
  test_domain_entity_resolver.py      DomainResolution structured object
  test_parent_facility_dedupe.py      Deduplication via dedupe_key
  test_signal_freshness.py            Freshness status classification
  test_negative_evidence.py           find_negative_evidence() in pipeline/run.py
  test_committee_after_qualification.py  contactability_score defaults to 0
  test_auditor.py                     AuditResult behavior
  test_apollo_export.py               Apollo export format and fields

  Learning system tests (new):
  test_outcome_ingestion.py           Schema validation and join integrity
  test_performance_analysis.py        Segment math and metric computation
  test_hypothesis_generation.py       Proposal YAML format validation
  test_proposal_evaluation.py         Backtest logic against fixture data
  test_promotion_safety.py            Gate enforcement — never auto-applies
```
