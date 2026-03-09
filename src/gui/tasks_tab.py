"""
Tasks Tab for MILO
Task management and visualization
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit, QMessageBox,
    QHeaderView, QDialog, QDialogButtonBox, QFrame, QStyle
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont, QColor
from gui.base_tab import BaseTab
from gui.dashboards import TaskDashboardChart, PriorityTasksChart


class TasksTab(BaseTab):
    """Tasks management tab"""
    
    def setup_ui(self):
        """Build the tasks UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Add task section
        add_card = QFrame()
        add_card.setObjectName("panelCard")
        add_card.setStyleSheet("QFrame#panelCard { border-left: 3px solid #38BDF8; }")
        add_card_layout = QVBoxLayout(add_card)
        add_card_layout.setContentsMargins(14, 12, 14, 12)
        add_card_layout.setSpacing(10)

        add_title = QLabel("📝 Create Task")
        add_title.setObjectName("sectionTitle")
        add_card_layout.addWidget(add_title)

        add_layout = QHBoxLayout()
        add_layout.setSpacing(10)
        
        self.task_title = QLineEdit()
        self.task_title.setPlaceholderText("Task title...")
        add_layout.addWidget(self.task_title)
        
        self.task_priority = QComboBox()
        self.task_priority.addItems(["LOW", "MEDIUM", "HIGH"])
        add_layout.addWidget(self.task_priority)
        
        self.task_date = QDateEdit()
        self.task_date.setDate(QDate.currentDate())
        add_layout.addWidget(self.task_date)
        
        add_btn = QPushButton("➕ Add Task")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self.add_task)
        add_layout.addWidget(add_btn)

        add_card_layout.addLayout(add_layout)
        layout.addWidget(add_card)
        
        # Charts section
        charts_card = QFrame()
        charts_card.setObjectName("panelCard")
        charts_card.setStyleSheet("QFrame#panelCard { border-left: 3px solid #6366F1; }")
        charts_card_layout = QVBoxLayout(charts_card)
        charts_card_layout.setContentsMargins(12, 12, 12, 12)
        charts_card_layout.setSpacing(10)

        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(12)
        
        self.task_chart = TaskDashboardChart()
        self.priority_chart = PriorityTasksChart()
        
        charts_layout.addWidget(self.task_chart, 1)
        charts_layout.addWidget(self.priority_chart, 1)
        
        charts_card_layout.addLayout(charts_layout)
        
        # Tasks table
        table_card = QFrame()
        table_card.setObjectName("panelCard")
        table_card.setStyleSheet("QFrame#panelCard { border-left: 3px solid #22D3EE; }")
        table_card_layout = QVBoxLayout(table_card)
        table_card_layout.setContentsMargins(12, 12, 12, 12)
        table_card_layout.setSpacing(10)

        table_title = QLabel("📋 Pending Tasks")
        table_title.setObjectName("sectionTitle")
        table_card_layout.addWidget(table_title)

        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(7)
        self.tasks_table.setHorizontalHeaderLabels(["ID", "Title", "Priority", "Due Date", "Status", "Edit", "Delete"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tasks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tasks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tasks_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tasks_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tasks_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tasks_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.setMinimumHeight(250)
        self.tasks_table.verticalHeader().setDefaultSectionSize(45)
        self.tasks_table.verticalHeader().setVisible(False)
        self.tasks_table.setShowGrid(False)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.setSelectionMode(QTableWidget.SingleSelection)
        self.tasks_table.setFocusPolicy(Qt.NoFocus)
        table_card_layout.addWidget(self.tasks_table)

        # Content split: charts (left) + table (right)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        content_layout.addWidget(charts_card, 2)
        content_layout.addWidget(table_card, 3)
        layout.addLayout(content_layout)
        
        self.load_tasks()
    
    def add_task(self):
        """Add new task"""
        title = self.task_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Error", "Enter task title")
            return
        
        try:
            self.assistant.task_manager.create_task(
                title,
                priority=self.task_priority.currentText().lower(),
                due_date=self.task_date.date().toString("yyyy-MM-dd")
            )
            self.task_title.clear()
            self.load_tasks()
            self.refresh()
            self.speak(f"Task {title} added")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def load_tasks(self):
        """Load tasks into table"""
        try:
            tasks = self.assistant.task_manager.get_pending_tasks()
            tasks = sorted(tasks, key=lambda t: t.get('id', 0), reverse=True)
            self.tasks_table.setRowCount(len(tasks))
            
            for i, task in enumerate(tasks):
                id_item = QTableWidgetItem(str(task.get('id', '')))
                id_item.setTextAlignment(Qt.AlignCenter)
                id_item.setFont(QFont('Arial', 11, QFont.Medium))
                self.tasks_table.setItem(i, 0, id_item)

                title_item = QTableWidgetItem(task.get('title', ''))
                title_item.setFont(QFont('Arial', 11))
                self.tasks_table.setItem(i, 1, title_item)

                priority_item = QTableWidgetItem(task.get('priority', '').upper())
                priority_item.setTextAlignment(Qt.AlignCenter)
                priority_item.setFont(QFont('Arial', 10, QFont.Bold))
                priority = task.get('priority', '').lower()
                if priority == 'high' or priority == 'urgent':
                    priority_item.setForeground(QColor('#FB7185'))
                elif priority == 'medium':
                    priority_item.setForeground(QColor('#F59E0B'))
                else:
                    priority_item.setForeground(QColor('#34D399'))
                self.tasks_table.setItem(i, 2, priority_item)

                due_date = task.get('due_date') or ''
                due_item = QTableWidgetItem(f"📅 {due_date[:10]}" if due_date else "—")
                due_item.setTextAlignment(Qt.AlignCenter)
                due_item.setFont(QFont('Arial', 10))
                self.tasks_table.setItem(i, 3, due_item)

                status_item = QTableWidgetItem(task.get('status', '').upper())
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setFont(QFont('Arial', 10, QFont.Bold))
                status = task.get('status', '').lower()
                if status == 'completed':
                    status_item.setForeground(QColor('#10B981'))
                elif status == 'pending':
                    status_item.setForeground(QColor('#38BDF8'))
                elif status == 'overdue':
                    status_item.setForeground(QColor('#FB7185'))
                self.tasks_table.setItem(i, 4, status_item)
                
                edit_btn = QPushButton()
                edit_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
                edit_btn.setToolTip("Edit task")
                edit_btn.setFixedSize(74, 30)
                edit_btn.clicked.connect(lambda checked, t=task: self.edit_task(t))
                self.tasks_table.setCellWidget(i, 5, edit_btn)
                
                delete_btn = QPushButton()
                delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
                delete_btn.setToolTip("Delete task")
                delete_btn.setFixedSize(74, 30)
                delete_btn.clicked.connect(lambda checked, t=task: self.delete_task(t))
                self.tasks_table.setCellWidget(i, 6, delete_btn)
            
            # Update charts
            self.update_task_charts()
        except Exception as e:
            print(f"Error loading tasks: {e}")
    
    def update_task_charts(self):
        """Update task-related charts"""
        try:
            all_tasks = self.assistant.task_manager.get_tasks()
            
            # Count by status
            task_stats = {
                'pending_tasks': sum(1 for t in all_tasks if t.get('status') == 'pending'),
                'completed_tasks': sum(1 for t in all_tasks if t.get('status') == 'completed'),
                'overdue_tasks': sum(1 for t in all_tasks if t.get('status') == 'overdue'),
            }
            self.task_chart.update_task_data(task_stats)
            
            # Count by priority
            tasks_by_priority = {}
            for task in all_tasks:
                if task.get('status') != 'completed':
                    priority = task.get('priority', 'low').lower()
                    tasks_by_priority[priority] = tasks_by_priority.get(priority, 0) + 1
            self.priority_chart.update_priority_data(tasks_by_priority)
        except Exception as e:
            print(f"Error updating task charts: {e}")
    
    def edit_task(self, task):
        """Edit task"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Task")
        dialog.setGeometry(400, 300, 400, 200)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        layout.addWidget(QLabel("Title:"))
        title_input = QLineEdit(task.get('title', ''))
        layout.addWidget(title_input)
        
        # Priority
        layout.addWidget(QLabel("Priority:"))
        priority_combo = QComboBox()
        priority_combo.addItems(["low", "medium", "high"])
        priority_combo.setCurrentText(task.get('priority', 'medium'))
        layout.addWidget(priority_combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                self.assistant.task_manager.db.update_task(
                    task['id'],
                    title=title_input.text(),
                    priority=priority_combo.currentText()
                )
                self.assistant.task_manager._invalidate_cache()
                self.load_tasks()
                self.refresh()
                self.speak("Task updated")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def delete_task(self, task):
        """Delete task with confirmation"""
        reply = QMessageBox.question(
            self, 
            'Confirm Delete',
            f"Are you sure you want to delete task: {task.get('title', '')}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.assistant.task_manager.db.delete_task(task['id'])
                self.assistant.task_manager._invalidate_cache()
                self.load_tasks()
                self.refresh()
                self.speak("Task deleted")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def refresh(self):
        """Refresh tasks data"""
        self.load_tasks()
        # Intentionally avoid calling parent refresh_all to prevent recursion
