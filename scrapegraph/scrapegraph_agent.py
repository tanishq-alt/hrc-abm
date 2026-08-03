"""
ScrapeGraph Agent Wrapper
Wraps all HR Intel modules as a ScrapeGraph-compatible agent.

Usage (CLI):
  python scrapegraph_agent.py --module manual_onboarding
  python scrapegraph_agent.py --module adp_confirmed
  python scrapegraph_agent.py --module rfp_rfq
  python scrapegraph_agent.py --module high_intent
  python scrapegraph_agent.py --module agent_reach        # Agent-Reach: Reddit/GitHub/web/RSS
  python scrapegraph_agent.py --module agent_reach_web    # web-only (Jina Reader, no auth)
  python scrapegraph_agent.py --module all

Usage (ScrapeGraph Cloud):
  Upload this file as your agent entrypoint. Set OPENAI_API_KEY in env vars.
  The agent reads the prompt from scrapegraph/prompts/<module>.txt and runs
  the corresponding scraper, returning structured JSON leads.

Environment variables:
  OPENAI_API_KEY     — required for ScrapeGraph LLM extraction
  MODULE             — override --module flag (for cloud deployments)
  MAX_RESULTS        — cap total leads per run (default: 100)

Agent-Reach channels available (zero-config):
  web       — any URL via Jina Reader (no API key needed)
  rss       — RSS/Atom procurement feeds
  github    — GitHub repo search via gh CLI
  reddit    — Reddit search via rdt-cli or OpenCLI (requires login)
  twitter   — Twitter/X via twitter-cli or OpenCLI (requires login)
  linkedin  — LinkedIn via linkedin-scraper-mcp
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path

BASE = Path(__file__).parent.parent

MODULE_MAP = {
    "manual_onboarding": BASE / "scrapers/manual_onboarding/nano_batch3.py",
    "adp_confirmed":     BASE / "scrapers/adp_confirmed/adp_finder.py",
    "rfp_rfq":           BASE / "scrapers/rfp_rfq/rfp_finder.py",
    "high_intent":       BASE / "scrapers/high_intent/intent_signals.py",
    # Agent-Reach powered channels
    "agent_reach":       BASE / "scrapers/agent_reach_signals/signal_finder.py",
    "agent_reach_web":   BASE / "scrapers/agent_reach_signals/signal_finder.py",
}

OUTPUT_MAP = {
    "manual_onboarding": BASE / "data/nano_batch3_leads.csv",
    "adp_confirmed":     BASE / "data/adp_confirmed_leads.csv",
    "rfp_rfq":           BASE / "data/rfp_rfq_leads.csv",
    "high_intent":       BASE / "data/high_intent_leads.csv",
    "agent_reach":       BASE / "data/agent_reach_leads.csv",
    "agent_reach_web":   BASE / "data/agent_reach_leads.csv",
}

# Extra args per module when running as subprocess
MODULE_EXTRA_ARGS = {
    "agent_reach_web": ["--channel", "web"],
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

    extra_args = MODULE_EXTRA_ARGS.get(module, [])
    result = subprocess.run(
        [sys.executable, "-u", str(script)] + extra_args,
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
                "https://sam.gov/search/?index=opp&q=HRIS&dateRange=custom&start=2026-01-01",
            ],
            "high_intent": [
                "https://duckduckgo.com/?q=%22evaluating+HRIS%22+OR+%22looking+for+HR+software%22&ia=web",
            ],
            "agent_reach": [
                "https://r.jina.ai/https://www.rfpmart.com/hr-services-rfp-government-contract.html",
                "https://r.jina.ai/https://www.instantmarkets.com/q/hris",
                "https://r.jina.ai/https://www.bidnetdirect.com/new-york/solicitations/open-bids/statewide/Human-Resources-Information-System-HRIS/444101967368",
            ],
            "agent_reach_web": [
                "https://r.jina.ai/https://www.rfpmart.com/hr-services-rfp-government-contract.html",
                "https://r.jina.ai/https://www.instantmarkets.com/q/hris",
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
    parser.add_argument(
        "--module",
        choices=list(MODULE_MAP.keys()) + ["all"],
        default=os.environ.get("MODULE", "manual_onboarding"),
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
