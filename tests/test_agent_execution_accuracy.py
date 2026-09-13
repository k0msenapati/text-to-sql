import pytest
from database import run_query
from evaluation.comparator import compare_results
from evaluation.dataset import BENCHMARK_CASES
from evaluation.runner import EvalStatus, evaluate_single_case


def test_all_ground_truth_queries_are_valid():
    """
    Sanity test: Verify that every benchmark case has syntactically valid ground-truth SQL
    and successfully executes against the actual database.
    """
    for case in BENCHMARK_CASES:
        rows = run_query(case.ground_truth_sql)
        assert isinstance(rows, list), f"Case {case.id} ground truth SQL failed to return a list"


@pytest.mark.parametrize("case_id", ["EASY-01", "EASY-02", "EASY-03", "MED-02"])
def test_agent_execution_accuracy_sample_queries(case_id: str):
    """
    Tests live agent execution accuracy on representative benchmark queries
    comparing generated SQL execution against pre-computed ground truth.
    """
    case = next(c for c in BENCHMARK_CASES if c.id == case_id)
    result = evaluate_single_case(case)

    # Assert that execution succeeded and matched expected results
    assert result.status == EvalStatus.PASSED, (
        f"Case {case_id} failed with status: {result.status}. "
        f"Reason: {result.comparison_reason or result.error_message}. "
        f"Generated SQL: {result.generated_sql}"
    )


def test_eval_runner_handles_failures_gracefully():
    """
    Verify that evaluate_single_case safely catches runtime execution errors
    without crashing unhandledly (e.g. when execute_sql raises sqlite3.OperationalError).
    """
    from evaluation.dataset import EvalTestCase

    broken_case = EvalTestCase(
        id="EDGE-01",
        question="Extract invalid json key from broken data.",
        ground_truth_sql="SELECT 1;",
        difficulty="hard",
        category="Error Handling",
    )

    # Even if the question triggers an agent crash or error, evaluate_single_case returns a CaseResult
    res = evaluate_single_case(broken_case)
    assert res.case_id == "EDGE-01"
    assert res.status in (
        EvalStatus.PASSED,
        EvalStatus.RESULT_MISMATCH,
        EvalStatus.EXECUTION_ERROR,
        EvalStatus.VALIDATION_ERROR,
        EvalStatus.AGENT_CRASH,
    )
