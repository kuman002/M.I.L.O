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
    from src.automation.computer_use import ContextEngine, MiloHands, MiloEyes
    from src.automation.rpa_service import RPAService
except Exception:
    from automation.computer_use import ContextEngine, MiloHands, MiloEyes
    from automation.rpa_service import RPAService


class TestAutomationModules(unittest.TestCase):
    def test_context_engine_returns_string(self):
        context = ContextEngine.get_active_context()
        self.assertIsInstance(context, str)
        self.assertIn(context, {"unknown", "notepad", "browser", "vscode", "terminal"})

    def test_hands_availability_flag(self):
        self.assertIsInstance(MiloHands.is_available(), bool)

    def test_rpa_context_wrapper(self):
        rpa = RPAService()
        context = rpa.get_active_context()
        self.assertIsInstance(context, str)

    def test_rpa_search_empty_query_is_rejected(self):
        rpa = RPAService()
        result = rpa.search_in_browser_context("")
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("success", True))
        self.assertIn("empty", result.get("message", "").lower())

    def test_eyes_availability_flag(self):
        eyes = MiloEyes(gpu=False)
        self.assertIsInstance(eyes.is_available(), bool)


if __name__ == "__main__":
    unittest.main()
