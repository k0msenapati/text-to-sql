from collections import Counter
from itertools import combinations
import math
from typing import Any


def normalize_value(val: Any) -> Any:
    """Normalize values for robust comparisons across SQL outputs."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    if isinstance(val, str):
        cleaned = val.strip()
        try:
            num = float(cleaned)
            return round(num, 2)
        except ValueError:
            return cleaned.lower()
    return val


def compare_results(
    actual: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    order_matters: bool = False,
) -> tuple[bool, str]:
    """
    Compares the execution output of a generated SQL query against the ground-truth output.

    Features:
    - Handles scalar matching (e.g., COUNT, SUM, AVG) regardless of alias name.
    - Compares row content independently of order when order_matters=False.
    - Preserves ordering checks when order_matters=True (e.g., ORDER BY + LIMIT).
    - Tolerates extra projected columns in actual output (e.g., returning ID along with NAME).
    - Tolerates minor floating-point differences.

    Returns:
        (is_match: bool, reason: str)
    """
    if not actual and not expected:
        return True, "Both result sets are empty"

    if not actual and expected:
        return False, f"Actual result is empty, but expected {len(expected)} row(s)"

    if actual and not expected:
        return False, f"Expected result is empty, but actual returned {len(actual)} row(s)"

    # 1. Single scalar comparison (e.g., COUNT, SUM, single calculated metric)
    if len(expected) == 1 and len(expected[0]) == 1:
        exp_val = normalize_value(list(expected[0].values())[0])
        if len(actual) == 1:
            for act_val_raw in actual[0].values():
                act_val = normalize_value(act_val_raw)
                if act_val == exp_val:
                    return True, f"Scalar values match: {act_val}"
                if (
                    isinstance(act_val, float)
                    and isinstance(exp_val, float)
                    and math.isclose(act_val, exp_val, abs_tol=0.05)
                ):
                    return True, f"Scalar values match within float tolerance ({act_val} ~ {exp_val})"
            return False, f"Scalar mismatch: expected {exp_val}, got {actual[0]}"

    # 2. Row count check
    if len(actual) != len(expected):
        return False, f"Row count mismatch: expected {len(expected)} rows, got {len(actual)} rows"

    exp_col_count = len(expected[0])
    act_col_count = len(actual[0])
    exp_tuples = [tuple(normalize_value(v) for v in row.values()) for row in expected]

    # 3. Direct column count match
    if act_col_count == exp_col_count:
        act_tuples = [tuple(normalize_value(v) for v in row.values()) for row in actual]
        if order_matters:
            if act_tuples == exp_tuples:
                return True, "Rows and order match exactly"
            return False, f"Order/value mismatch: actual {act_tuples[:3]}... != expected {exp_tuples[:3]}..."
        else:
            if Counter(act_tuples) == Counter(exp_tuples):
                return True, "Rows match (order-independent)"
            return False, f"Row content mismatch: actual {act_tuples[:3]}... != expected {exp_tuples[:3]}..."

    # 4. Actual has more columns than expected (e.g. LLM projected id and name instead of just name)
    if act_col_count > exp_col_count:
        act_keys = list(actual[0].keys())
        for col_subset in combinations(act_keys, exp_col_count):
            act_subset_tuples = [
                tuple(normalize_value(row[col]) for col in col_subset) for row in actual
            ]
            if order_matters:
                if act_subset_tuples == exp_tuples:
                    return True, f"Rows and order match on projected columns: {col_subset}"
            else:
                if Counter(act_subset_tuples) == Counter(exp_tuples):
                    return True, f"Rows match on projected columns: {col_subset}"

        return (
            False,
            f"Column count mismatch: actual has {act_col_count} cols, expected {exp_col_count}, and no column subset matched",
        )

    return False, f"Column count mismatch: expected {exp_col_count} cols, but actual only has {act_col_count}"
