"""
Finances Tab for MILO
Financial tracking and budgeting
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QHeaderView
)
from PyQt5.QtGui import QFont, QColor
from gui.base_tab import BaseTab
from gui.dashboards import FinanceDashboardChart, ExpenseByCategoryChart, BudgetStatusChart


class FinancesTab(BaseTab):
    """Financial tracking tab"""
    
    def setup_ui(self):
        """Build the finances UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Add transaction section
        add_layout = QHBoxLayout()
        
        self.trans_type = QComboBox()
        self.trans_type.addItems(["Income", "Expense"])
        add_layout.addWidget(QLabel("Type:"))
        add_layout.addWidget(self.trans_type)
        
        self.trans_amount = QLineEdit()
        self.trans_amount.setPlaceholderText("Amount...")
        add_layout.addWidget(QLabel("Amount:"))
        add_layout.addWidget(self.trans_amount)
        
        self.trans_category = QComboBox()
        self.trans_category.addItems(["Food", "Transport", "Entertainment", "Utilities", "Other"])
        add_layout.addWidget(QLabel("Category:"))
        add_layout.addWidget(self.trans_category)
        
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self.add_transaction)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        # Main content layout - Charts on left, Table on right
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left side - Charts (vertical layout)
        charts_container = QVBoxLayout()
        charts_container.setSpacing(15)
        
        # Chart row 1 - Income vs Expenses and Expenses by Category
        charts_layout1 = QHBoxLayout()
        charts_layout1.setSpacing(15)
        
        self.finance_chart = FinanceDashboardChart()
        self.expense_category_chart = ExpenseByCategoryChart()
        
        charts_layout1.addWidget(self.finance_chart, 1)
        charts_layout1.addWidget(self.expense_category_chart, 1)
        
        charts_container.addLayout(charts_layout1)
        
        # Chart row 2 - Budget Status
        self.budget_chart = BudgetStatusChart()
        charts_container.addWidget(self.budget_chart)
        
        content_layout.addLayout(charts_container, 2)  # Charts take 2/3 of width
        
        # Right side - Transactions table
        table_container = QVBoxLayout()
        table_container.setSpacing(10)
        
        table_label = QLabel("Recent Transactions")
        table_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        table_container.addWidget(table_label)
        
        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(5)
        self.trans_table.setHorizontalHeaderLabels(["Type", "Amount", "Category", "Date", "Delete"])
        self.trans_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.trans_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.trans_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.trans_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.trans_table.setAlternatingRowColors(True)
        self.trans_table.setMinimumHeight(400)
        self.trans_table.verticalHeader().setDefaultSectionSize(45)
        self.trans_table.verticalHeader().setVisible(False)
        self.trans_table.setShowGrid(False)
        self.trans_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.trans_table.setSelectionMode(QTableWidget.SingleSelection)
        table_container.addWidget(self.trans_table)
        
        content_layout.addLayout(table_container, 1)  # Table takes 1/3 of width
        
        layout.addLayout(content_layout)
        
        self.load_transactions()
    
    def add_transaction(self):
        """Add transaction"""
        try:
            amount = float(self.trans_amount.text())
            trans_type = self.trans_type.currentText().lower()
            category = self.trans_category.currentText().lower()
            
            if trans_type == "income":
                self.assistant.finance_manager.add_income(category, amount)
            else:
                self.assistant.finance_manager.add_expense(category, amount)
            
            self.trans_amount.clear()
            self.load_transactions()
            self.refresh()
            self.speak(f"{trans_type} of rupees {amount} added")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid amount")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def load_transactions(self):
        """Load transactions"""
        try:
            transactions = self.assistant.finance_manager.get_transactions(50)
            self.trans_table.setRowCount(len(transactions))
            
            for i, trans in enumerate(transactions):
                # Type with icon
                trans_type = trans.get('transaction_type', '').title()
                icon = "💰" if trans_type == "Income" else "💸"
                type_item = QTableWidgetItem(f"{icon} {trans_type}")
                type_item.setFont(QFont('Arial', 10))
                self.trans_table.setItem(i, 0, type_item)
                
                # Amount with Rupee symbol - colored based on type
                amount = trans.get('amount', 0)
                amount_item = QTableWidgetItem(f"₹{amount:.2f}")
                amount_item.setFont(QFont('Arial', 11, QFont.Bold))
                if trans_type == "Income":
                    amount_item.setForeground(QColor('#10b981'))  # Green
                else:
                    amount_item.setForeground(QColor('#ef4444'))  # Red
                self.trans_table.setItem(i, 1, amount_item)
                
                # Category
                cat_item = QTableWidgetItem(trans.get('category', '').title())
                cat_item.setFont(QFont('Arial', 10))
                self.trans_table.setItem(i, 2, cat_item)
                
                # Date with calendar icon
                date_item = QTableWidgetItem(f"📅 {trans.get('date', '')[:10]}")
                date_item.setFont(QFont('Arial', 9))
                self.trans_table.setItem(i, 3, date_item)
                
                delete_btn = QPushButton("🗑️")
                delete_btn.clicked.connect(lambda checked, id=trans.get('id'): self.delete_transaction(id))
                self.trans_table.setCellWidget(i, 4, delete_btn)
            
            # Update charts
            self.update_finance_charts()
        except Exception as e:
            print(f"Error loading transactions: {e}")
    
    def update_finance_charts(self):
        """Update finance-related charts"""
        try:
            # Get finance summary
            finance_summary = self.assistant.finance_manager.get_summary()
            self.finance_chart.update_finance_data(finance_summary)
            
            # Get expenses by category
            all_transactions = self.assistant.finance_manager.get_transactions(1000)
            expenses_by_category = {}
            for trans in all_transactions:
                if trans.get('transaction_type', '').lower() == 'expense':
                    category = trans.get('category', 'Other').title()
                    expenses_by_category[category] = expenses_by_category.get(category, 0) + trans.get('amount', 0)
            
            expenses_list = sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)
            self.expense_category_chart.update_category_data(expenses_list)
            
            # Budget status
            budget_status = {}
            for category in expenses_by_category:
                raw_pct = (expenses_by_category[category] / 500) * 100
                pct = max(0, min(raw_pct, 100))
                budget_status[category] = {
                    'percentage': pct,
                    'status': 'over' if raw_pct > 100 else 'warning' if raw_pct > 80 else 'ok'
                }
            self.budget_chart.update_budget_data(budget_status)
        except Exception as e:
            print(f"Error updating finance charts: {e}")
    
    def delete_transaction(self, trans_id):
        """Delete transaction"""
        reply = QMessageBox.question(self, "Confirm", "Delete this transaction?")
        if reply == QMessageBox.Yes:
            try:
                self.assistant.finance_manager.db.conn.execute(
                    "DELETE FROM finances WHERE id = ?",
                    (trans_id,)
                )
                self.assistant.finance_manager.db.conn.commit()
                self.assistant.finance_manager._invalidate_cache()
                self.load_transactions()
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def refresh(self):
        """Refresh finances data"""
        self.load_transactions()
        # Intentionally avoid calling parent refresh_all to prevent recursion
