"""
Module: finance_analyzer.py
Description: Analyzes financial data using Pandas.
"""

"""
Module: finance_analyzer.py
Description: Analyzes financial data using Pandas.
"""
import sqlite3
import pandas as pd
import logging

class FinanceAnalyzer:
    def __init__(self, db_path="data/expenses.sqlite"):
        self.db_path = db_path

    def get_monthly_summary(self):
        """Returns total spending per category for the current month."""
        try:
            conn = sqlite3.connect(self.db_path)
            # Read SQL directly into a Pandas DataFrame
            df = pd.read_sql_query("SELECT * FROM expenses", conn)
            conn.close()

            if df.empty:
                return "No expenses logged yet."

            # Convert date column to datetime objects
            df['expense_date'] = pd.to_datetime(df['expense_date'])
            
            # Group by category and sum amounts
            summary = df.groupby('category')['amount'].sum()
            
            # Format the output
            result = "Spending Summary:\n"
            for category, total in summary.items():
                result += f"- {category.title()}: ${total:.2f}\n"
            
            return result

        except Exception as e:
            logging.error(f"Analysis error: {e}")
            return "Could not analyze data."