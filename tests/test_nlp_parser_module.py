import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

try:
    from src.nlp.nlp_parser import NLPParser
except Exception:
    from nlp.nlp_parser import NLPParser


class TestNLPParserModule(unittest.TestCase):
    def test_order_agnostic_expense_phrase(self):
        parser = NLPParser()
        parser._llm_disabled = True  # Lock to deterministic fallback behavior for this regression test

        result = parser.parse("for food add a 50")

        self.assertEqual(result.get("intent"), "add_expense")
        entities = result.get("entities", {})
        self.assertEqual(entities.get("amount"), 50.0)
        self.assertEqual(entities.get("category"), "food")

    def test_task_phrase_with_bare_hour_keeps_clean_title(self):
        parser = NLPParser()
        parser._llm_disabled = True

        result = parser.parse("add task to create ui for tomorrow 4")

        self.assertEqual(result.get("intent"), "create_task")
        entities = result.get("entities", {})
        self.assertEqual(entities.get("title"), "create ui")
        self.assertIn("date", entities)


if __name__ == "__main__":
    unittest.main()
