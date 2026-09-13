import ast
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import logging
import sqlite3
import time
from typing import Any
from uuid import uuid4

from agent.agent import agent
from database import run_query
from evaluation.comparator import compare_results
from evaluation.dataset import BENCHMARK_CASES, EvalTestCase

logger = logging.getLogger(__name__)


class EvalStatus(str, Enum):
    PASSED = "PASSED"
    RESULT_MISMATCH = "RESULT_MISMATCH"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AGENT_CRASH = "AGENT_CRASH"


@dataclass
class CaseResult:
    case_id: str
    question: str
    difficulty: str
    category: str
    status: EvalStatus
    generated_sql: str | None = None
    ground_truth_sql: str | None = None
    expected_rows: list[dict[str, Any]] = field(default_factory=list)
    actual_rows: list[dict[str, Any]] = field(default_factory=list)
    agent_answer: str | None = None
    error_message: str | None = None
    comparison_reason: str | None = None
    retry_count: int = 0
    duration_ms: float = 0.0


@dataclass
class EvalSummary:
    total_queries: int = 0
    passed: int = 0
    result_mismatches: int = 0
    execution_errors: int = 0
    validation_errors: int = 0
    agent_crashes: int = 0
    accuracy_percentage: float = 0.0
    by_difficulty: dict[str, dict[str, Any]] = field(default_factory=dict)
    results: list[CaseResult] = field(default_factory=list)


def evaluate_single_case(case: EvalTestCase) -> CaseResult:
    """
    Evaluates a single benchmark case against the agent.
    Safely captures execution errors, validation failures, and result mismatches.
    """
    # 1. Compute ground-truth output from database
    try:
        expected_rows = run_query(case.ground_truth_sql)
    except Exception as e:
        return CaseResult(
            case_id=case.id,
            question=case.question,
            difficulty=case.difficulty,
            category=case.category,
            status=EvalStatus.AGENT_CRASH,
            error_message=f"Failed running ground truth SQL: {e}",
            ground_truth_sql=case.ground_truth_sql,
        )

    config = {"configurable": {"thread_id": f"eval-{case.id}-{uuid4()}"}}
    start_time = time.perf_counter()

    try:
        agent_response = agent.invoke({"question": case.question}, config=config)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        is_valid = agent_response.get("is_valid", True)
        generated_sql = agent_response.get("sql_query")
        agent_answer = agent_response.get("answer")
        retry_count = agent_response.get("retry_count", 0)

        # Case: Query failed validation after maximum retries
        if not is_valid:
            return CaseResult(
                case_id=case.id,
                question=case.question,
                difficulty=case.difficulty,
                category=case.category,
                status=EvalStatus.VALIDATION_ERROR,
                generated_sql=generated_sql,
                ground_truth_sql=case.ground_truth_sql,
                expected_rows=expected_rows,
                error_message=agent_response.get("validation_error"),
                agent_answer=agent_answer,
                retry_count=retry_count,
                duration_ms=elapsed_ms,
            )

        # Parse returned SQL output rows
        actual_output_str = agent_response.get("sql_output", "[]")
        try:
            actual_rows = ast.literal_eval(actual_output_str) if actual_output_str else []
        except Exception:
            # Fallback to direct execution if string representation parsing fails
            actual_rows = run_query(generated_sql) if generated_sql else []

        # Compare actual result with pre-computed / ground-truth result
        is_match, reason = compare_results(
            actual=actual_rows,
            expected=expected_rows,
            order_matters=case.order_matters,
        )

        status = EvalStatus.PASSED if is_match else EvalStatus.RESULT_MISMATCH

        return CaseResult(
            case_id=case.id,
            question=case.question,
            difficulty=case.difficulty,
            category=case.category,
            status=status,
            generated_sql=generated_sql,
            ground_truth_sql=case.ground_truth_sql,
            expected_rows=expected_rows,
            actual_rows=actual_rows,
            agent_answer=agent_answer,
            comparison_reason=reason,
            retry_count=retry_count,
            duration_ms=elapsed_ms,
        )

    except sqlite3.OperationalError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        # NOTE: This happens specifically because execute_sql node crashes
        # when a runtime query error occurs, since diagnose_exec_error is not yet implemented.
        return CaseResult(
            case_id=case.id,
            question=case.question,
            difficulty=case.difficulty,
            category=case.category,
            status=EvalStatus.EXECUTION_ERROR,
            error_message=(
                f"sqlite3.OperationalError: {e} "
                "(Crashed during execution - diagnose_exec_error node not present)"
            ),
            ground_truth_sql=case.ground_truth_sql,
            expected_rows=expected_rows,
            duration_ms=elapsed_ms,
        )

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return CaseResult(
            case_id=case.id,
            question=case.question,
            difficulty=case.difficulty,
            category=case.category,
            status=EvalStatus.AGENT_CRASH,
            error_message=f"{type(e).__name__}: {e}",
            ground_truth_sql=case.ground_truth_sql,
            expected_rows=expected_rows,
            duration_ms=elapsed_ms,
        )


def run_evaluation(
    cases: list[EvalTestCase] | None = None,
    difficulty: str | None = None,
    on_case_done: Any | None = None,
) -> EvalSummary:
    """
    Runs the evaluation suite across specified cases and returns an EvalSummary.
    """
    test_cases = cases or BENCHMARK_CASES
    if difficulty:
        test_cases = [c for c in test_cases if c.difficulty.lower() == difficulty.lower()]

    summary = EvalSummary(total_queries=len(test_cases))
    diff_stats: dict[str, dict[str, int]] = {
        "easy": {"total": 0, "passed": 0},
        "medium": {"total": 0, "passed": 0},
        "hard": {"total": 0, "passed": 0},
        "challenge": {"total": 0, "passed": 0},
    }

    for case in test_cases:
        result = evaluate_single_case(case)
        summary.results.append(result)

        d = case.difficulty.lower()
        if d in diff_stats:
            diff_stats[d]["total"] += 1

        if result.status == EvalStatus.PASSED:
            summary.passed += 1
            if d in diff_stats:
                diff_stats[d]["passed"] += 1
        elif result.status == EvalStatus.RESULT_MISMATCH:
            summary.result_mismatches += 1
        elif result.status == EvalStatus.EXECUTION_ERROR:
            summary.execution_errors += 1
        elif result.status == EvalStatus.VALIDATION_ERROR:
            summary.validation_errors += 1
        elif result.status == EvalStatus.AGENT_CRASH:
            summary.agent_crashes += 1

        if on_case_done:
            on_case_done(result)

    if summary.total_queries > 0:
        summary.accuracy_percentage = round((summary.passed / summary.total_queries) * 100, 1)

    summary.by_difficulty = {
        d: {
            "total": s["total"],
            "passed": s["passed"],
            "accuracy": (
                round((s["passed"] / s["total"]) * 100, 1) if s["total"] > 0 else 0.0
            ),
        }
        for d, s in diff_stats.items()
        if s["total"] > 0
    }

    return summary


def save_report_to_json(summary: EvalSummary, filepath: str = "eval_report.json"):
    """Saves evaluation results and summary statistics to a JSON file."""
    data = {
        "summary": {
            "total_queries": summary.total_queries,
            "passed": summary.passed,
            "accuracy_percentage": summary.accuracy_percentage,
            "result_mismatches": summary.result_mismatches,
            "execution_errors": summary.execution_errors,
            "validation_errors": summary.validation_errors,
            "agent_crashes": summary.agent_crashes,
            "by_difficulty": summary.by_difficulty,
        },
        "results": [asdict(r) for r in summary.results],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
