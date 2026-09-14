from dataclasses import asdict, dataclass, field
import json
import logging
import time
from typing import Any

from classifier import classify_query_intent
from evaluation.intent_dataset import INTENT_BENCHMARK_CASES, IntentTestCase

logger = logging.getLogger(__name__)


@dataclass
class IntentCaseResult:
    case_id: str
    question: str
    category: str
    expected_intent: str
    predicted_intent: str | None = None
    is_match: bool = False
    duration_ms: float = 0.0
    error_message: str | None = None


@dataclass
class IntentEvalSummary:
    total_queries: int = 0
    passed: int = 0
    failed: int = 0
    accuracy_percentage: float = 0.0
    by_intent: dict[str, dict[str, Any]] = field(default_factory=dict)
    results: list[IntentCaseResult] = field(default_factory=list)


def evaluate_single_intent_case(case: IntentTestCase) -> IntentCaseResult:
    """
    Evaluates intent classification accuracy on a single benchmark case.
    """
    start_time = time.perf_counter()
    try:
        predicted = classify_query_intent(case.question)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        is_match = predicted == case.expected_intent

        return IntentCaseResult(
            case_id=case.id,
            question=case.question,
            category=case.category,
            expected_intent=case.expected_intent,
            predicted_intent=predicted,
            is_match=is_match,
            duration_ms=elapsed_ms,
        )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.error("[evaluate_single_intent_case] Error on %s: %s", case.id, e)
        return IntentCaseResult(
            case_id=case.id,
            question=case.question,
            category=case.category,
            expected_intent=case.expected_intent,
            predicted_intent=None,
            is_match=False,
            duration_ms=elapsed_ms,
            error_message=str(e),
        )


def run_intent_evaluation(
    cases: list[IntentTestCase] | None = None,
    intent_filter: str | None = None,
    on_case_done: Any | None = None,
) -> IntentEvalSummary:
    """
    Runs intent classification evaluation across test cases and returns summary metrics.
    """
    test_cases = cases or INTENT_BENCHMARK_CASES
    if intent_filter and intent_filter.lower() != "all":
        test_cases = [
            c for c in test_cases if c.expected_intent.lower() == intent_filter.lower()
        ]

    summary = IntentEvalSummary(total_queries=len(test_cases))
    intent_stats: dict[str, dict[str, int]] = {
        "data_query": {"total": 0, "passed": 0},
        "metadata_query": {"total": 0, "passed": 0},
        "ambiguous_query": {"total": 0, "passed": 0},
        "out_of_scope_query": {"total": 0, "passed": 0},
    }

    for case in test_cases:
        result = evaluate_single_intent_case(case)
        summary.results.append(result)

        target = case.expected_intent
        if target in intent_stats:
            intent_stats[target]["total"] += 1

        if result.is_match:
            summary.passed += 1
            if target in intent_stats:
                intent_stats[target]["passed"] += 1
        else:
            summary.failed += 1

        if on_case_done:
            on_case_done(result)

    if summary.total_queries > 0:
        summary.accuracy_percentage = round(
            (summary.passed / summary.total_queries) * 100, 1
        )

    summary.by_intent = {
        intent: {
            "total": s["total"],
            "passed": s["passed"],
            "accuracy": (
                round((s["passed"] / s["total"]) * 100, 1) if s["total"] > 0 else 0.0
            ),
        }
        for intent, s in intent_stats.items()
        if s["total"] > 0
    }

    return summary


def save_intent_report_to_json(
    summary: IntentEvalSummary, filepath: str = "eval_intent_report.json"
):
    """Saves intent evaluation results and summary statistics to a JSON file."""
    data = {
        "summary": {
            "total_queries": summary.total_queries,
            "passed": summary.passed,
            "failed": summary.failed,
            "accuracy_percentage": summary.accuracy_percentage,
            "by_intent": summary.by_intent,
        },
        "results": [asdict(r) for r in summary.results],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
