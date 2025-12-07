"""
Module: expenses_manager.py
Description: Manages expenses.
"""

# milo/managers/expenses_manager.py
import sqlite3
import os
from datetime import date

class ExpensesManager:
    def __init__(self, db_path="data/expenses.sqlite"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses 
            (id INTEGER PRIMARY KEY, amount REAL, category TEXT, date TEXT)
        """)

    def log_expense(self, amount, category):
        with self.conn:
            self.conn.execute("INSERT INTO expenses (amount, category, date) VALUES (?, ?, ?)", 
                              (amount, category.lower(), date.today().isoformat()))
        return f"Logged {amount} for {category}."