"""
Module: memory_manager.py
Description: Manages memory storage.
"""

# milo/managers/memory_manager.py
import sqlite3
import os

class MemoryManager:
    def __init__(self, db_path="data/memory.sqlite"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("CREATE TABLE IF NOT EXISTS facts (key TEXT PRIMARY KEY, value TEXT)")

    def remember(self, key, value):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO facts VALUES (?, ?)", (key.lower(), value))
        return f"I remembered that {key} is {value}."

    def recall(self, key):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM facts WHERE key=?", (key.lower(),))
        res = cursor.fetchone()
        return res[0] if res else None