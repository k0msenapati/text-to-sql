from evaluation.comparator import compare_results, normalize_value


def test_normalize_value():
    assert normalize_value(" Alice  ") == "alice"
    assert normalize_value(42.000) == 42.0
    assert normalize_value("123.45") == 123.45
    assert normalize_value(None) is None


def test_empty_results():
    assert compare_results([], [])[0] is True
    assert compare_results([{"a": 1}], [])[0] is False
    assert compare_results([], [{"a": 1}])[0] is False


def test_scalar_matching_different_alias():
    actual = [{"COUNT(*)": 8}]
    expected = [{"total_count": 8}]
    matched, reason = compare_results(actual, expected)
    assert matched is True
    assert "Scalar values match" in reason


def test_scalar_matching_float_tolerance():
    actual = [{"percentage": 50.01}]
    expected = [{"shipped_percentage": 50.0}]
    matched, reason = compare_results(actual, expected)
    assert matched is True


def test_order_independent_matching():
    actual = [{"name": "Bob"}, {"name": "Alice"}]
    expected = [{"name": "Alice"}, {"name": "Bob"}]
    matched, _ = compare_results(actual, expected, order_matters=False)
    assert matched is True


def test_order_dependent_matching():
    actual = [{"name": "Bob"}, {"name": "Alice"}]
    expected = [{"name": "Alice"}, {"name": "Bob"}]
    matched, reason = compare_results(actual, expected, order_matters=True)
    assert matched is False
    assert "Order/value mismatch" in reason

    # Correct order
    matched_ordered, _ = compare_results(expected, expected, order_matters=True)
    assert matched_ordered is True


def test_extra_columns_subset_matching():
    # LLM returned id and name, but expected only checks name
    actual = [
        {"customer_id": 1, "name": "Alice"},
        {"customer_id": 2, "name": "Bob"},
    ]
    expected = [
        {"name": "Bob"},
        {"name": "Alice"},
    ]
    matched, reason = compare_results(actual, expected, order_matters=False)
    assert matched is True
    assert "Rows match on projected columns" in reason


def test_row_count_mismatch():
    actual = [{"name": "Alice"}]
    expected = [{"name": "Alice"}, {"name": "Bob"}]
    matched, reason = compare_results(actual, expected)
    assert matched is False
    assert "Row count mismatch" in reason
