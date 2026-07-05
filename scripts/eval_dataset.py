"""Evaluate the CLASSIFIER against the 30 labeled emails, and cache the result for the
dashboard. Classification-only (no graph/tools/HITL) - evaluation measures the model and
stays separate from the live operational pipeline.

Runs ~30 real classifications. Run from the repo root:  python scripts/eval_dataset.py
"""
import sys, os, json
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servicedesk.schema import IncomingEmail
from servicedesk.llm import LLMClient
from servicedesk.hitl import needs_human

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(_ROOT, "data", "labeled_emails.json")
OUT = os.path.join(_ROOT, "data", "eval_results.json")


def main():
    rows = json.load(open(DATA))
    client = LLMClient()

    header = f"{'id':<8} {'difficulty':<10} {'expected':<22} {'predicted':<22} {'conf':<5} {'route':<6} ok"
    print(header); print("-" * len(header))
    results = []
    for r in rows:
        email = IncomingEmail(id=r["id"], sender=r["sender"], subject=r["subject"], body=r["body"])
        c = client.classify(email)
        correct = c.category.value == r["expected_category"]
        route = "human" if needs_human(c) else "auto"
        results.append({"id": r["id"], "difficulty": r["difficulty"],
                        "expected": r["expected_category"], "predicted": c.category.value,
                        "confidence": c.confidence, "route": route, "correct": correct})
        print(f"{r['id']:<8} {r['difficulty']:<10} {r['expected_category']:<22} "
              f"{c.category.value:<22} {c.confidence:<5.2f} {route:<6} {'OK' if correct else 'x'}")

    total = len(results)
    correct = sum(x["correct"] for x in results)
    by_difficulty = {}
    for d in ("clear", "ambiguous", "edge"):
        subset = [x for x in results if x["difficulty"] == d]
        by_difficulty[d] = {"total": len(subset), "correct": sum(x["correct"] for x in subset)}
    low_conf = sum(1 for x in results if x["confidence"] < 0.75)

    payload = {"accuracy": correct / total if total else 0.0, "total": total, "correct": correct,
               "by_difficulty": by_difficulty, "low_confidence": low_conf,
               "generated_at": datetime.now(timezone.utc).isoformat(), "rows": results}
    json.dump(payload, open(OUT, "w"), indent=2)

    print("-" * len(header))
    print(f"accuracy: {correct}/{total}    below 0.75 confidence: {low_conf}/{total}")
    print(f"cached -> {OUT}")


if __name__ == "__main__":
    main()
