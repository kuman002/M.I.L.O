"""
Finance Management Module for MILO
Handles financial tracking and budget management with optimized performance
"""

from typing import List, Dict, Tuple, Optional
from database.database import Database
from datetime import datetime, timedelta
import re


class FinanceManager:
    """Manages finances and expenses with optimized performance"""

    def __init__(self, database: Database):
        """Initialize finance manager with database"""
        self.db = database
        self._cache = {}  # Cache for frequently accessed data
        self._cache_timeout = 300  # 5 minutes cache timeout
        self._last_cache_update = 0

    def _invalidate_cache(self):
        """Invalidate the finance cache"""
        self._cache.clear()
        self._last_cache_update = 0

    def _get_cached_data(self, cache_key: str, query_func, *args, **kwargs):
        """Get data from cache or execute query"""
        current_time = datetime.now().timestamp()

        # Check if cache is stale
        if current_time - self._last_cache_update > self._cache_timeout:
            self._invalidate_cache()

        if cache_key not in self._cache:
            self._cache[cache_key] = query_func(*args, **kwargs)
            self._last_cache_update = current_time

        return self._cache[cache_key]

    def _validate_amount(self, amount: float, min_amount: float = 0.01) -> Tuple[bool, str]:
        """Validate transaction amount"""
        try:
            amount = float(amount)
            if amount < min_amount:
                return False, f"Amount must be at least {min_amount}"
            if amount > 999999999.99:
                return False, "Amount exceeds maximum limit"
            return True, ""
        except (ValueError, TypeError):
            return False, "Invalid amount format"

    def _validate_category(self, category: str) -> Tuple[bool, str]:
        """Validate transaction category"""
        if not category or not category.strip():
            return False, "Category cannot be empty"
        
        category = category.strip()
        if len(category) > 50:
            return False, "Category name too long (max 50 characters)"
        
        # Only allow alphanumeric, spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', category):
            return False, "Category contains invalid characters"
        
        return True, ""

    def _validate_description(self, description: str) -> str:
        """Validate and sanitize description"""
        if not description:
            return ""
        return description.strip()[:500]  # Max 500 characters

    def add_expense(self, category: str, amount: float, description: str = "") -> Dict:
        """Add an expense with validation"""
        # Validate amount
        is_valid, error_msg = self._validate_amount(amount)
        if not is_valid:
            return {'success': False, 'message': error_msg}

        # Validate category
        is_valid, error_msg = self._validate_category(category)
        if not is_valid:
            return {'success': False, 'message': error_msg}

        # Validate description
        description = self._validate_description(description)

        try:
            transaction_id = self.db.add_transaction('expense', category.strip(), amount, description)
            self._invalidate_cache()  # Clear cache since we added a transaction
            self.db.log_activity('expense_added', f"{category}: {amount}")
            return {
                'success': True,
                'message': f"Expense of ${amount:.2f} added to {category}.",
                'transaction_id': transaction_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to add expense: {str(e)}"
            }

    def add_income(self, category: str, amount: float, description: str = "") -> Dict:
        """Add income with validation"""
        # Validate amount
        is_valid, error_msg = self._validate_amount(amount)
        if not is_valid:
            return {'success': False, 'message': error_msg}

        # Validate category
        is_valid, error_msg = self._validate_category(category)
        if not is_valid:
            return {'success': False, 'message': error_msg}

        # Validate description
        description = self._validate_description(description)

        try:
            transaction_id = self.db.add_transaction('income', category.strip(), amount, description)
            self._invalidate_cache()  # Clear cache since we added a transaction
            self.db.log_activity('income_added', f"{category}: {amount}")
            return {
                'success': True,
                'message': f"Income of ${amount:.2f} added to {category}.",
                'transaction_id': transaction_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to add income: {str(e)}"
            }

    def get_balance(self) -> float:
        """Get current balance (cached)"""
        cache_key = "balance"
        return self._get_cached_data(cache_key, self.db.get_balance)

    def get_transactions(self, limit: int = 50, transaction_type: str = None,
                        category: str = None) -> List[Dict]:
        """Get transactions with filtering and caching"""
        cache_key = f"transactions_{limit}_{transaction_type}_{category}"

        def _query_transactions():
            cursor = self.db.conn.cursor()
            
            conditions = []
            params = []

            if transaction_type:
                conditions.append("transaction_type = ?")
                params.append(transaction_type)

            if category:
                conditions.append("category = ?")
                params.append(category)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM finances WHERE {where_clause} ORDER BY date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

        return self._get_cached_data(cache_key, _query_transactions)

    def get_expenses_by_category(self, limit: int = None) -> List[Tuple[str, float]]:
        """Get expenses grouped by category (cached and optimized)"""
        cache_key = f"expenses_by_category_{limit}"

        def _query_expenses():
            cursor = self.db.conn.cursor()
            query = """
                SELECT category, SUM(amount) as total
                FROM finances
                WHERE transaction_type = 'expense'
                GROUP BY category
                ORDER BY total DESC
            """
            
            if limit:
                query += " LIMIT ?"
                cursor.execute(query, (limit,))
            else:
                cursor.execute(query)

            return cursor.fetchall()

        return self._get_cached_data(cache_key, _query_expenses)

    def get_income_by_category(self, limit: int = None) -> List[Tuple[str, float]]:
        """Get income grouped by category (optimized)"""
        cache_key = f"income_by_category_{limit}"

        def _query_income():
            cursor = self.db.conn.cursor()
            query = """
                SELECT category, SUM(amount) as total
                FROM finances
                WHERE transaction_type = 'income'
                GROUP BY category
                ORDER BY total DESC
            """
            
            if limit:
                query += " LIMIT ?"
                cursor.execute(query, (limit,))
            else:
                cursor.execute(query)

            return cursor.fetchall()

        return self._get_cached_data(cache_key, _query_income)

    def get_summary(self, days: int = 30) -> Dict:
        """Get comprehensive financial summary"""
        cache_key = f"summary_{days}"

        def _calculate_summary():
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            cursor = self.db.conn.cursor()

            # Get period statistics
            cursor.execute("""
                SELECT
                    transaction_type,
                    COUNT(*) as count,
                    SUM(amount) as total
                FROM finances
                WHERE date >= ?
                GROUP BY transaction_type
            """, (cutoff_date,))

            stats_by_type = {row[0]: {'count': row[1], 'total': row[2]} for row in cursor.fetchall()}

            income_stats = stats_by_type.get('income', {'count': 0, 'total': 0})
            expense_stats = stats_by_type.get('expense', {'count': 0, 'total': 0})

            total_income = income_stats['total'] or 0
            total_expenses = expense_stats['total'] or 0
            net = total_income - total_expenses

            # Get breakdown by category
            cursor.execute("""
                SELECT
                    category,
                    transaction_type,
                    SUM(amount) as total,
                    COUNT(*) as count
                FROM finances
                WHERE date >= ?
                GROUP BY category, transaction_type
                ORDER BY transaction_type, total DESC
            """, (cutoff_date,))

            category_breakdown = {}
            for row in cursor.fetchall():
                cat, trans_type, total, count = row
                if cat not in category_breakdown:
                    category_breakdown[cat] = {}
                category_breakdown[cat][trans_type] = {'total': total, 'count': count}

            # Get top spending categories
            cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM finances
                WHERE date >= ? AND transaction_type = 'expense'
                GROUP BY category
                ORDER BY total DESC
                LIMIT 5
            """, (cutoff_date,))
            top_spending = cursor.fetchall()

            return {
                'period_days': days,
                'balance': self.db.get_balance(),
                'total_income': total_income,
                'income_count': income_stats['count'],
                'total_expenses': total_expenses,
                'expense_count': expense_stats['count'],
                'net_change': net,
                'savings_rate': (net / total_income * 100) if total_income > 0 else 0,
                'category_breakdown': category_breakdown,
                'top_spending_categories': top_spending,
                'avg_expense': (total_expenses / expense_stats['count']) if expense_stats['count'] > 0 else 0,
                'avg_income': (total_income / income_stats['count']) if income_stats['count'] > 0 else 0
            }

        return self._get_cached_data(cache_key, _calculate_summary)

    def search_transactions(self, query: str, transaction_type: str = None) -> List[Dict]:
        """Search transactions by description"""
        if not query or not query.strip():
            return []

        search_term = f"%{query.strip()}%"
        cursor = self.db.conn.cursor()

        if transaction_type:
            cursor.execute("""
                SELECT * FROM finances
                WHERE (description LIKE ? OR category LIKE ?)
                AND transaction_type = ?
                ORDER BY date DESC
            """, (search_term, search_term, transaction_type))
        else:
            cursor.execute("""
                SELECT * FROM finances
                WHERE description LIKE ? OR category LIKE ?
                ORDER BY date DESC
            """, (search_term, search_term))

        return [dict(row) for row in cursor.fetchall()]

    def get_monthly_summary(self, year: int = None, month: int = None) -> Dict:
        """Get summary for specific month"""
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month

        cache_key = f"monthly_{year}_{month}"

        def _calculate_monthly():
            cursor = self.db.conn.cursor()

            # Get date range for the month
            month_start = f"{year}-{month:02d}-01"
            if month == 12:
                month_end = f"{year + 1}-01-01"
            else:
                month_end = f"{year}-{month + 1:02d}-01"

            cursor.execute("""
                SELECT
                    transaction_type,
                    COUNT(*) as count,
                    SUM(amount) as total
                FROM finances
                WHERE date >= ? AND date < ?
                GROUP BY transaction_type
            """, (month_start, month_end))

            stats_by_type = {row[0]: {'count': row[1], 'total': row[2]} for row in cursor.fetchall()}

            income_stats = stats_by_type.get('income', {'count': 0, 'total': 0})
            expense_stats = stats_by_type.get('expense', {'count': 0, 'total': 0})

            total_income = income_stats['total'] or 0
            total_expenses = expense_stats['total'] or 0

            # Get daily breakdown
            cursor.execute("""
                SELECT
                    DATE(date) as day,
                    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expense
                FROM finances
                WHERE date >= ? AND date < ?
                GROUP BY DATE(date)
                ORDER BY day
            """, (month_start, month_end))

            daily_breakdown = [{'date': row[0], 'income': row[1] or 0, 'expense': row[2] or 0} for row in cursor.fetchall()]

            return {
                'year': year,
                'month': month,
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net': total_income - total_expenses,
                'income_count': income_stats['count'],
                'expense_count': expense_stats['count'],
                'daily_breakdown': daily_breakdown,
                'expenses_by_category': dict(self.get_expenses_by_category())
            }

        return self._get_cached_data(cache_key, _calculate_monthly)

    def get_budget_status(self, category_budgets: Dict[str, float]) -> Dict:
        """Check spending against budget limits"""
        cache_key = f"budget_status_{str(sorted(category_budgets.items()))}"

        def _check_budgets():
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            cursor = self.db.conn.cursor()

            budget_status = {}

            for category, budget_limit in category_budgets.items():
                cursor.execute("""
                    SELECT SUM(amount) as total
                    FROM finances
                    WHERE category = ?
                    AND transaction_type = 'expense'
                    AND date >= ?
                """, (category, thirty_days_ago))

                result = cursor.fetchone()
                spent = result[0] or 0

                percentage = (spent / budget_limit * 100) if budget_limit > 0 else 0

                budget_status[category] = {
                    'budget_limit': budget_limit,
                    'spent': spent,
                    'remaining': budget_limit - spent,
                    'percentage': round(percentage, 1),
                    'status': 'over' if spent > budget_limit else 'warning' if percentage > 80 else 'ok'
                }

            return budget_status

        return self._get_cached_data(cache_key, _check_budgets)

    def bulk_add_transactions(self, transactions: List[Dict]) -> Dict:
        """Add multiple transactions at once"""
        if not transactions:
            return {'success': False, 'message': 'No transactions provided'}

        added = 0
        failed = 0
        errors = []

        for trans in transactions:
            trans_type = trans.get('type', 'expense')
            category = trans.get('category')
            amount = trans.get('amount')
            description = trans.get('description', '')

            if trans_type == 'expense':
                result = self.add_expense(category, amount, description)
            elif trans_type == 'income':
                result = self.add_income(category, amount, description)
            else:
                result = {'success': False, 'message': 'Invalid transaction type'}

            if result['success']:
                added += 1
            else:
                failed += 1
                errors.append(f"{category}: {result['message']}")

        return {
            'success': added > 0,
            'added_count': added,
            'failed_count': failed,
            'errors': errors
        }

    def get_spending_trends(self, days: int = 90) -> Dict:
        """Analyze spending trends over time"""
        cache_key = f"trends_{days}"

        def _calculate_trends():
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            cursor = self.db.conn.cursor()

            # Weekly breakdown
            cursor.execute("""
                SELECT
                    strftime('%Y-W%W', date) as week,
                    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expense
                FROM finances
                WHERE date >= ?
                GROUP BY week
                ORDER BY week
            """, (cutoff_date,))

            weekly_data = [
                {'week': row[0], 'income': row[1] or 0, 'expense': row[2] or 0}
                for row in cursor.fetchall()
            ]

            # Calculate trend (is spending increasing or decreasing)
            if len(weekly_data) > 1:
                first_week_expense = weekly_data[0]['expense']
                last_week_expense = weekly_data[-1]['expense']
                trend = 'increasing' if last_week_expense > first_week_expense else 'decreasing'
                change_percent = ((last_week_expense - first_week_expense) / first_week_expense * 100) if first_week_expense > 0 else 0
            else:
                trend = 'stable'
                change_percent = 0

            return {
                'period_days': days,
                'weekly_breakdown': weekly_data,
                'trend': trend,
                'trend_change_percent': round(change_percent, 1),
                'total_weeks': len(weekly_data)
            }

        return self._get_cached_data(cache_key, _calculate_trends)

    def get_categories(self) -> List[str]:
        """Get all unique transaction categories"""
        cache_key = "categories"

        def _fetch_categories():
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM finances ORDER BY category")
            return [row[0] for row in cursor.fetchall()]

        return self._get_cached_data(cache_key, _fetch_categories)
