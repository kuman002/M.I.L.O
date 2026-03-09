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

    def _decrypt_transaction(self, trans: Dict) -> Dict:
        """Decrypt encrypted transaction fields when present"""
        if not trans:
            return trans
        trans["transaction_type"] = self.db.decrypt_text(trans.get("transaction_type"))
        trans["category"] = self.db.decrypt_text(trans.get("category"))
        trans["description"] = self.db.decrypt_text(trans.get("description"))
        amount = trans.get("amount")
        try:
            trans["amount"] = float(amount)
        except (TypeError, ValueError):
            trans["amount"] = 0.0
        return trans

    def _in_date_range(self, date_str: str, start: str = None, end: str = None) -> bool:
        if not date_str:
            return False
        date_only = date_str[:10]
        if start and date_only < start:
            return False
        if end and date_only >= end:
            return False
        return True

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
            transactions = self.db.get_all_transactions()

            filtered = []
            for trans in transactions:
                trans = self._decrypt_transaction(trans)
                if transaction_type and (trans.get("transaction_type") or "").lower() != transaction_type.lower():
                    continue
                if category and (trans.get("category") or "").lower() != category.lower():
                    continue
                filtered.append(trans)

            return filtered[:limit]

        return self._get_cached_data(cache_key, _query_transactions)

    def get_expenses_by_category(self, limit: int = None) -> List[Tuple[str, float]]:
        """Get expenses grouped by category (cached and optimized)"""
        cache_key = f"expenses_by_category_{limit}"

        def _query_expenses():
            totals = {}
            for trans in self.db.get_all_transactions():
                trans = self._decrypt_transaction(trans)
                if (trans.get("transaction_type") or "").lower() != "expense":
                    continue
                category = trans.get("category") or "Other"
                totals[category] = totals.get(category, 0.0) + float(trans.get("amount") or 0)

            result = sorted(totals.items(), key=lambda x: x[1], reverse=True)
            return result[:limit] if limit else result

        return self._get_cached_data(cache_key, _query_expenses)

    def get_income_by_category(self, limit: int = None) -> List[Tuple[str, float]]:
        """Get income grouped by category (optimized)"""
        cache_key = f"income_by_category_{limit}"

        def _query_income():
            totals = {}
            for trans in self.db.get_all_transactions():
                trans = self._decrypt_transaction(trans)
                if (trans.get("transaction_type") or "").lower() != "income":
                    continue
                category = trans.get("category") or "Other"
                totals[category] = totals.get(category, 0.0) + float(trans.get("amount") or 0)

            result = sorted(totals.items(), key=lambda x: x[1], reverse=True)
            return result[:limit] if limit else result

        return self._get_cached_data(cache_key, _query_income)

    def get_summary(self, days: int = 30) -> Dict:
        """Get comprehensive financial summary"""
        cache_key = f"summary_{days}"

        def _calculate_summary():
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            total_income = 0.0
            total_expenses = 0.0
            income_count = 0
            expense_count = 0
            category_breakdown = {}
            top_spending_map = {}

            for trans in self.db.get_all_transactions():
                trans = self._decrypt_transaction(trans)
                if not self._in_date_range(trans.get("date", ""), start=cutoff_date):
                    continue
                trans_type = (trans.get("transaction_type") or "").lower()
                category = trans.get("category") or "Other"
                amount = float(trans.get("amount") or 0)

                category_breakdown.setdefault(category, {})
                stats = category_breakdown[category].setdefault(trans_type, {'total': 0.0, 'count': 0})
                stats['total'] += amount
                stats['count'] += 1

                if trans_type == "income":
                    total_income += amount
                    income_count += 1
                elif trans_type == "expense":
                    total_expenses += amount
                    expense_count += 1
                    top_spending_map[category] = top_spending_map.get(category, 0.0) + amount

            top_spending = sorted(top_spending_map.items(), key=lambda x: x[1], reverse=True)[:5]
            net = total_income - total_expenses

            return {
                'period_days': days,
                'balance': self.db.get_balance(),
                'total_income': total_income,
                'income_count': income_count,
                'total_expenses': total_expenses,
                'expense_count': expense_count,
                'net_change': net,
                'savings_rate': (net / total_income * 100) if total_income > 0 else 0,
                'category_breakdown': category_breakdown,
                'top_spending_categories': top_spending,
                'avg_expense': (total_expenses / expense_count) if expense_count > 0 else 0,
                'avg_income': (total_income / income_count) if income_count > 0 else 0
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
                WHERE transaction_type = ?
                ORDER BY date DESC
            """, (transaction_type,))
        else:
            cursor.execute("""
                SELECT * FROM finances
                ORDER BY date DESC
            """)

        query_lower = query.strip().lower()
        results = []
        for row in cursor.fetchall():
            trans = self._decrypt_transaction(dict(row))
            description = (trans.get("description") or "").lower()
            category = (trans.get("category") or "").lower()
            if query_lower in description or query_lower in category:
                results.append(trans)

        return results

    def get_monthly_summary(self, year: int = None, month: int = None) -> Dict:
        """Get summary for specific month"""
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month

        cache_key = f"monthly_{year}_{month}"

        def _calculate_monthly():
            # Get date range for the month
            month_start = f"{year}-{month:02d}-01"
            if month == 12:
                month_end = f"{year + 1}-01-01"
            else:
                month_end = f"{year}-{month + 1:02d}-01"

            total_income = 0.0
            total_expenses = 0.0
            income_count = 0
            expense_count = 0
            daily_map = {}

            for trans in self.db.get_all_transactions():
                trans = self._decrypt_transaction(trans)
                if not self._in_date_range(trans.get("date", ""), start=month_start, end=month_end):
                    continue

                date_only = (trans.get("date") or "")[:10]
                daily_map.setdefault(date_only, {"date": date_only, "income": 0.0, "expense": 0.0})

                trans_type = (trans.get("transaction_type") or "").lower()
                amount = float(trans.get("amount") or 0)

                if trans_type == "income":
                    total_income += amount
                    income_count += 1
                    daily_map[date_only]["income"] += amount
                elif trans_type == "expense":
                    total_expenses += amount
                    expense_count += 1
                    daily_map[date_only]["expense"] += amount

            daily_breakdown = [daily_map[key] for key in sorted(daily_map.keys())]

            return {
                'year': year,
                'month': month,
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net': total_income - total_expenses,
                'income_count': income_count,
                'expense_count': expense_count,
                'daily_breakdown': daily_breakdown,
                'expenses_by_category': dict(self.get_expenses_by_category())
            }

        return self._get_cached_data(cache_key, _calculate_monthly)

    def get_budget_status(self, category_budgets: Dict[str, float]) -> Dict:
        """Check spending against budget limits"""
        cache_key = f"budget_status_{str(sorted(category_budgets.items()))}"

        def _check_budgets():
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            budget_status = {}

            for category, budget_limit in category_budgets.items():
                spent = 0.0
                for trans in self.db.get_all_transactions():
                    trans = self._decrypt_transaction(trans)
                    if not self._in_date_range(trans.get("date", ""), start=thirty_days_ago):
                        continue
                    if (trans.get("transaction_type") or "").lower() != "expense":
                        continue
                    if (trans.get("category") or "").lower() != category.lower():
                        continue
                    spent += float(trans.get("amount") or 0)

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

            weekly_map = {}
            for trans in self.db.get_all_transactions():
                trans = self._decrypt_transaction(trans)
                if not self._in_date_range(trans.get("date", ""), start=cutoff_date):
                    continue

                date_str = trans.get("date") or ""
                dt = None
                try:
                    dt = datetime.fromisoformat(date_str)
                except ValueError:
                    try:
                        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    except ValueError:
                        dt = None

                if not dt:
                    continue

                week_key = dt.strftime("%Y-W%W")
                weekly_map.setdefault(week_key, {"week": week_key, "income": 0.0, "expense": 0.0})

                trans_type = (trans.get("transaction_type") or "").lower()
                amount = float(trans.get("amount") or 0)

                if trans_type == "income":
                    weekly_map[week_key]["income"] += amount
                elif trans_type == "expense":
                    weekly_map[week_key]["expense"] += amount

            weekly_data = [weekly_map[key] for key in sorted(weekly_map.keys())]

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
            categories = set()
            for trans in self.db.get_all_transactions():
                trans = self._decrypt_transaction(trans)
                category = trans.get("category")
                if category:
                    categories.add(category)
            return sorted(categories)

        return self._get_cached_data(cache_key, _fetch_categories)
