"""
Habit Management Module for MILO
Handles habit tracking and analytics
"""

from typing import List, Dict
from datetime import datetime
import time
from database.database import Database


class HabitManager:
    """Manages habits and habit tracking"""
    
    def __init__(self, database: Database):
        """Initialize habit manager with database"""
        self.db = database
        self._cache: Dict[str, object] = {}
        self._cache_timeout = 300  # 5 minutes
        self._last_cache_update = 0.0
        self._reminded_today = set()
    
    def _invalidate_cache(self):
        """Invalidate habit cache"""
        self._cache.clear()
        self._last_cache_update = 0.0

    def _normalize_time(self, time_str: str) -> str:
        """Normalize time string to HH:MM format"""
        try:
            parsed = datetime.strptime(time_str.strip(), "%H:%M")
            return parsed.strftime("%H:%M")
        except Exception:
            return "20:00"
    
    def _get_cached_data(self, cache_key: str, query_func, *args, **kwargs):
        """Get data from cache or execute query"""
        now = time.time()
        if now - self._last_cache_update > self._cache_timeout:
            self._invalidate_cache()
        
        if cache_key not in self._cache:
            self._cache[cache_key] = query_func(*args, **kwargs)
            self._last_cache_update = now
        
        return self._cache[cache_key]
    
    def _has_logged_today(self, habit_id: int) -> bool:
        """Check if habit already logged today"""
        today = datetime.now().strftime('%Y-%m-%d')
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM habit_logs WHERE habit_id = ? AND date = ? LIMIT 1",
            (habit_id, today)
        )
        return cursor.fetchone() is not None

    def get_logged_today_ids(self, habit_ids: List[int]) -> set:
        """Get set of habit IDs already logged today (bulk)"""
        if not habit_ids:
            return set()

        today = datetime.now().strftime('%Y-%m-%d')
        placeholders = ",".join(["?"] * len(habit_ids))
        query = f"SELECT habit_id FROM habit_logs WHERE date = ? AND habit_id IN ({placeholders})"
        cursor = self.db.conn.cursor()
        cursor.execute(query, [today, *habit_ids])
        return {row[0] for row in cursor.fetchall()}

    def get_due_habit_reminders(self) -> List[Dict]:
        """Return habits that should be reminded now (not logged today)"""
        try:
            now = datetime.now()
            today_key = now.strftime('%Y-%m-%d')
            habits = self.get_habits()
            habit_ids = [h.get('id') for h in habits if h.get('id') is not None]
            logged_today = self.get_logged_today_ids(habit_ids)

            due = []
            for habit in habits:
                habit_id = habit.get('id')
                reminder_time = habit.get('reminder_time') or "20:00"
                reminder_time = self._normalize_time(reminder_time)

                try:
                    reminder_dt = datetime.strptime(reminder_time, "%H:%M").time()
                except Exception:
                    reminder_dt = datetime.strptime("20:00", "%H:%M").time()

                if habit_id in logged_today:
                    continue

                reminder_key = f"{today_key}:{habit_id}"
                if reminder_key in self._reminded_today:
                    continue

                if now.time() >= reminder_dt:
                    due.append(habit)
                    self._reminded_today.add(reminder_key)

            return due
        except Exception:
            return []
    
    def add_habit(self, name: str, description: str = "", target_frequency: str = "daily", reminder_time: str = "20:00") -> Dict:
        """Add a new habit"""
        reminder_time = self._normalize_time(reminder_time)
        habit_id = self.db.add_habit(name, description, target_frequency, reminder_time)
        self._invalidate_cache()
        self.db.log_activity('habit_created', f"Habit: {name}")
        return {
            'success': True,
            'message': f"Habit '{name}' added.",
            'habit_id': habit_id
        }
    
    def get_habits(self) -> List[Dict]:
        """Get all habits"""
        return self._get_cached_data("habits", self.db.get_habits)
    
    def log_habit(self, habit_id: int, notes: str = "") -> Dict:
        """Compatibility wrapper for logging a habit completion"""
        return self.log_habit_completion(habit_id, notes)
    
    def log_habit_completion(self, habit_id: int, notes: str = "") -> Dict:
        """Log habit completion for today"""
        if self._has_logged_today(habit_id):
            return {
                'success': False,
                'message': "Habit already logged today."
            }
        
        today = datetime.now().strftime('%Y-%m-%d')
        log_id = self.db.log_habit(habit_id, today, notes)
        self._invalidate_cache()
        self.db.log_activity('habit_logged', f"Habit ID: {habit_id}")
        return {
            'success': True,
            'message': "Habit logged successfully.",
            'log_id': log_id
        }
    
    def get_habit_stats(self, habit_id: int, days: int = 30) -> Dict:
        """Get habit statistics"""
        cache_key = f"habit_stats_{habit_id}_{days}"
        stats = self._get_cached_data(cache_key, self.db.get_habit_stats, habit_id, days)
        
        # Calculate completion rate
        completion_rate = (stats['completed_count'] / days * 100) if days > 0 else 0
        
        return {
            **stats,
            'completion_rate': round(completion_rate, 2)
        }
    
    def get_all_habit_stats(self) -> List[Dict]:
        """Get statistics for all habits"""
        habits = self.get_habits()
        result = []
        
        for habit in habits:
            stats = self.get_habit_stats(habit['id'])
            result.append({
                **habit,
                **stats
            })
        
        return result
    
    def analyze_patterns(self) -> Dict:
        """Analyze user activity patterns for optimized AI insights"""
        now = datetime.now()
        hour = now.hour
        
        # 1. Fetch relevant data
        pending_tasks = self.db.get_tasks(status='pending')
        high_priority = [t for t in pending_tasks if t.get('priority') == 'high']
        balance = self.db.get_balance()
        habit_stats = self.get_all_habit_stats()
        habits = self.get_habits()
        
        suggestions = []
        
        # 2. Time-aware suggestions
        if 5 <= hour < 10:
            suggestions.append("Morning focus: pick your top task and finish it first for quick momentum.")
        elif 12 <= hour < 15:
            suggestions.append("Midday check-in: review your tasks and log a habit to stay on track.")
        elif 21 <= hour or hour < 5:
            suggestions.append("Evening wrap-up: log today’s habits and set one task for tomorrow.")
            
        # 3. Task-based insights
        if len(high_priority) > 3:
            suggestions.append(f"You have {len(high_priority)} high-priority tasks. Tackle the smallest one to build momentum.")
        elif len(pending_tasks) > 10:
            suggestions.append("Your task list is growing. Use a quick sweep: complete any task under 2 minutes.")
        elif len(pending_tasks) == 0:
            suggestions.append("Nice! No pending tasks. Invest 10 minutes in a habit or plan tomorrow.")

        # 4. Finance-based insights
        if balance < 0:
            suggestions.append("Your balance is negative. Review recent expenses and pause non-essentials this week.")
        elif balance < 100:
            suggestions.append("Your balance is low. Set a small daily spend limit to stabilize cash flow.")
            
        # 5. Habit-based insights
        low_habit = next((h for h in habit_stats if h.get('completion_rate', 100) < 50), None)
        if low_habit:
            suggestions.append(f"Your habit '{low_habit['name']}' needs focus. Shrink it to a 2-minute version today.")
        elif habit_stats and all(h.get('completion_rate', 0) > 80 for h in habit_stats):
            suggestions.append("Great consistency! Consider stacking a new habit onto an existing routine.")

        # Streak-based insights (estimate using recent logs)
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            if habits:
                habit_ids = [h.get('id') for h in habits if h.get('id') is not None]
                placeholders = ",".join(["?"] * len(habit_ids))
                query = f"SELECT habit_id, date FROM habit_logs WHERE habit_id IN ({placeholders}) ORDER BY date DESC"
                cursor = self.db.conn.cursor()
                cursor.execute(query, habit_ids)
                logs = cursor.fetchall()

                # Build recent streak counts (simple: consecutive days from today)
                streaks = {hid: 0 for hid in habit_ids}
                seen_dates = {hid: set() for hid in habit_ids}
                for row in logs:
                    hid = row[0]
                    log_date = row[1]
                    seen_dates[hid].add(log_date)

                for hid in habit_ids:
                    streak = 0
                    check_day = datetime.now()
                    while True:
                        day_str = check_day.strftime('%Y-%m-%d')
                        if day_str in seen_dates[hid]:
                            streak += 1
                            check_day = check_day.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
                        else:
                            break
                    streaks[hid] = streak

                # Pick best streak
                best_habit_id = max(streaks, key=streaks.get) if streaks else None
                best_streak = streaks.get(best_habit_id, 0) if best_habit_id else 0
                if best_streak >= 3 and best_habit_id is not None:
                    best_habit = next((h for h in habits if h.get('id') == best_habit_id), None)
                    if best_habit:
                        suggestions.append(
                            f"Streak win: '{best_habit['name']}' is {best_streak} days strong. Keep it going tomorrow."
                        )
                elif best_streak == 0 and habits:
                    suggestions.append("No streaks yet. Start with a single habit today to begin a streak.")
        except Exception:
            pass

        # 6. Activity Count fallback
        task_activities = self.db.get_activity_patterns('task_created', days=7)
        if len(task_activities) > 15:
            suggestions.append("You created many tasks this week. Schedule a 15-minute cleanup to prioritize.")

        # Category-specific finance tips (based on top expense category)
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM finances
                WHERE transaction_type = 'expense'
                AND date >= date('now', '-30 days')
                GROUP BY category
                ORDER BY total DESC
                LIMIT 1
            """)
            top_row = cursor.fetchone()
            if top_row:
                top_cat = top_row[0]
                top_total = top_row[1] or 0
                if top_total > 0:
                    if str(top_cat).lower() in ['food', 'groceries']:
                        suggestions.append("Top spend is Food. Try meal planning 2 days this week to cut costs.")
                    elif str(top_cat).lower() in ['transport', 'fuel']:
                        suggestions.append("Transport is your top expense. Batch errands to reduce trips.")
                    elif str(top_cat).lower() in ['entertainment']:
                        suggestions.append("Entertainment is highest. Set a weekly fun budget to stay on track.")
                    elif str(top_cat).lower() in ['utilities']:
                        suggestions.append("Utilities lead expenses. Check for small savings like AC timers or LED bulbs.")
                    else:
                        suggestions.append(f"Your top expense is {top_cat}. Set a simple monthly cap for it.")
        except Exception:
            pass

        # Final cleanup: ensure we always have at least 2 suggestions
        if len(suggestions) < 2:
            suggestions.append("Consistency is key. Log at least one habit today for better insights.")
            suggestions.append("Check your dashboard once a day to keep priorities clear.")
            
        return {
            'suggestions': suggestions[:5], # Return top 5 most relevant
            'task_activity_count': len(task_activities),
            'high_priority_count': len(high_priority)
        }
