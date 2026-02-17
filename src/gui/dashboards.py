"""
Dashboard Utilities for MILO - Charts and Visualizations
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class ChartCanvas(FigureCanvas):
    """Base class for matplotlib charts in PyQt5"""
    
    def __init__(self, width=5, height=4, dpi=100):
        """Initialize the chart canvas"""
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#0f172a', edgecolor='none')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1a1f2e')
        
        # Style the chart for dark theme
        self.ax.spines['bottom'].set_color('#475569')
        self.ax.spines['left'].set_color('#475569')
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['top'].set_visible(False)
        
        self.ax.tick_params(colors='#94a3b8', labelsize=9)
        self.ax.xaxis.label.set_color('#cbd5e1')
        self.ax.yaxis.label.set_color('#cbd5e1')
        
        self.fig.tight_layout()
        
        super().__init__(self.fig)
        self.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; border-radius: 8px;")


class TaskDashboardChart(ChartCanvas):
    """Dashboard chart for task metrics"""
    
    def __init__(self):
        super().__init__(width=5, height=3.5)
        self.setMinimumHeight(300)
    
    def update_task_data(self, task_stats):
        """Update chart with task data"""
        self.ax.clear()
        
        # Pie chart for task status
        status_counts = {
            'Pending': task_stats.get('pending_tasks', 0),
            'Completed': task_stats.get('completed_tasks', 0),
            'Overdue': task_stats.get('overdue_tasks', 0),
        }
        
        # Remove zero values
        status_counts = {k: v for k, v in status_counts.items() if v > 0}
        
        if status_counts:
            colors = ['#3b82f6', '#10b981', '#ef4444']
            labels = list(status_counts.keys())
            sizes = list(status_counts.values())
            
            wedges, texts, autotexts = self.ax.pie(
                sizes,
                labels=labels,
                colors=colors[:len(labels)],
                autopct='%1.0f%%',
                startangle=90,
                textprops={'color': '#cbd5e1', 'fontsize': 9}
            )
            
            # Style percentage text
            for autotext in autotexts:
                autotext.set_color('#0f172a')
                autotext.set_fontweight('bold')
            
            self.ax.set_title('Task Status Distribution', color='#cbd5e1', fontsize=11, fontweight='bold', pad=15)
        else:
            self.ax.text(0.5, 0.5, 'No tasks', ha='center', va='center', 
                        color='#64748b', fontsize=12, transform=self.ax.transAxes)
            self.ax.set_title('Task Status Distribution', color='#cbd5e1', fontsize=11, fontweight='bold')
        
        self.fig.tight_layout()
        self.draw()


class FinanceDashboardChart(ChartCanvas):
    """Dashboard chart for financial metrics"""
    
    def __init__(self):
        super().__init__(width=5, height=3.5)
        self.setMinimumHeight(300)
    
    def update_finance_data(self, finance_summary):
        """Update chart with finance data"""
        self.ax.clear()
        
        # Bar chart for income vs expenses
        income = finance_summary.get('total_income', 0)
        expenses = finance_summary.get('total_expenses', 0)
        
        if income > 0 or expenses > 0:
            categories = ['Income', 'Expenses']
            values = [income, expenses]
            colors = ['#10b981', '#ef4444']
            
            bars = self.ax.bar(categories, values, color=colors, width=0.5, edgecolor='#475569', linewidth=1.5)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                self.ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'₹{value:.0f}',
                           ha='center', va='bottom', color='#cbd5e1', fontweight='bold', fontsize=10)
            
            self.ax.set_ylabel('Amount (₹)', color='#cbd5e1')
            self.ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 100)
            self.ax.set_title('Income vs Expenses (30 Days)', color='#cbd5e1', fontsize=11, fontweight='bold', pad=15)
        else:
            self.ax.text(0.5, 0.5, 'No transactions', ha='center', va='center',
                        color='#64748b', fontsize=12, transform=self.ax.transAxes)
            self.ax.set_title('Income vs Expenses', color='#cbd5e1', fontsize=11, fontweight='bold')
        
        self.fig.tight_layout()
        self.draw()


class ExpenseByCategoryChart(ChartCanvas):
    """Chart for expense breakdown by category"""
    
    def __init__(self):
        super().__init__(width=5, height=3.5)
        self.setMinimumHeight(300)
    
    def update_category_data(self, expenses_by_category):
        """Update chart with category data"""
        self.ax.clear()
        
        if expenses_by_category:
            # Convert list of tuples to separate lists
            if isinstance(expenses_by_category, list) and len(expenses_by_category) > 0:
                if isinstance(expenses_by_category[0], tuple):
                    categories = [item[0] for item in expenses_by_category[:8]]  # Top 8
                    amounts = [item[1] for item in expenses_by_category[:8]]
                else:
                    return
                
                # Horizontal bar chart
                colors = plt.cm.Set3(range(len(categories)))
                bars = self.ax.barh(categories, amounts, color=colors, edgecolor='#475569', linewidth=1.5)
                
                # Add value labels
                for bar, amount in zip(bars, amounts):
                    width = bar.get_width()
                    self.ax.text(width, bar.get_y() + bar.get_height()/2.,
                               f' ₹{amount:.0f}',
                               ha='left', va='center', color='#cbd5e1', fontweight='bold', fontsize=9)
                
                self.ax.set_xlabel('Amount (₹)', color='#cbd5e1')
                self.ax.set_title('Expenses by Category', color='#cbd5e1', fontsize=11, fontweight='bold', pad=15)
                self.ax.invert_yaxis()
            else:
                self.ax.text(0.5, 0.5, 'No expense data', ha='center', va='center',
                            color='#64748b', fontsize=12, transform=self.ax.transAxes)
                self.ax.set_title('Expenses by Category', color='#cbd5e1', fontsize=11, fontweight='bold')
        else:
            self.ax.text(0.5, 0.5, 'No expense data', ha='center', va='center',
                        color='#64748b', fontsize=12, transform=self.ax.transAxes)
            self.ax.set_title('Expenses by Category', color='#cbd5e1', fontsize=11, fontweight='bold')
        
        self.fig.tight_layout()
        self.draw()


class PriorityTasksChart(ChartCanvas):
    """Chart for task breakdown by priority"""
    
    def __init__(self):
        super().__init__(width=5, height=3)
        self.setMinimumHeight(250)
    
    def update_priority_data(self, tasks_by_priority):
        """Update chart with priority data"""
        self.ax.clear()
        
        if tasks_by_priority:
            priorities = list(tasks_by_priority.keys())
            counts = list(tasks_by_priority.values())
            
            # Color map for priorities
            priority_colors = {
                'urgent': '#ef4444',
                'high': '#f97316',
                'medium': '#eab308',
                'low': '#3b82f6'
            }
            
            colors = [priority_colors.get(p, '#64748b') for p in priorities]
            
            bars = self.ax.bar(priorities, counts, color=colors, edgecolor='#475569', linewidth=1.5)
            
            # Add value labels
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                self.ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(count)}',
                           ha='center', va='bottom', color='#cbd5e1', fontweight='bold', fontsize=9)
            
            self.ax.set_ylabel('Count', color='#cbd5e1')
            self.ax.set_title('Tasks by Priority', color='#cbd5e1', fontsize=11, fontweight='bold', pad=10)
        else:
            self.ax.text(0.5, 0.5, 'No tasks', ha='center', va='center',
                        color='#64748b', fontsize=12, transform=self.ax.transAxes)
            self.ax.set_title('Tasks by Priority', color='#cbd5e1', fontsize=11, fontweight='bold')
        
        self.fig.tight_layout()
        self.draw()


class BudgetStatusChart(ChartCanvas):
    """Chart for budget status across categories"""
    
    def __init__(self):
        super().__init__(width=5, height=3)
        self.setMinimumHeight(250)
    
    def update_budget_data(self, budget_status):
        """Update chart with budget data"""
        self.ax.clear()
        
        if budget_status:
            categories = []
            percentages = []
            colors_list = []
            
            for category, status in budget_status.items():
                categories.append(category)
                percentage = status.get('percentage', 0)
                percentages.append(max(0, min(percentage, 100)))  # Clamp 0-100
                
                # Color based on status
                if status.get('status') == 'over':
                    colors_list.append('#ef4444')
                elif status.get('status') == 'warning':
                    colors_list.append('#f97316')
                else:
                    colors_list.append('#10b981')
            
            # Horizontal bar chart with percentages
            bars = self.ax.barh(categories, percentages, color=colors_list, edgecolor='#475569', linewidth=1.5)
            
            # Add percentage labels
            for bar, pct in zip(bars, percentages):
                width = bar.get_width()
                label_pct = max(0, min(pct, 100))
                self.ax.text(width, bar.get_y() + bar.get_height()/2.,
                           f' {label_pct:.0f}%',
                           ha='left', va='center', color='#cbd5e1', fontweight='bold', fontsize=9)
            
            self.ax.set_xlabel('Budget Used (%)', color='#cbd5e1')
            self.ax.set_xlim(0, 100)
            self.ax.axvline(x=100, color='#64748b', linestyle='--', linewidth=1, alpha=0.5)
            self.ax.set_title('Budget Status', color='#cbd5e1', fontsize=11, fontweight='bold', pad=10)
            self.ax.invert_yaxis()
        else:
            self.ax.text(0.5, 0.5, 'No budget data', ha='center', va='center',
                        color='#64748b', fontsize=12, transform=self.ax.transAxes)
            self.ax.set_title('Budget Status', color='#cbd5e1', fontsize=11, fontweight='bold')
        
        self.fig.tight_layout()
        self.draw()


def create_dashboard_section(title, charts):
    """Create a dashboard section with multiple charts"""
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    
    # Title
    title_label = QLabel(title)
    title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
    title_label.setStyleSheet("color: #cbd5e1; margin-top: 10px; margin-bottom: 10px;")
    layout.addWidget(title_label)
    
    # Charts in a row
    charts_layout = QHBoxLayout()
    charts_layout.setSpacing(15)
    
    for chart in charts:
        charts_layout.addWidget(chart, 1)
    
    layout.addLayout(charts_layout)
    
    return container
