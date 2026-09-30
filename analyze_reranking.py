"""Compare retrieval metrics before and after lexical reranking for Exercise 3.5.

The reranker sees only the question and previously retrieved chunks. The
expected answer is used afterward to evaluate the two fixed chunk sets.
"""

import json
from pathlib import Path

from template import RAGASEvaluator, rerank_by_overlap


ROOT = Path(__file__).resolve().parent
SELECTED_IDS = ("E01", "M02", "M04", "M05", "M07")


def main() -> None:
    golden = json.loads((ROOT / "golden_dataset.json").read_text(encoding="utf-8"))
    actual = json.loads((ROOT / "artifacts/actual_answers.json").read_text(encoding="utf-8"))
    gold_by_id = {record["id"]: record for record in golden["qa_pairs"]}
    evaluator = RAGASEvaluator()
    measurements: list[tuple[float, float, float, float]] = []

    print("| ID | Recall before | Recall after | Precision before | Precision after | Delta Precision |")
    print("|---|---:|---:|---:|---:|---:|")
    for answer in actual["answers"]:
        if answer["id"] not in SELECTED_IDS:
            continue
        record = gold_by_id[answer["id"]]
        chunks = [context["text"] for context in answer["retrieved_contexts"]]
        reranked = rerank_by_overlap(chunks, record["question"])
        if sorted(reranked) != sorted(chunks):
            raise ValueError(f"Reranking changed the retrieved set for {answer['id']}")

        expected = record["expected_answer"]
        recall_before = evaluator.evaluate_context_recall(chunks, expected)
        recall_after = evaluator.evaluate_context_recall(reranked, expected)
        if recall_before != recall_after:
            raise ValueError(f"Reranking changed recall for {answer['id']}")
        precision_before = evaluator.evaluate_context_precision(chunks, expected)
        precision_after = evaluator.evaluate_context_precision(reranked, expected)
        measurements.append((recall_before, recall_after, precision_before, precision_after))
        print(
            f"| {answer['id']} | {recall_before:.3f} | {recall_after:.3f} | "
            f"{precision_before:.3f} | {precision_after:.3f} | "
            f"{precision_after - precision_before:+.3f} |"
        )
    if len(measurements) != len(SELECTED_IDS):
        raise ValueError("One or more selected IDs were missing from actual answers")
    averages = [sum(row[index] for row in measurements) / len(measurements)
                for index in range(4)]
    print(
        f"| **Avg** | {averages[0]:.3f} | {averages[1]:.3f} | "
        f"{averages[2]:.3f} | {averages[3]:.3f} | "
        f"{averages[3] - averages[2]:+.3f} |"
    )


if __name__ == "__main__":
    main()
