"""
Database module for MILO - Managing Information & Lifestyle Optimizer
Handles all database operations for tasks, finances, and habits
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class Database:
    """Manages all database operations for MILO"""
    
    def __init__(self, db_path: str = "data/milo.db"):
        """Initialize database connection and create tables"""
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Optimize SQLite for better performance
        self.conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        self.conn.execute("PRAGMA synchronous=NORMAL")  # Balanced sync mode
        self.conn.execute("PRAGMA cache_size=10000")  # Larger cache
        self.conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp
        self.conn.execute("PRAGMA query_only=OFF")  # Allow writes
        
        # Enable foreign key constraints
        self.conn.execute("PRAGMA foreign_keys=ON")
        
        self.create_tables()
        self.migrate_schema()
        self.create_indexes()
    
    def migrate_schema(self):
        """Perform schema migrations for existing databases"""
        cursor = self.conn.cursor()
        
        # Check for category column in tasks
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'category' not in columns:
            try:
                print("Migrating: Adding category column to tasks table")
                cursor.execute("ALTER TABLE tasks ADD COLUMN category TEXT DEFAULT 'general'")
            except sqlite3.OperationalError as e:
                # Handle case where table might not exist yet (though it should be created by now)
                print(f"Migration warning: {e}")
            
        # Check for reminder_time column in habits
        cursor.execute("PRAGMA table_info(habits)")
        habit_columns = [info[1] for info in cursor.fetchall()]
        if 'reminder_time' not in habit_columns:
            try:
                print("Migrating: Adding reminder_time column to habits table")
                cursor.execute("ALTER TABLE habits ADD COLUMN reminder_time TEXT DEFAULT '20:00'")
            except sqlite3.OperationalError as e:
                print(f"Migration warning: {e}")

        self.conn.commit()
    
    def create_tables(self):
        """Create all required tables"""
        cursor = self.conn.cursor()
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                category TEXT DEFAULT 'general',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        """)
        
        # Subtasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subtasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        
        # Finances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS finances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                date TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Habits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                target_frequency TEXT,
                reminder_time TEXT DEFAULT '20:00',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Habit logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                completed INTEGER DEFAULT 1,
                notes TEXT,
                FOREIGN KEY (habit_id) REFERENCES habits(id)
            )
        """)
        
        # User activity table for habit learning
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_type TEXT NOT NULL,
                activity_data TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()

    def create_indexes(self):
        """Create all required indexes for optimal performance"""
        cursor = self.conn.cursor()

        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_completed_at ON tasks(completed_at)")

        # Composite indexes for common query patterns
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status_due_date ON tasks(status, due_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status_priority ON tasks(status, priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status_category ON tasks(status, category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_category_priority ON tasks(category, priority)")

        # Full-text search index for title and description
        cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS tasks_fts USING fts5(title, description, content='tasks', content_rowid='id')")

        # Triggers to keep FTS table in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS tasks_fts_insert AFTER INSERT ON tasks
            BEGIN
                INSERT INTO tasks_fts(rowid, title, description) VALUES (new.id, new.title, new.description);
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS tasks_fts_delete AFTER DELETE ON tasks
            BEGIN
                DELETE FROM tasks_fts WHERE rowid = old.id;
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS tasks_fts_update AFTER UPDATE ON tasks
            BEGIN
                UPDATE tasks_fts SET title = new.title, description = new.description WHERE rowid = new.id;
            END
        """)

        # Other table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subtasks_task_id ON subtasks(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_finances_date ON finances(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_finances_type ON finances(transaction_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_finances_category ON finances(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_finances_type_date ON finances(transaction_type, date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_finances_category_type ON finances(category, transaction_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_finances_date_type ON finances(date, transaction_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_habit_id ON habit_logs(habit_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_date ON habit_logs(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_type ON user_activity(activity_type)")

        self.conn.commit()
    
    # Task operations
    def add_task(self, title: str, description: str = "", due_date: str = None, 
                 priority: str = "medium", category: str = "general") -> int:
        """Add a new task"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (title, description, due_date, priority, category)
            VALUES (?, ?, ?, ?, ?)
        """, (title, description, due_date, priority, category))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_tasks(self, status: str = None) -> List[Dict]:
        """Get all tasks, optionally filtered by status"""
        cursor = self.conn.cursor()
        if status:
            cursor.execute("SELECT * FROM tasks WHERE status = ? ORDER BY due_date, priority", (status,))
        else:
            cursor.execute("SELECT * FROM tasks ORDER BY due_date, priority")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        """Update a task"""
        cursor = self.conn.cursor()
        allowed_fields = ['title', 'description', 'due_date', 'priority', 'status', 'completed_at', 'category']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # Finance operations
    def add_transaction(self, transaction_type: str, category: str, 
                       amount: float, description: str = "") -> int:
        """Add a financial transaction"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO finances (transaction_type, category, amount, description)
            VALUES (?, ?, ?, ?)
        """, (transaction_type, category, amount, description))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_transactions(self, limit: int = 50) -> List[Dict]:
        """Get recent transactions"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM finances 
            ORDER BY date DESC 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_balance(self) -> float:
        """Get current balance (income - expenses)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expenses
            FROM finances
        """)
        result = cursor.fetchone()
        income = result[0] or 0
        expenses = result[1] or 0
        return income - expenses
    
    def get_expenses_by_category(self) -> List[Tuple[str, float]]:
        """Get total expenses grouped by category"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM finances
            WHERE transaction_type = 'expense'
            GROUP BY category
            ORDER BY total DESC
        """)
        return cursor.fetchall()
    
    # Habit operations
    def add_habit(self, name: str, description: str = "", target_frequency: str = "daily", reminder_time: str = "20:00") -> int:
        """Add a new habit"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO habits (name, description, target_frequency, reminder_time)
            VALUES (?, ?, ?, ?)
        """, (name, description, target_frequency, reminder_time))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_habits(self) -> List[Dict]:
        """Get all habits"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM habits ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def log_habit(self, habit_id: int, date: str = None, notes: str = "") -> int:
        """Log habit completion"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO habit_logs (habit_id, date, notes)
            VALUES (?, ?, ?)
        """, (habit_id, date, notes))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_habit_stats(self, habit_id: int, days: int = 30) -> Dict:
        """Get habit completion statistics"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as completed_count
            FROM habit_logs
            WHERE habit_id = ? 
            AND date >= date('now', '-' || ? || ' days')
        """, (habit_id, days))
        result = cursor.fetchone()
        return {'completed_count': result[0] if result else 0, 'days': days}
    
    # Activity logging for habit learning
    def log_activity(self, activity_type: str, activity_data: str = ""):
        """Log user activity for habit learning"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO user_activity (activity_type, activity_data)
            VALUES (?, ?)
        """, (activity_type, activity_data))
        self.conn.commit()
    
    def get_activity_patterns(self, activity_type: str, days: int = 7) -> List[Dict]:
        """Get activity patterns for habit learning"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM user_activity
            WHERE activity_type = ?
            AND timestamp >= date('now', '-' || ? || ' days')
            ORDER BY timestamp DESC
        """, (activity_type, days))
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        self.conn.close()
