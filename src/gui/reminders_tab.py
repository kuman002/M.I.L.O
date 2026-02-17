"""
Reminders Tab for MILO
Reminder management and notifications
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QDateEdit, QTimeEdit, QMessageBox, QHeaderView
)
from PyQt5.QtCore import QDate, QTime
from PyQt5.QtGui import QColor
from gui.base_tab import BaseTab


class RemindersTab(BaseTab):
    """Reminders management tab"""
    
    def setup_ui(self):
        """Build the reminders UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Add reminder section
        add_layout = QHBoxLayout()
        
        self.reminder_text = QLineEdit()
        self.reminder_text.setPlaceholderText("Reminder message...")
        add_layout.addWidget(QLabel("Message:"))
        add_layout.addWidget(self.reminder_text)
        
        self.reminder_date = QDateEdit()
        self.reminder_date.setDate(QDate.currentDate())
        self.reminder_date.setCalendarPopup(True)
        add_layout.addWidget(QLabel("Date:"))
        add_layout.addWidget(self.reminder_date)
        
        self.reminder_time = QTimeEdit()
        self.reminder_time.setTime(QTime.currentTime())
        add_layout.addWidget(QLabel("Time:"))
        add_layout.addWidget(self.reminder_time)
        
        add_btn = QPushButton("➕ Add Reminder")
        add_btn.clicked.connect(self.add_reminder)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        # Reminders table
        self.reminders_table = QTableWidget()
        self.reminders_table.setColumnCount(5)
        self.reminders_table.setHorizontalHeaderLabels(["Message", "Date", "Time", "Status", "Delete"])
        self.reminders_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.reminders_table)
        
        self.load_reminders()
    
    def add_reminder(self):
        """Add new reminder"""
        message = self.reminder_text.text().strip()
        if not message:
            QMessageBox.warning(self, "Error", "Enter reminder message")
            return
        
        try:
            date = self.reminder_date.date().toString("yyyy-MM-dd")
            time = self.reminder_time.time().toString("HH:mm")
            datetime_str = f"{date} {time}"
            
            # Store reminder in database
            cursor = self.assistant.db.conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (message, datetime, status) VALUES (?, ?, ?)",
                (message, datetime_str, 'pending')
            )
            self.assistant.db.conn.commit()
            
            self.reminder_text.clear()
            self.load_reminders()
            self.refresh()
            self.speak(f"Reminder set for {date} at {time}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def load_reminders(self):
        """Load reminders"""
        try:
            # Create table if not exists
            cursor = self.assistant.db.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    datetime TEXT NOT NULL,
                    status TEXT DEFAULT 'pending'
                )
            """)
            self.assistant.db.conn.commit()
            
            cursor.execute("SELECT * FROM reminders ORDER BY datetime")
            rows = cursor.fetchall()
            
            # Convert sqlite3.Row to dict
            reminders = []
            for row in rows:
                reminder_dict = {}
                for key in row.keys():
                    reminder_dict[key] = row[key]
                reminders.append(reminder_dict)
            
            self.reminders_table.setRowCount(len(reminders))
            
            for i, reminder in enumerate(reminders):
                self.reminders_table.setItem(i, 0, QTableWidgetItem(reminder.get('message', '')))
                
                datetime_str = reminder.get('datetime', '')
                if ' ' in datetime_str:
                    date_part, time_part = datetime_str.split(' ', 1)
                    self.reminders_table.setItem(i, 1, QTableWidgetItem(date_part))
                    self.reminders_table.setItem(i, 2, QTableWidgetItem(time_part))
                else:
                    self.reminders_table.setItem(i, 1, QTableWidgetItem(datetime_str))
                    self.reminders_table.setItem(i, 2, QTableWidgetItem(''))
                
                status = reminder.get('status', 'pending')
                status_item = QTableWidgetItem(status.upper())
                if status == 'completed':
                    status_item.setForeground(QColor('#10b981'))
                elif status == 'pending':
                    status_item.setForeground(QColor('#f59e0b'))
                self.reminders_table.setItem(i, 3, status_item)
                
                delete_btn = QPushButton("🗑️")
                delete_btn.clicked.connect(lambda checked, id=reminder.get('id'): self.delete_reminder(id))
                self.reminders_table.setCellWidget(i, 4, delete_btn)
        except Exception as e:
            print(f"[Reminders] Error loading reminders: {e}")
    
    def delete_reminder(self, reminder_id):
        """Delete reminder"""
        reply = QMessageBox.question(self, "Confirm", "Delete this reminder?")
        if reply == QMessageBox.Yes:
            try:
                cursor = self.assistant.db.conn.cursor()
                cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
                self.assistant.db.conn.commit()
                self.load_reminders()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def create_voice_reminder(self, reminder_info: dict):
        """Create reminder from voice command"""
        try:
            message = reminder_info.get('message', 'Reminder')
            datetime_str = reminder_info.get('datetime', '')
            seconds = reminder_info.get('seconds', 0)
            
            # Store reminder in database
            cursor = self.assistant.db.conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (message, datetime, status) VALUES (?, ?, ?)",
                (message, datetime_str, 'pending')
            )
            self.assistant.db.conn.commit()
            
            # Calculate friendly time description
            if seconds < 60:
                time_desc = f"{seconds} seconds"
            elif seconds < 3600:
                minutes = seconds // 60
                time_desc = f"{minutes} minute{'s' if minutes > 1 else ''}"
            else:
                hours = seconds // 3600
                time_desc = f"{hours} hour{'s' if hours > 1 else ''}"
            
            # Provide feedback
            response = f"✅ Reminder set! I'll remind you to {message} in {time_desc}."
            self.speak(response)
            
            # Reload reminders
            self.load_reminders()
            
            return response
        except Exception as e:
            error_msg = f"Error setting reminder: {str(e)}"
            print(f"[Reminders] {error_msg}")
            return error_msg
    
    def refresh(self):
        """Refresh reminders data"""
        self.load_reminders()
        # Intentionally avoid calling parent refresh_all to prevent recursion
