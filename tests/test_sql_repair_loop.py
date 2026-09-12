import unittest
from unittest.mock import MagicMock, patch

import nodes
from agent import agent, route_after_validation
from database import db_manager, validate_sql_query
from nodes import repair_sql, validate_sql


class TestSQLValidator(unittest.TestCase):
    def test_validate_empty_query(self):
        result = validate_sql_query("")
        self.assertFalse(result["is_valid"])
        self.assertIn("empty", result["validation_error"].lower())

    def test_validate_non_select_query(self):
        result = validate_sql_query("DELETE FROM customers WHERE customer_id = 1")
        self.assertFalse(result["is_valid"])
        self.assertIn("select", result["validation_error"].lower())

    def test_validate_syntax_error(self):
        result = validate_sql_query("SELECT * FORM customers")
        self.assertFalse(result["is_valid"])
        self.assertIn("syntax error", result["validation_error"].lower())

    def test_validate_non_existent_table(self):
        result = validate_sql_query("SELECT * FROM non_existent_table")
        self.assertFalse(result["is_valid"])
        self.assertIn("no such table", result["validation_error"].lower())

    def test_validate_non_existent_column(self):
        result = validate_sql_query("SELECT nonexistent_col FROM customers")
        self.assertFalse(result["is_valid"])
        self.assertIn("no such column", result["validation_error"].lower())

    def test_validate_valid_query(self):
        result = validate_sql_query("SELECT name, email FROM customers")
        self.assertTrue(result["is_valid"])
        self.assertIsNone(result["validation_error"])


class TestValidationAndRepairNodes(unittest.TestCase):
    def test_validate_sql_node_updates_state(self):
        state = {"sql_query": "SELECT invalid_col FROM customers"}
        output = validate_sql(state)
        self.assertFalse(output["is_valid"])
        self.assertIn("no such column", output["validation_error"])

    @patch.object(nodes, "llm")
    def test_repair_sql_node_increments_retry_and_fixes_query(self, mock_llm):
        mock_response = MagicMock()
        mock_response.content = "```sql\nSELECT name FROM customers\n```"
        mock_llm.invoke.return_value = mock_response

        state = {
            "schema": str(db_manager.get_schema()),
            "question": "Show all customer names",
            "sql_query": "SELECT invalid_col FROM customers",
            "validation_error": "no such column: invalid_col",
            "retry_count": 0,
        }

        output = repair_sql(state)
        self.assertEqual(output["retry_count"], 1)
        self.assertEqual(output["sql_query"], "SELECT name FROM customers")


class TestRoutingAndLoopLogic(unittest.TestCase):
    def test_route_after_validation_valid(self):
        state = {"is_valid": True, "retry_count": 0}
        self.assertEqual(route_after_validation(state), "execute_sql")

    def test_route_after_validation_invalid_under_max_retries(self):
        state = {"is_valid": False, "retry_count": 0}
        self.assertEqual(route_after_validation(state), "repair_sql")

        state = {"is_valid": False, "retry_count": 2}
        self.assertEqual(route_after_validation(state), "repair_sql")

    def test_route_after_validation_invalid_reaches_max_retries(self):
        state = {"is_valid": False, "retry_count": 3}
        self.assertEqual(route_after_validation(state), "format_answer")


class TestAgentGraphLoop(unittest.TestCase):
    @patch.object(nodes, "llm")
    def test_agent_repairs_sql_and_succeeds(self, mock_llm):
        # 1st call (generate_sql): returns bad query with nonexistent column
        # 2nd call (repair_sql): returns valid query
        # 3rd call (format_answer): returns final answer
        bad_sql_resp = MagicMock(content="SELECT bad_col FROM customers")
        repaired_sql_resp = MagicMock(content="SELECT name FROM customers")
        answer_resp = MagicMock(content="Here are the customer names: Alice, Bob, Charlie.")

        mock_llm.invoke.side_effect = [bad_sql_resp, repaired_sql_resp, answer_resp]

        config = {"configurable": {"thread_id": "test-repair-success"}}
        result = agent.invoke({"question": "List all customer names"}, config=config)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["retry_count"], 1)
        self.assertEqual(result["sql_query"], "SELECT name FROM customers")
        self.assertEqual(result["answer"], "Here are the customer names: Alice, Bob, Charlie.")

    @patch.object(nodes, "llm")
    def test_agent_stops_at_max_retries_when_unrepairable(self, mock_llm):
        # 1st call: generate bad sql
        # 2nd, 3rd, 4th calls: repair returns bad sql 3 times
        bad_sql_resp = MagicMock(content="SELECT still_bad FROM customers")
        mock_llm.invoke.return_value = bad_sql_resp

        config = {"configurable": {"thread_id": "test-repair-fail"}}
        result = agent.invoke({"question": "Show me something"}, config=config)

        self.assertFalse(result["is_valid"])
        self.assertEqual(result["retry_count"], 3)
        self.assertIn("could not be validated", result["answer"])


if __name__ == "__main__":
    unittest.main()
