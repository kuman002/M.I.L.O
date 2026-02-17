"""
Task Management Module for MILO
Handles task operations and scheduling with optimized performance
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from database.database import Database
import re


class TaskManager:
    """Manages tasks and reminders with optimized performance"""

    def __init__(self, database: Database):
        """Initialize task manager with database"""
        self.db = database
        self.reminded_task_ids = set()  # Track tasks already alerted in this session
        self._task_cache = {}  # Cache for frequently accessed tasks
        self._cache_timeout = 300  # 5 minutes cache timeout
        self._last_cache_update = 0

    def _invalidate_cache(self):
        """Invalidate the task cache"""
        self._task_cache.clear()
        self._last_cache_update = 0

    def _get_cached_tasks(self, cache_key: str, query_func, *args, **kwargs):
        """Get tasks from cache or execute query"""
        current_time = datetime.now().timestamp()

        # Check if cache is stale
        if current_time - self._last_cache_update > self._cache_timeout:
            self._invalidate_cache()

        if cache_key not in self._task_cache:
            self._task_cache[cache_key] = query_func(*args, **kwargs)
            self._last_cache_update = current_time

        return self._task_cache[cache_key]

    def _validate_task_data(self, title: str, priority: str = "medium", due_date: str = None) -> Tuple[bool, str]:
        """Validate task input data"""
        if not title or not title.strip():
            return False, "Task title cannot be empty"

        title = title.strip()
        if len(title) > 200:
            return False, "Task title too long (max 200 characters)"

        if priority not in ['low', 'medium', 'high', 'urgent']:
            return False, "Invalid priority level"

        if due_date:
            try:
                # Validate date format
                if ' ' in due_date:
                    datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
                else:
                    datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                return False, "Invalid date format (use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"

        return True, ""

    def create_task(self, title: str, description: str = "", due_date: str = None,
                   priority: str = "medium", category: str = "general") -> Dict:
        """Create a new task with validation"""
        is_valid, error_msg = self._validate_task_data(title, priority, due_date)
        if not is_valid:
            return {
                'success': False,
                'message': error_msg
            }

        try:
            task_id = self.db.add_task(title.strip(), description.strip(), due_date, priority, category)
            self._invalidate_cache()  # Invalidate cache since we added a task
            self.db.log_activity('task_created', f"Task: {title}")
            return {
                'success': True,
                'message': f"Task '{title}' created successfully.",
                'task_id': task_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to create task: {str(e)}"
            }
    
    def get_tasks(self, status: str = None, priority: str = None, category: str = None,
                 limit: int = None, offset: int = 0) -> List[Dict]:
        """Get tasks with advanced filtering and pagination"""
        cache_key = f"tasks_{status}_{priority}_{category}_{limit}_{offset}"

        def _query_tasks():
            # Build query dynamically
            conditions = []
            params = []

            if status:
                conditions.append("status = ?")
                params.append(status)

            if priority:
                conditions.append("priority = ?")
                params.append(priority)

            if category:
                conditions.append("category = ?")
                params.append(category)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # Add ordering: urgent first, then by due date, then by priority
            order_by = """
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END,
                due_date IS NULL, due_date,
                created_at DESC
            """

            query = f"SELECT * FROM tasks WHERE {where_clause} ORDER BY {order_by}"

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor = self.db.conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

        return self._get_cached_tasks(cache_key, _query_tasks)

    def get_pending_tasks(self) -> List[Dict]:
        """Get all pending tasks (cached)"""
        return self.get_tasks(status='pending')

    def get_completed_tasks(self, limit: int = 50) -> List[Dict]:
        """Get completed tasks with limit"""
        return self.get_tasks(status='completed', limit=limit)

    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """Get a specific task by ID"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def complete_task(self, task_id: int) -> Dict:
        """Mark a task as complete with validation"""
        # Check if task exists and is pending
        task = self.get_task_by_id(task_id)
        if not task:
            return {
                'success': False,
                'message': f"Task {task_id} not found."
            }

        if task['status'] == 'completed':
            return {
                'success': False,
                'message': f"Task {task_id} is already completed."
            }

        try:
            success = self.db.update_task(
                task_id,
                status='completed',
                completed_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

            if success:
                self._invalidate_cache()  # Clear cache since task status changed
                self.db.log_activity('task_completed', f"Task ID: {task_id} - {task['title']}")
                return {
                    'success': True,
                    'message': f"Task '{task['title']}' marked as complete."
                }

            return {
                'success': False,
                'message': f"Failed to complete task {task_id}."
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Error completing task: {str(e)}"
            }

    def delete_task(self, task_id: int) -> Dict:
        """Delete a task with validation"""
        # Check if task exists
        task = self.get_task_by_id(task_id)
        if not task:
            return {
                'success': False,
                'message': f"Task {task_id} not found."
            }

        try:
            success = self.db.delete_task(task_id)
            if success:
                self._invalidate_cache()  # Clear cache since task was deleted
                self.db.log_activity('task_deleted', f"Task ID: {task_id} - {task['title']}")
                return {
                    'success': True,
                    'message': f"Task '{task['title']}' deleted."
                }

            return {
                'success': False,
                'message': f"Failed to delete task {task_id}."
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Error deleting task: {str(e)}"
            }

    def update_task(self, task_id: int, **kwargs) -> Dict:
        """Update a task with validation"""
        # Check if task exists
        task = self.get_task_by_id(task_id)
        if not task:
            return {
                'success': False,
                'message': f"Task {task_id} not found."
            }

        # Validate fields if they're being updated
        if 'title' in kwargs:
            is_valid, error_msg = self._validate_task_data(kwargs['title'], kwargs.get('priority', task['priority']), kwargs.get('due_date'))
            if not is_valid:
                return {
                    'success': False,
                    'message': error_msg
                }

        if 'priority' in kwargs and kwargs['priority'] not in ['low', 'medium', 'high', 'urgent']:
            return {
                'success': False,
                'message': "Invalid priority level"
            }

        if 'due_date' in kwargs and kwargs['due_date']:
            try:
                if ' ' in kwargs['due_date']:
                    datetime.strptime(kwargs['due_date'], '%Y-%m-%d %H:%M:%S')
                else:
                    datetime.strptime(kwargs['due_date'], '%Y-%m-%d')
            except ValueError:
                return {
                    'success': False,
                    'message': "Invalid date format"
                }

        try:
            success = self.db.update_task(task_id, **kwargs)
            if success:
                self._invalidate_cache()  # Clear cache since task was updated
                self.db.log_activity('task_updated', f"Task ID: {task_id}")
                return {
                    'success': True,
                    'message': f"Task {task_id} updated."
                }

            return {
                'success': False,
                'message': f"Failed to update task {task_id}."
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Error updating task: {str(e)}"
            }
    
    def get_upcoming_tasks(self, days: int = 7) -> List[Dict]:
        """Get tasks due in the next N days using optimized database query"""
        cache_key = f"upcoming_{days}"

        def _query_upcoming():
            today = datetime.now().date()
            cutoff = (today + timedelta(days=days)).strftime('%Y-%m-%d')

            cursor = self.db.conn.cursor()
            # Use database date functions for better performance
            cursor.execute("""
                SELECT * FROM tasks
                WHERE status = 'pending'
                AND due_date IS NOT NULL
                AND date(due_date) >= date('now')
                AND date(due_date) <= date(?)
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    due_date
            """, (cutoff,))

            return [dict(row) for row in cursor.fetchall()]

        return self._get_cached_tasks(cache_key, _query_upcoming)

    def get_overdue_tasks(self) -> List[Dict]:
        """Get tasks that are past their due date"""
        cache_key = "overdue"

        def _query_overdue():
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks
                WHERE status = 'pending'
                AND due_date IS NOT NULL
                AND date(due_date) < date('now')
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    due_date DESC
            """)

            return [dict(row) for row in cursor.fetchall()]

        return self._get_cached_tasks(cache_key, _query_overdue)

    def get_due_reminders(self) -> List[Dict]:
        """Get pending tasks that are due right now and haven't been reminded yet (optimized)"""
        # Get tasks due today or overdue
        all_pending = self.get_pending_tasks()
        now = datetime.now()
        due_now = []

        for task in all_pending:
            if not task['due_date'] or task['id'] in self.reminded_task_ids:
                continue

            try:
                # Accept both date and datetime formats
                fmt = '%Y-%m-%d %H:%M:%S' if ' ' in task['due_date'] else '%Y-%m-%d'
                due_dt = datetime.strptime(task['due_date'], fmt)

                # If we've passed the due date/time, it's due
                if due_dt <= now:
                    due_now.append(task)
                    self.reminded_task_ids.add(task['id'])
            except Exception:
                # Skip tasks with invalid dates
                continue

        return due_now

    def search_tasks(self, query: str, status: str = None) -> List[Dict]:
        """Search tasks by title or description using full-text search"""
        if not query or not query.strip():
            return []

        search_term = query.strip()
        cursor = self.db.conn.cursor()

        # Use FTS for better search results
        if status:
            cursor.execute("""
                SELECT t.* FROM tasks t
                JOIN tasks_fts fts ON t.id = fts.rowid
                WHERE tasks_fts MATCH ?
                AND t.status = ?
                ORDER BY
                    CASE t.priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    t.due_date
            """, (search_term, status))
        else:
            cursor.execute("""
                SELECT t.* FROM tasks t
                JOIN tasks_fts fts ON t.id = fts.rowid
                WHERE tasks_fts MATCH ?
                ORDER BY
                    CASE t.priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    t.due_date
            """, (search_term,))

        results = [dict(row) for row in cursor.fetchall()]

        # If FTS didn't find results, fall back to LIKE search
        if not results:
            return self._fallback_search(query, status)

        return results

    def _fallback_search(self, query: str, status: str = None) -> List[Dict]:
        """Fallback search using LIKE when FTS fails"""
        search_term = f"%{query.strip()}%"
        cursor = self.db.conn.cursor()

        if status:
            cursor.execute("""
                SELECT * FROM tasks
                WHERE (title LIKE ? OR description LIKE ?)
                AND status = ?
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    due_date
            """, (search_term, search_term, status))
        else:
            cursor.execute("""
                SELECT * FROM tasks
                WHERE title LIKE ? OR description LIKE ?
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    due_date
            """, (search_term, search_term))

        return [dict(row) for row in cursor.fetchall()]

    def get_task_statistics(self) -> Dict:
        """Get comprehensive task statistics"""
        cache_key = "stats"

        def _calculate_stats():
            cursor = self.db.conn.cursor()

            # Get counts by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM tasks
                GROUP BY status
            """)
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Get counts by priority
            cursor.execute("""
                SELECT priority, COUNT(*) as count
                FROM tasks
                WHERE status = 'pending'
                GROUP BY priority
            """)
            priority_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Get counts by category
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM tasks
                WHERE status = 'pending'
                GROUP BY category
            """)
            category_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Calculate completion rate (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT COUNT(*) as completed
                FROM tasks
                WHERE status = 'completed'
                AND completed_at >= ?
            """, (thirty_days_ago,))
            completed_30d = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) as total
                FROM tasks
                WHERE created_at >= ?
            """, (thirty_days_ago,))
            total_30d = cursor.fetchone()[0]

            completion_rate = (completed_30d / total_30d * 100) if total_30d > 0 else 0

            return {
                'total_tasks': sum(status_counts.values()),
                'pending_tasks': status_counts.get('pending', 0),
                'completed_tasks': status_counts.get('completed', 0),
                'overdue_tasks': len(self.get_overdue_tasks()),
                'upcoming_tasks': len(self.get_upcoming_tasks(7)),
                'priority_breakdown': priority_counts,
                'category_breakdown': category_counts,
                'completion_rate_30d': round(completion_rate, 1)
            }

        return self._get_cached_tasks(cache_key, _calculate_stats)

    def bulk_complete_tasks(self, task_ids: List[int]) -> Dict:
        """Complete multiple tasks at once"""
        if not task_ids:
            return {'success': False, 'message': 'No task IDs provided'}

        completed = 0
        failed = 0
        errors = []

        for task_id in task_ids:
            result = self.complete_task(task_id)
            if result['success']:
                completed += 1
            else:
                failed += 1
                errors.append(f"Task {task_id}: {result['message']}")

        message = f"Bulk completion: {completed} completed"
        if failed > 0:
            message += f", {failed} failed"

        return {
            'success': completed > 0,
            'message': message,
            'completed_count': completed,
            'failed_count': failed,
            'errors': errors
        }

    def bulk_delete_tasks(self, task_ids: List[int]) -> Dict:
        """Delete multiple tasks at once"""
        if not task_ids:
            return {'success': False, 'message': 'No task IDs provided'}

        deleted = 0
        failed = 0
        errors = []

        for task_id in task_ids:
            result = self.delete_task(task_id)
            if result['success']:
                deleted += 1
            else:
                failed += 1
                errors.append(f"Task {task_id}: {result['message']}")

        message = f"Bulk deletion: {deleted} deleted"
        if failed > 0:
            message += f", {failed} failed"

        return {
            'success': deleted > 0,
            'message': message,
            'deleted_count': deleted,
            'failed_count': failed,
            'errors': errors
        }

    def get_categories(self) -> List[str]:
        """Get all unique task categories"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM tasks ORDER BY category")
        return [row[0] for row in cursor.fetchall()]

    def clear_completed_tasks(self, days_old: int = None) -> Dict:
        """Clear old completed tasks"""
        cursor = self.db.conn.cursor()

        if days_old:
            cutoff_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d')
            cursor.execute("""
                DELETE FROM tasks
                WHERE status = 'completed'
                AND completed_at < ?
            """, (cutoff_date,))
        else:
            cursor.execute("DELETE FROM tasks WHERE status = 'completed'")

        deleted_count = cursor.rowcount
        self.db.conn.commit()

        if deleted_count > 0:
            self._invalidate_cache()
            self.db.log_activity('bulk_task_deletion', f"Cleared {deleted_count} completed tasks")

        return {
            'success': True,
            'message': f"Cleared {deleted_count} completed tasks",
            'deleted_count': deleted_count
        }
