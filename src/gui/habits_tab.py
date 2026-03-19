"""
Habits Tab for MILO
Habit tracking and logging
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QTimeEdit, QFrame, QLabel, QStyle
)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QColor, QFont
from gui.base_tab import BaseTab


class HabitsTab(BaseTab):
    """Habits tracking tab"""
    
    def setup_ui(self):
        """Build the habits UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Add habit section
        add_card = QFrame()
        add_card.setObjectName("panelCard")
        add_card.setStyleSheet("QFrame#panelCard { border-left: 3px solid #F59E0B; }")
        add_card_layout = QVBoxLayout(add_card)
        add_card_layout.setContentsMargins(14, 12, 14, 12)
        add_card_layout.setSpacing(10)

        add_title = QLabel("📈 Create Habit")
        add_title.setObjectName("sectionTitle")
        add_card_layout.addWidget(add_title)

        add_layout = QHBoxLayout()
        add_layout.setSpacing(10)
        
        self.habit_name = QLineEdit()
        self.habit_name.setPlaceholderText("Habit name...")
        add_layout.addWidget(self.habit_name, 1)

        self.habit_time = QTimeEdit()
        self.habit_time.setDisplayFormat("HH:mm")
        self.habit_time.setTime(QTime.currentTime())
        add_layout.addWidget(self.habit_time)
        
        add_btn = QPushButton("➕ Add Habit")
        add_btn.setObjectName("primary")
        add_btn.setMinimumWidth(120)
        add_btn.clicked.connect(self.add_habit)
        add_layout.addWidget(add_btn)

        add_card_layout.addLayout(add_layout)
        layout.addWidget(add_card)
        
        # Habits table
        table_card = QFrame()
        table_card.setObjectName("panelCard")
        table_card.setStyleSheet("QFrame#panelCard { border-left: 3px solid #FB7185; }")
        table_card_layout = QVBoxLayout(table_card)
        table_card_layout.setContentsMargins(12, 12, 12, 12)
        table_card_layout.setSpacing(10)

        table_title = QLabel("✅ Habit Tracker")
        table_title.setObjectName("sectionTitle")
        table_card_layout.addWidget(table_title)

        self.habits_table = QTableWidget()
        self.habits_table.setColumnCount(5)
        self.habits_table.setHorizontalHeaderLabels(["Habit", "Time", "Streak", "Log", "Delete"])
        self.habits_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.habits_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.habits_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.habits_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.habits_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.habits_table.setColumnWidth(1, 110)
        self.habits_table.setColumnWidth(2, 90)
        self.habits_table.setColumnWidth(3, 110)
        self.habits_table.setColumnWidth(4, 110)
        self.habits_table.setAlternatingRowColors(True)
        self.habits_table.setMinimumHeight(300)
        self.habits_table.verticalHeader().setDefaultSectionSize(45)
        self.habits_table.verticalHeader().setVisible(False)
        self.habits_table.setShowGrid(False)
        self.habits_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.habits_table.setSelectionMode(QTableWidget.SingleSelection)
        self.habits_table.setFocusPolicy(Qt.NoFocus)
        self.habits_table.setEditTriggers(QTableWidget.NoEditTriggers)
        table_card_layout.addWidget(self.habits_table)
        layout.addWidget(table_card)
        
        self.load_habits()
    
    def add_habit(self):
        """Add habit"""
        name = self.habit_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Enter habit name")
            return
        
        try:
            reminder_time = self.habit_time.time().toString("HH:mm")
            self.assistant.habit_manager.add_habit(name, reminder_time=reminder_time)
            self.habit_name.clear()
            self.load_habits()
            self.refresh()
            self.speak(f"Habit {name} added")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def load_habits(self):
        """Load habits"""
        try:
            habits = self.assistant.habit_manager.get_habits()
            self.habits_table.setRowCount(len(habits))
            habit_ids = [habit.get('id') for habit in habits if habit.get('id') is not None]
            logged_today = self.assistant.habit_manager.get_logged_today_ids(habit_ids)
            
            for i, habit in enumerate(habits):
                name_item = QTableWidgetItem(habit.get('name', ''))
                name_item.setFont(QFont('Arial', 11))
                time_item = QTableWidgetItem(habit.get('reminder_time', '20:00'))
                time_item.setTextAlignment(Qt.AlignCenter)
                time_item.setFont(QFont('Arial', 10))
                streak_val = habit.get('streak', 0)
                fire = "\U0001f525 " if streak_val >= 3 else ("\u2b50 " if streak_val > 0 else "")
                streak_item = QTableWidgetItem(f"{fire}{streak_val}")
                streak_item.setTextAlignment(Qt.AlignCenter)
                streak_item.setFont(QFont('Segoe UI', 13, QFont.Bold))
                streak_item.setForeground(QColor('#FBBF24') if streak_val >= 3 else QColor('#38BDF8'))
                self.habits_table.setItem(i, 0, name_item)
                self.habits_table.setItem(i, 1, time_item)
                self.habits_table.setItem(i, 2, streak_item)
                
                habit_id = habit.get('id')
                if habit_id in logged_today:
                    logged_item = QTableWidgetItem("LOGGED")
                    logged_item.setTextAlignment(Qt.AlignCenter)
                    logged_item.setFont(QFont('Arial', 10, QFont.Bold))
                    logged_item.setForeground(QColor('#10b981'))
                    self.habits_table.setItem(i, 3, logged_item)
                else:
                    log_btn = QPushButton()
                    log_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
                    log_btn.setToolTip("Log habit")
                    log_btn.setFixedSize(90, 30)
                    log_btn.clicked.connect(lambda checked, id=habit_id: self.log_habit(id))
                    self.habits_table.setCellWidget(i, 3, log_btn)
                
                delete_btn = QPushButton()
                delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
                delete_btn.setToolTip("Delete habit")
                delete_btn.setFixedSize(74, 30)
                delete_btn.clicked.connect(lambda checked, id=habit_id: self.delete_habit(id))
                self.habits_table.setCellWidget(i, 4, delete_btn)

            # Clear any default selection to avoid blue first row
            self.habits_table.clearSelection()
            self.habits_table.setCurrentItem(None)
        except Exception as e:
            print(f"Error loading habits: {e}")
    
    def log_habit(self, habit_id):
        """Log habit completion"""
        try:
            result = self.assistant.habit_manager.log_habit(habit_id)
            if result.get('success'):
                self.load_habits()
                self.refresh()
                self.speak("Habit logged")
            else:
                QMessageBox.information(self, "Habit", result.get('message', 'Already logged'))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def delete_habit(self, habit_id):
        """Delete habit"""
        reply = QMessageBox.question(self, "Confirm", "Delete this habit?")
        if reply == QMessageBox.Yes:
            try:
                # Remove habit logs first to satisfy FK constraint
                self.assistant.habit_manager.db.conn.execute(
                    "DELETE FROM habit_logs WHERE habit_id = ?",
                    (habit_id,)
                )
                self.assistant.habit_manager.db.conn.execute(
                    "DELETE FROM habits WHERE id = ?",
                    (habit_id,)
                )
                self.assistant.habit_manager.db.conn.commit()
                self.assistant.habit_manager._invalidate_cache()
                self.load_habits()
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def refresh(self):
        """Refresh habits data"""
        self.load_habits()
        # Intentionally avoid calling parent refresh_all to prevent recursion
