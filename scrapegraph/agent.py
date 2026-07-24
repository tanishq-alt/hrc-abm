"""
ScrapeGraph Agent Wrapper — HR Cloud GTM Intelligence Toolkit
Wraps all 7 HR Intel prompt modules as a ScrapeGraph-compatible agent.

Usage (CLI):
  python agent.py --module p01_manual_onboarding
  python agent.py --module p02_lookalike
  python agent.py --module p03_adp_confirmed
  python agent.py --module p04_high_intent
  python agent.py --module p05_workmates
  python agent.py --module p06_healthcare
  python agent.py --module p07_education
  python agent.py --module all

Legacy module names also work:
  python agent.py --module manual_onboarding
  python agent.py --module adp_confirmed
  python agent.py --module high_intent

Usage (ScrapeGraph Cloud):
  Upload this file as your agent entrypoint. Set OPENAI_API_KEY in env vars.
  The agent reads the prompt from scrapegraph/prompts/<module>.txt and runs
  the corresponding scraper, returning structured JSON leads.

Environment variables:
  OPENAI_API_KEY     — required for ScrapeGraph LLM extraction
  MODULE             — override --module flag (for cloud deployments)
  MAX_RESULTS        — cap total leads per run (default: 100)
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path

BASE = Path(__file__).parent.parent

MODULE_MAP = {
    # New structured module paths
    "p01_manual_onboarding": BASE / "scrapers/p01_manual_onboarding/batch3.py",
    "p02_lookalike":         BASE / "scrapers/p02_lookalike/lookalike.py",
    "p03_adp_confirmed":     BASE / "scrapers/p03_adp_confirmed/adp_finder.py",
    "p04_high_intent":       BASE / "scrapers/p04_high_intent/intent_signals.py",
    "p05_workmates":         BASE / "scrapers/p05_workmates/workmates_finder.py",
    "p06_healthcare":        BASE / "scrapers/p06_healthcare/healthcare_finder.py",
    "p07_education":         BASE / "scrapers/p07_education/education_finder.py",
    # Legacy aliases
    "manual_onboarding":     BASE / "scrapers/p01_manual_onboarding/batch3.py",
    "adp_confirmed":         BASE / "scrapers/p03_adp_confirmed/adp_finder.py",
    "rfp_rfq":               BASE / "scrapers/rfp_rfq/rfp_finder.py",
    "high_intent":           BASE / "scrapers/p04_high_intent/intent_signals.py",
}

OUTPUT_MAP = {
    "p01_manual_onboarding": BASE / "data/nano_batch3_leads.csv",
    "p02_lookalike":         BASE / "data/lookalike_leads.csv",
    "p03_adp_confirmed":     BASE / "data/adp_confirmed_leads.csv",
    "p04_high_intent":       BASE / "data/high_intent_leads.csv",
    "p05_workmates":         BASE / "data/workmates_leads.csv",
    "p06_healthcare":        BASE / "data/healthcare_leads.csv",
    "p07_education":         BASE / "data/education_leads.csv",
    # Legacy aliases
    "manual_onboarding":     BASE / "data/nano_batch3_leads.csv",
    "adp_confirmed":         BASE / "data/adp_confirmed_leads.csv",
    "rfp_rfq":               BASE / "data/rfp_rfq_leads.csv",
    "high_intent":           BASE / "data/high_intent_leads.csv",
}

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(module: str) -> str:
    prompt_file = PROMPTS_DIR / f"{module}.txt"
    if prompt_file.exists():
        return prompt_file.read_text()
    return f"Find companies with manual HR onboarding processes that need {module} intelligence."


def run_module(module: str) -> dict:
    """Run a scraper module and return results as dict."""
    script = MODULE_MAP.get(module)
    if not script or not script.exists():
        return {"error": f"Module not found: {module}"}

    print(f"[ScrapeGraph Agent] Running module: {module}", flush=True)
    print(f"[ScrapeGraph Agent] Script: {script}", flush=True)

    result = subprocess.run(
        [sys.executable, "-u", str(script)],
        capture_output=False,
        text=True,
    )

    output_csv = OUTPUT_MAP.get(module)
    if output_csv and output_csv.exists():
        import csv
        with open(output_csv, newline="", encoding="utf-8") as f:
            leads = list(csv.DictReader(f))
        return {
            "module": module,
            "lead_count": len(leads),
            "output_file": str(output_csv),
            "leads": leads,
        }
    return {"module": module, "error": "No output file found", "returncode": result.returncode}


def run_with_scrapegraph(module: str) -> dict:
    """
    ScrapeGraph-enhanced extraction.
    Uses LLM to extract structured data from pages that DDG alone might miss.
    Requires: pip install scrapegraphai
    """
    try:
        from scrapegraphai.graphs import SmartScraperGraph

        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            print("[ScrapeGraph] No OPENAI_API_KEY — falling back to plain scraper", flush=True)
            return run_module(module)

        graph_config = {
            "llm": {
                "api_key": openai_key,
                "model": "openai/gpt-4o-mini",
            },
            "verbose": False,
            "headless": True,
        }

        prompt = load_prompt(module)
        # Example URL targets per module
        target_urls = {
            "manual_onboarding": [
                "https://duckduckgo.com/?q=%22new+hire+packet%22+filetype%3Apdf&ia=web",
            ],
            "adp_confirmed": [
                "https://duckduckgo.com/?q=%22ADP+Workforce+Now%22+%22HR+coordinator%22+job&ia=web",
            ],
            "rfp_rfq": [
                "https://sam.gov/search/?index=opp&q=HRIS&dateRange=custom&start=2025-01-01",
            ],
            "high_intent": [
                "https://duckduckgo.com/?q=%22evaluating+HRIS%22+OR+%22looking+for+HR+software%22&ia=web",
            ],
        }

        urls = target_urls.get(module, [])
        all_results = []
        for url in urls:
            graph = SmartScraperGraph(
                prompt=prompt,
                source=url,
                config=graph_config,
            )
            result = graph.run()
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, dict):
                all_results.append(result)

        return {
            "module": module,
            "mode": "scrapegraph",
            "lead_count": len(all_results),
            "leads": all_results,
        }

    except ImportError:
        print("[ScrapeGraph] scrapegraphai not installed — falling back to plain scraper", flush=True)
        return run_module(module)


def main():
    parser = argparse.ArgumentParser(description="HR Intel ScrapeGraph Agent")
    # Deduplicate choices (aliases share same paths)
    primary_modules = [
        "p01_manual_onboarding", "p02_lookalike", "p03_adp_confirmed",
        "p04_high_intent", "p05_workmates", "p06_healthcare", "p07_education",
        "manual_onboarding", "adp_confirmed", "high_intent", "rfp_rfq",
    ]
    parser.add_argument(
        "--module",
        choices=primary_modules + ["all"],
        default=os.environ.get("MODULE", "p01_manual_onboarding"),
        help="Which intel module to run",
    )
    parser.add_argument(
        "--scrapegraph",
        action="store_true",
        default=False,
        help="Use ScrapeGraph LLM extraction (requires OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--output",
        choices=["json", "csv", "both"],
        default="both",
        help="Output format",
    )
    args = parser.parse_args()

    modules_to_run = list(MODULE_MAP.keys()) if args.module == "all" else [args.module]

    all_results = {}
    for module in modules_to_run:
        if args.scrapegraph:
            result = run_with_scrapegraph(module)
        else:
            result = run_module(module)
        all_results[module] = result

    if args.output in ("json", "both"):
        out_path = BASE / "data" / "agent_results.json"
        with open(out_path, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\n[ScrapeGraph Agent] JSON → {out_path}", flush=True)

    # Summary
    print("\n" + "=" * 60, flush=True)
    print("AGENT SUMMARY", flush=True)
    print("=" * 60, flush=True)
    for module, result in all_results.items():
        count = result.get("lead_count", 0)
        err = result.get("error", "")
        print(f"  {module}: {count} leads {('ERROR: ' + err) if err else ''}", flush=True)


if __name__ == "__main__":
    main()
