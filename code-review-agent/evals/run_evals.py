import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from agent.comment_formatter import format_github_comment
from agent.graph import get_graph
from evals.llm_judge import judge_review_comment
from evals.metrics import (
    measure_hallucination,
    measure_pass_at_k,
    semantic_scope_check,
)

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "true"

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


async def run_single(entry: dict, graph) -> dict:
    initial_state = {
        "repo_name": "eval/eval",
        "pr_number": int(entry["id"]),
        "analysis": {
            "summary": f"Eval entry {entry['id']}: {entry['description']}",
            "changed_functions": [
                {
                    "name": entry.get("affected_function", "target"),
                    "source": entry["buggy_code"],
                    "filename": "solution.py",
                    "start_line": 1,
                    "end_line": entry["buggy_code"].count("\n") + 1,
                    "is_changed": True,
                }
            ],
            "all_static_issues": [],
            "raw_diffs": {"solution.py": entry.get("patch_hint", "")},
            "file_contents": {
                "solution.py": entry["buggy_code"],
                "test_solution.py": entry["test_code"],
            },
        },
        "messages": [],
        "current_issue": "",
        "current_patch": "",
        "execution_result": {},
        "iteration": 0,
        "max_iterations": 3,
        "approved": False,
        "escalate": False,
        "review_issues": [],
        "final_comment": "",
    }

    try:
        final = await graph.ainvoke(initial_state)
        patch = final.get("current_patch", "")
        comment = format_github_comment(final)
        scope = semantic_scope_check(
            entry["buggy_code"],
            patch,
            entry.get("affected_function", "target"),
        )
        judge = judge_review_comment(comment, entry["expected_issues"], patch)

        return {
            "id": entry["id"],
            "pass_at_1": measure_pass_at_k(entry["buggy_code"], patch, entry["test_code"], k=1),
            "pass_at_3": measure_pass_at_k(entry["buggy_code"], patch, entry["test_code"], k=3),
            "hallucination_rate": round(
                measure_hallucination(entry["buggy_code"], patch, list(range(1, 20))), 3
            ),
            "judge_score": judge["score"],
            "judge_reason": judge["reason"],
            "iterations": final.get("iteration", 0),
            "scope_violation": scope["scope_violation"],
        }
    except Exception as exc:
        return {"id": entry["id"], "error": str(exc)}


async def main() -> None:
    dataset = [
        json.loads(line)
        for line in Path("evals/golden_dataset.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    graph = get_graph()

    print(f"Running evals on {len(dataset)} examples...")
    results = await asyncio.gather(*(run_single(entry, graph) for entry in dataset))
    valid = [result for result in results if "error" not in result]

    print(f"\n{'=' * 50}")
    print(f"Results ({len(valid)}/{len(dataset)} successful):")
    print(f"  pass@1:            {sum(r['pass_at_1'] for r in valid)/len(valid):.1%}")
    print(f"  pass@3:            {sum(r['pass_at_3'] for r in valid)/len(valid):.1%}")
    print(
        f"  hallucination:     "
        f"{sum(r['hallucination_rate'] for r in valid)/len(valid):.1%}"
    )
    print(f"  judge score (avg): {sum(r['judge_score'] for r in valid)/len(valid):.1f}/5")
    print(
        f"  scope violations:  "
        f"{sum(r['scope_violation'] for r in valid)/len(valid):.1%}"
    )
    print(f"{'=' * 50}\n")

    with open("evals/results.jsonl", "w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result) + "\n")
    print("Results saved to evals/results.jsonl")


if __name__ == "__main__":
    asyncio.run(main())
