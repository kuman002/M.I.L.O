import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

try:
    from src.database.database import Database
    from src.managers.task_manager import TaskManager
    from src.managers.finance_manager import FinanceManager
    from src.managers.habit_manager import HabitManager
except Exception:
    from database.database import Database
    from managers.task_manager import TaskManager
    from managers.finance_manager import FinanceManager
    from managers.habit_manager import HabitManager


class TestManagersAndDatabaseModule(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "milo_test.db")
        self.db = Database(db_path=self.db_path)
        self.tasks = TaskManager(self.db)
        self.finance = FinanceManager(self.db)
        self.habits = HabitManager(self.db)

    def tearDown(self):
        try:
            self.db.close()
        finally:
            self._tmpdir.cleanup()

    def test_database_add_and_get_task(self):
        task_id = self.db.add_task("Write tests", due_date="2030-01-01", priority="high")
        self.assertIsInstance(task_id, int)
        rows = self.db.get_tasks(status="pending")
        self.assertTrue(any(row.get("title") == "Write tests" for row in rows))

    def test_database_balance_from_transactions(self):
        self.db.add_transaction("income", "salary", 1000.0, "monthly")
        self.db.add_transaction("expense", "food", 250.0, "groceries")
        self.assertAlmostEqual(self.db.get_balance(), 750.0, places=2)

    def test_task_manager_create_complete_delete_flow(self):
        created = self.tasks.create_task("Prepare review document", priority="medium")
        self.assertTrue(created.get("success"))
        task_id = created.get("task_id")

        completed = self.tasks.complete_task(task_id)
        self.assertTrue(completed.get("success"))

        deleted = self.tasks.delete_task(task_id)
        self.assertTrue(deleted.get("success"))

    def test_task_manager_rejects_empty_title(self):
        result = self.tasks.create_task("   ")
        self.assertFalse(result.get("success"))
        self.assertIn("title", result.get("message", "").lower())

    def test_finance_manager_add_and_summary(self):
        self.assertTrue(self.finance.add_income("salary", 1200.0).get("success"))
        self.assertTrue(self.finance.add_expense("food", 200.0).get("success"))

        summary = self.finance.get_summary(days=30)
        self.assertGreater(summary.get("total_income", 0), 0)
        self.assertGreater(summary.get("total_expenses", 0), 0)
        self.assertGreater(summary.get("balance", 0), 0)

    def test_finance_manager_rejects_invalid_category(self):
        result = self.finance.add_expense("food!!!", 50)
        self.assertFalse(result.get("success"))
        self.assertIn("category", result.get("message", "").lower())

    def test_habit_manager_blocks_duplicate_daily_log(self):
        habit = self.habits.add_habit("Read 20 pages")
        self.assertTrue(habit.get("success"))
        habit_id = habit.get("habit_id")

        first = self.habits.log_habit_completion(habit_id)
        second = self.habits.log_habit_completion(habit_id)

        self.assertTrue(first.get("success"))
        self.assertFalse(second.get("success"))

    def test_habit_manager_streak_is_computed(self):
        habit = self.habits.add_habit("Meditate")
        habit_id = habit.get("habit_id")
        self.habits.log_habit_completion(habit_id)

        habits = self.habits.get_habits()
        matched = next((h for h in habits if h.get("id") == habit_id), None)
        self.assertIsNotNone(matched)
        self.assertGreaterEqual(matched.get("streak", 0), 1)

    def test_habit_due_reminder_detected(self):
        habit = self.habits.add_habit("Walk", reminder_time="00:00")
        self.assertTrue(habit.get("success"))

        due = self.habits.get_due_habit_reminders()
        self.assertTrue(any(h.get("name") == "Walk" for h in due))


if __name__ == "__main__":
    unittest.main()
