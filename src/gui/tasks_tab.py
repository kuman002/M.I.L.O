"""
Tasks Tab for MILO
Task management and visualization
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit, QMessageBox,
    QHeaderView, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import QDate
from gui.base_tab import BaseTab
from gui.dashboards import TaskDashboardChart, PriorityTasksChart


class TasksTab(BaseTab):
    """Tasks management tab"""
    
    def setup_ui(self):
        """Build the tasks UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Add task section
        add_layout = QHBoxLayout()
        
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
        add_btn.clicked.connect(self.add_task)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        # Charts section
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)
        
        self.task_chart = TaskDashboardChart()
        self.priority_chart = PriorityTasksChart()
        
        charts_layout.addWidget(self.task_chart, 1)
        charts_layout.addWidget(self.priority_chart, 1)
        
        layout.addLayout(charts_layout)
        
        # Tasks table
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(7)
        self.tasks_table.setHorizontalHeaderLabels(["ID", "Title", "Priority", "Due Date", "Status", "Edit", "Delete"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tasks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.setMinimumHeight(250)
        self.tasks_table.verticalHeader().setDefaultSectionSize(45)
        self.tasks_table.verticalHeader().setVisible(False)
        self.tasks_table.setShowGrid(False)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tasks_table)
        
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
            self.tasks_table.setRowCount(len(tasks))
            
            for i, task in enumerate(tasks):
                self.tasks_table.setItem(i, 0, QTableWidgetItem(str(task.get('id', ''))))
                self.tasks_table.setItem(i, 1, QTableWidgetItem(task.get('title', '')))
                self.tasks_table.setItem(i, 2, QTableWidgetItem(task.get('priority', '').upper()))
                self.tasks_table.setItem(i, 3, QTableWidgetItem(task.get('due_date', '')[:10]))
                self.tasks_table.setItem(i, 4, QTableWidgetItem(task.get('status', '')))
                
                edit_btn = QPushButton("✏️")
                edit_btn.clicked.connect(lambda checked, t=task: self.edit_task(t))
                self.tasks_table.setCellWidget(i, 5, edit_btn)
                
                delete_btn = QPushButton("🗑️")
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
