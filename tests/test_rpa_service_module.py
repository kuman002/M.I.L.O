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
    from src.automation.rpa_service import RPAService
except Exception:
    from automation.rpa_service import RPAService


class TestRPAServiceModule(unittest.TestCase):
    def test_expand_spoken_keys_maps_linebreak_and_tab(self):
        rpa = RPAService()
        text = "hello world next line this is milo tab done enter"
        expanded = rpa._expand_spoken_keys(text)
        self.assertIn("\n", expanded)
        self.assertIn("\t", expanded)

    def test_expand_spoken_keys_preserves_regular_spaces(self):
        rpa = RPAService()
        text = "hello world how are you"
        expanded = rpa._expand_spoken_keys(text)
        self.assertEqual(expanded, text)

    def test_type_text_returns_fail_when_unavailable(self):
        rpa = RPAService()
        rpa.available = False
        rpa.is_available = False
        result = rpa.type_text("hello world")
        self.assertFalse(result.get("success", True))


if __name__ == "__main__":
    unittest.main()
