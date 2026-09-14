"""Evaluation module for text-to-sql agent benchmarking and execution accuracy."""
from evaluation.comparator import compare_results, normalize_value
from evaluation.dataset import BENCHMARK_CASES, EvalTestCase
from evaluation.intent_dataset import INTENT_BENCHMARK_CASES, IntentTestCase
from evaluation.intent_runner import (
    IntentCaseResult,
    IntentEvalSummary,
    evaluate_single_intent_case,
    run_intent_evaluation,
    save_intent_report_to_json,
)
from evaluation.runner import (
    CaseResult,
    EvalStatus,
    EvalSummary,
    evaluate_single_case,
    run_evaluation,
    save_report_to_json,
)

__all__ = [
    "compare_results",
    "normalize_value",
    "BENCHMARK_CASES",
    "EvalTestCase",
    "CaseResult",
    "EvalStatus",
    "EvalSummary",
    "evaluate_single_case",
    "run_evaluation",
    "save_report_to_json",
    "INTENT_BENCHMARK_CASES",
    "IntentTestCase",
    "IntentCaseResult",
    "IntentEvalSummary",
    "evaluate_single_intent_case",
    "run_intent_evaluation",
    "save_intent_report_to_json",
]
