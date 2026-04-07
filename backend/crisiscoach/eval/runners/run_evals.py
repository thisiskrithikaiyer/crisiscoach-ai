"""Run all evaluations and output a summary score report."""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

DATASETS_DIR = Path(__file__).parent.parent / "datasets"
REPORTS_DIR = Path(__file__).parent.parent / "reports"


def load_dataset(name: str) -> list[dict]:
    path = DATASETS_DIR / f"{name}_golden.json"
    with open(path) as f:
        return json.load(f)


async def run_routing_eval() -> dict:
    from crisiscoach.eval.evaluators.routing_accuracy import score_routing
    cases = load_dataset("intake") + load_dataset("accountability") + load_dataset("checkin")
    routing_cases = [{"input": c["input"], "expected_intent": c["expected_intent"]} for c in cases if "input" in c and "expected_intent" in c]
    return score_routing(routing_cases)


async def run_all() -> dict:
    results = {}
    results["routing"] = await run_routing_eval()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"eval_report_{timestamp}.json"
    REPORTS_DIR.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n=== Eval Report ===")
    print(f"Routing accuracy: {results['routing']['accuracy']:.1%} ({results['routing']['correct']}/{results['routing']['total']})")
    print(f"Report saved: {report_path}")
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
