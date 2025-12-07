"""
Module: reminder_manager.py
Description: Manages reminders.
"""

# milo/managers/reminder_manager.py
import sqlite3
import os

class ReminderManager:
    def __init__(self, db_path="data/reminders.sqlite"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders 
            (id INTEGER PRIMARY KEY, text TEXT, time TEXT, status TEXT)
        """)

    def add_reminder(self, text, time):
        with self.conn:
            self.conn.execute("INSERT INTO reminders (text, time, status) VALUES (?, ?, 'pending')", (text, time))
        return f"Reminder set for {text}."