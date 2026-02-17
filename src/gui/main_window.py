"""
Clean MILO Main Window
Modularized interface
"""
import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTabWidget,
    QMessageBox, QFrame
)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QIcon

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Thread-safe signal emitter for voice commands
class VoiceCommandEmitter(QObject):
    """Emits voice command signals from voice recognition thread"""
    voice_command_detected = pyqtSignal(str)
    status_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)


from database import Database
from assistant import MILOAssistant
from voice.voice_recognition_optimized import VoiceRecognizer
from voice.text_to_speech import TextToSpeech

from gui.dashboard_tab import DashboardTab
from gui.tasks_tab import TasksTab
from gui.finances_tab import FinancesTab
from gui.habits_tab import HabitsTab
from gui.reminders_tab import RemindersTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MILO - Managing Information & Lifestyle Optimizer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set application icon (cute robot icon for window and taskbar)
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets')
        icon_files = ['cute_robot.ico', 'cute_robot.png']
        icon_set = False
        
        for icon_file in icon_files:
            icon_path = os.path.join(assets_dir, icon_file)
            if os.path.exists(icon_path):
                try:
                    icon = QIcon(icon_path)
                    self.setWindowIcon(icon)
                    from PyQt5.QtWidgets import QApplication
                    QApplication.setWindowIcon(icon)
                    print(f"[GUI] Icon loaded: {icon_file} (window + taskbar)")
                    icon_set = True
                    break
                except Exception as e:
                    print(f"[GUI] Failed to load {icon_file}: {e}")
        
        if not icon_set:
            print("[GUI] WARNING: No icon file found in assets directory")
        
        # Initialize core
        self.db = Database()
        self.assistant = MILOAssistant(self.db)
        self.tts = TextToSpeech()
        
        # Initialize thread-safe voice command emitter
        self.voice_emitter = VoiceCommandEmitter()
        self.voice_emitter.voice_command_detected.connect(self.handle_voice_command)
        self.voice_emitter.status_update.connect(self.update_status)
        self.voice_emitter.error_occurred.connect(self.handle_voice_error)
        
        # Initialize optimized voice recognition
        print("[GUI] Initializing Voice Recognition...")
        self.voice_recognizer = VoiceRecognizer(model_size="base")
        self.is_listening = False
        
        # Apply styling
        self.setStyleSheet(self.get_styles())
        
        # Build UI
        self.setup_ui()
        
        # Timers
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(30000)
    
    def get_styles(self):
        return """
        QMainWindow, QWidget {
            background-color: #1a1f2e;
            color: #ffffff;
        }
        QTabBar::tab {
            background-color: #252c3c;
            color: #ffffff;
            padding: 8px 20px;
            margin-right: 2px;
            border: none;
        }
        QTabBar::tab:selected {
            background-color: #0066cc;
        }
        QPushButton {
            background-color: #0066cc;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #0052a3;
        }
        QLineEdit, QComboBox, QDateEdit {
            background-color: #252c3c;
            color: #ffffff;
            border: 1px solid #404854;
            border-radius: 4px;
            padding: 6px;
        }
        QTableWidget {
            background-color: #1a1f2e;
            gridline-color: #2d3748;
            border: 1px solid #2d3748;
            border-radius: 8px;
        }
        QTableWidget::item {
            padding: 12px 8px;
            border-bottom: 1px solid #2d3748;
            color: #e2e8f0;
        }
        QTableWidget::item:selected {
            background-color: #0066cc;
            color: #ffffff;
        }
        QTableWidget::item:hover {
            background-color: #2d3748;
        }
        QTableWidget::item:alternate {
            background-color: #252c3c;
        }
        QHeaderView::section {
            background-color: #0066cc;
            color: #ffffff;
            padding: 12px 8px;
            border: none;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        QHeaderView::section:hover {
            background-color: #0052a3;
        }
        QTextEdit {
            background-color: #0f1419;
            color: #cbd5e1;
            border: 1px solid #334155;
            border-radius: 4px;
        }
        """
    
    def setup_ui(self):
        """Setup main UI"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create modular tabs
        self.dashboard_tab = DashboardTab(self.assistant, self.tts, self)
        self.tabs.addTab(self.dashboard_tab, "📊 Dashboard")
        
        self.tasks_tab = TasksTab(self.assistant, self.tts, self)
        self.tabs.addTab(self.tasks_tab, "✓ Tasks")
        
        self.finances_tab = FinancesTab(self.assistant, self.tts, self)
        self.tabs.addTab(self.finances_tab, "💰 Finances")
        
        self.habits_tab = HabitsTab(self.assistant, self.tts, self)
        self.tabs.addTab(self.habits_tab, "🎯 Habits")
        
        self.reminders_tab = RemindersTab(self.assistant, self.tts, self)
        self.tabs.addTab(self.reminders_tab, "⏰ Reminders")
        
        # Footer
        footer = self.create_footer()
        main_layout.addWidget(footer)
    
    def create_header(self):
        """Create header with controls"""
        header = QFrame()
        header.setStyleSheet("background-color: #0f1419; border-bottom: 1px solid #334155;")
        header.setMaximumHeight(70)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        
        title = QLabel("🤖 MILO")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        subtitle = QLabel("Managing Information & Lifestyle Optimizer")
        subtitle.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(subtitle)
        
        layout.addStretch()
        
        self.listen_btn = QPushButton("🎤 Start Listening")
        self.listen_btn.clicked.connect(self.toggle_voice)
        layout.addWidget(self.listen_btn)
        
        help_btn = QPushButton("❓ Help")
        help_btn.clicked.connect(self.show_commands_help)
        layout.addWidget(help_btn)
        
        calibrate_btn = QPushButton("🎛️ Calibrate")
        calibrate_btn.clicked.connect(self.calibrate_voice)
        layout.addWidget(calibrate_btn)
        
        self.status_label = QLabel("✅ Ready")
        self.status_label.setStyleSheet("color: #00ff00; font-weight: bold; padding: 0 10px;")
        layout.addWidget(self.status_label)
        
        return header
    
    def create_footer(self):
        """Create footer with message area and input"""
        footer = QFrame()
        footer.setStyleSheet("background-color: #0f1419; border-top: 1px solid #334155;")
        footer.setMaximumHeight(120)
        
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        
        self.message_area = QTextEdit()
        self.message_area.setMaximumHeight(35)
        self.message_area.setReadOnly(True)
        self.message_area.setText("Ready for commands...")
        layout.addWidget(self.message_area)
        
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask MILO anything...")
        self.input_field.returnPressed.connect(self.process_input)
        input_layout.addWidget(self.input_field)
        
        send_btn = QPushButton("📤 Send")
        send_btn.clicked.connect(self.process_input)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        return footer
    
    def check_reminders(self):
        """Check for due reminders"""
        try:
            import datetime
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT * FROM reminders WHERE datetime <= ? AND status = 'pending' ORDER BY datetime",
                (now,)
            )
            rows = cursor.fetchall()
            
            reminders = []
            for row in rows:
                reminder_dict = {}
                for key in row.keys():
                    reminder_dict[key] = row[key]
                reminders.append(reminder_dict)
            
            for reminder in reminders:
                message = reminder.get('message', '')
                reminder_text = f"""
⏰ REMINDER ALERT ⏰

{message}

Time: {reminder.get('datetime', 'Now')}
                """.strip()
                
                self.message_area.setText(reminder_text)
                QMessageBox.information(self, "⏰ REMINDER", reminder_text)
                
                try:
                    spoken_message = f"Reminder: {message}"
                    if self.tts:
                        self.tts.speak(spoken_message, wait=True)
                except Exception as tts_error:
                    print(f"[Reminders] TTS Error: {tts_error}")
                
                self.log_command(f"Reminder: {message}", f"Reminder triggered at {reminder.get('datetime')}", "system")
                
                cursor.execute(
                    "UPDATE reminders SET status = 'completed' WHERE id = ?",
                    (reminder.get('id'),)
                )
                self.db.conn.commit()
            
            if reminders and self.reminders_tab:
                self.reminders_tab.load_reminders()
        except Exception as e:
            print(f"[Reminders] Error checking reminders: {e}")
    
    # ==================== Voice & Input ====================
    
    def toggle_voice(self):
        """Toggle voice listening with optimized recognition"""
        if not self.voice_recognizer or not self.voice_recognizer.is_available():
            QMessageBox.warning(
                self,
                "Voice Recognition Not Available",
                "To enable voice recognition, install openai-whisper:\n\n"
                "pip install openai-whisper\n\n"
                "Then restart MILO."
            )
            return
        
        self.is_listening = not self.is_listening
        if self.is_listening:
            self.listen_btn.setText("⏹️ Stop Listening")
            self.status_label.setText("🎤 Listening...")
            self.status_label.setStyleSheet("color: #3498db; font-weight: bold; padding: 0 10px;")
            self.voice_recognizer.start_listening(self.voice_callback)
        else:
            self.listen_btn.setText("🎤 Start Listening")
            self.status_label.setText("✅ Ready")
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold; padding: 0 10px;")
            if self.voice_recognizer:
                self.voice_recognizer.stop_listening()
    
    def voice_callback(self, text: str):
        """Callback from voice recognition thread - emits signal to main thread"""
        self.voice_emitter.voice_command_detected.emit(text)
    
    def handle_voice_command(self, text: str):
        """Handle voice command (runs in main thread via signal)"""
        if not text:
            return
        
        try:
            command = self.voice_recognizer.detect_command(text)
            
            if command:
                command_id, matched_phrase = command
                self.update_status(f"✅ Command: {matched_phrase}")
                
                if command_id == "ADD_TASK":
                    self.add_task_dialog()
                    self.log_command(text, "Opening add task dialog", "voice")
                elif command_id == "ADD_EXPENSE":
                    self.add_transaction_dialog()
                    self.log_command(text, "Opening add expense dialog", "voice")
                elif command_id == "CHECK_BALANCE":
                    self.show_balance_message()
                elif command_id == "ADD_HABIT":
                    self.add_habit_dialog()
                    self.log_command(text, "Opening add habit dialog", "voice")
                elif command_id == "LOG_HABIT":
                    self.log_habit_dialog()
                    self.log_command(text, "Opening habit log dialog", "voice")
                elif command_id == "REMIND_ME":
                    reminder_info = self.voice_recognizer.parse_reminder_command(text)
                    if reminder_info:
                        response = self.reminders_tab.create_voice_reminder(reminder_info)
                        self.message_area.setText(response)
                        self.log_command(text, response, "voice")
                        self.tabs.setCurrentIndex(4)
                    else:
                        response = "I didn't understand the reminder time. Please try: 'Remind me to call mom in 5 minutes'"
                        self.message_area.setText(response)
                        self.tts.speak(response)
                        self.log_command(text, response, "voice")
                elif command_id == "REFRESH":
                    self.refresh_all()
                    self.update_status("✅ Refreshed")
                    self.log_command(text, "Dashboard refreshed", "voice")
                elif command_id == "WAKE_WORD":
                    self.update_status("👂 MILO listening...")
                    self.tts.speak("Yes, I'm listening")
                    self.log_command(text, "MILO activated and listening", "voice")
                else:
                    self.process_voice_text(text)
            else:
                self.process_voice_text(text)
        except Exception as e:
            error_msg = f"Voice command error: {str(e)}"
            self.handle_voice_error(error_msg)
            self.log_command(text, error_msg, "voice")
    
    def process_voice_text(self, text: str):
        """Process voice text through assistant"""
        self.message_area.setText(f"Processing: {text}...")
        try:
            response = self.assistant.process_command(text)
            message = response.get('message', 'Done')
            self.message_area.setText(message)
            if self.tts:
                self.tts.speak(message)
            self.log_command(text, message, "voice")
            self.refresh_all()
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.message_area.setText(error_msg)
            self.log_command(text, error_msg, "voice")
    
    def update_status(self, message: str):
        """Update status label"""
        if self.status_label:
            self.status_label.setText(message)
    
    def handle_voice_error(self, error_message: str):
        """Handle voice recognition errors"""
        print(f"❌ {error_message}")
        if self.message_area:
            self.message_area.setText(f"Error: {error_message}")
    
    def show_balance_message(self):
        """Show balance in response to voice command"""
        try:
            balance = self.assistant.finance_manager.get_balance()
            message = f"Your current balance is ₹{balance:.2f}"
            self.message_area.setText(message)
            if self.tts:
                self.tts.speak(f"Your current balance is rupees {balance:.2f}", wait=False)
            self.log_command("check balance", message, "voice")
        except Exception as e:
            error_msg = f"Error getting balance: {str(e)}"
            self.message_area.setText(error_msg)
            self.log_command("check balance", error_msg, "voice")
    
    def add_task_dialog(self):
        """Open add task dialog from voice command"""
        self.tabs.setCurrentIndex(1)
        if self.tasks_tab:
            self.tasks_tab.task_title.setFocus()
        self.status_label.setText("✅ Ready to add task")
        if self.tts:
            self.tts.speak("Please enter task details", wait=False)
    
    def add_transaction_dialog(self):
        """Open add transaction dialog from voice command"""
        self.tabs.setCurrentIndex(2)
        if self.finances_tab:
            self.finances_tab.trans_amount.setFocus()
        self.status_label.setText("✅ Ready to add expense")
        if self.tts:
            self.tts.speak("Please enter expense details", wait=False)
    
    def add_habit_dialog(self):
        """Open add habit dialog from voice command"""
        self.tabs.setCurrentIndex(3)
        if self.habits_tab:
            self.habits_tab.habit_name.setFocus()
        self.status_label.setText("✅ Ready to add habit")
        if self.tts:
            self.tts.speak("Please enter habit name", wait=False)
    
    def log_habit_dialog(self):
        """Open habit logging from voice command"""
        self.tabs.setCurrentIndex(3)
        self.status_label.setText("✅ Select habit to log")
        if self.tts:
            self.tts.speak("Click log button for the habit you completed", wait=False)
    
    def calibrate_voice(self):
        """Calibrate microphone for optimized recognition"""
        if not self.voice_recognizer or not self.voice_recognizer.is_available():
            QMessageBox.warning(self, "Voice Recognition", "Voice recognition is not available.")
            return
        
        QMessageBox.information(self, "Calibration", "Keep quiet for 3 seconds while MILO calibrates...")
        self.status_label.setText("🎛️ Calibrating...")
        try:
            if self.voice_recognizer.calibrate_noise(duration=3.0):
                self.status_label.setText("✅ Calibration complete")
            else:
                self.status_label.setText("❌ Calibration failed")
                QMessageBox.warning(self, "Failed", "Calibration failed. Please check your microphone.")
        except Exception as e:
            self.status_label.setText("❌ Calibration failed")
            QMessageBox.warning(self, "Failed", f"Calibration failed: {e}")
    
    def show_commands_help(self):
        """Show available voice commands"""
        commands_text = """
📋 AVAILABLE VOICE COMMANDS:

🎯 TASK MANAGEMENT:
• "Add task" / "Create task" / "New task"
• "Delete task" / "Remove task"
• "Complete task" / "Finish task"

💰 FINANCE:
• "Add expense" - Add a new expense
• "Add income" - Add income entry
• "Check balance" / "Show balance"

🎯 HABITS:
• "Add habit" - Create new habit
• "Log habit" / "Track habit"

⏰ REMINDERS:
• "Remind me in 10 seconds"
• "Remind me to [action] in 5 minutes"
• "Set reminder to [action] in 2 hours"

🔧 SYSTEM:
• "Refresh" - Refresh dashboard
• "Open browser"
• "Close window"
• "Hey MILO" / "Hello MILO" / "Hi MILO" - Wake word

📝 TEXT INPUT:
• Use the text field at the bottom to type commands
        """
        
        QMessageBox.information(self, "💬 MILO Voice Commands", commands_text)
        if self.tts:
            self.tts.speak("Available commands displayed", wait=False)
    
    def log_command(self, command: str, response: str, source: str = "text"):
        """Log command and response to dashboard"""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            icon = "🎤" if source == "voice" else "⌨️"
            if self.dashboard_tab:
                self.dashboard_tab.update_command_display(f"{icon} [{timestamp}]\n{command}")
                self.dashboard_tab.update_reply_display(f"💬 [{timestamp}]\n{response}")
        except Exception as e:
            print(f"Error logging command: {e}")
    
    def process_input(self):
        """Process user input"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        self.message_area.setText(f"Processing: {text}...")
        self.input_field.clear()
        
        try:
            response = self.assistant.process_command(text)
            response_msg = response.get('message', 'Done')
            self.message_area.setText(response_msg)
            if self.tts:
                self.tts.speak(response_msg)
            
            self.log_command(text, response_msg, "text")
            self.refresh_all()
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.message_area.setText(error_msg)
            self.log_command(text, error_msg, "text")
    
    def refresh_all(self):
        """Refresh all data"""
        if self.tasks_tab:
            self.tasks_tab.refresh()
        if self.finances_tab:
            self.finances_tab.refresh()
        if self.habits_tab:
            self.habits_tab.refresh()
        if self.reminders_tab:
            self.reminders_tab.refresh()
        self.check_reminders()
        self.check_habit_reminders()
        self.update_dashboard_metrics()

    def check_habit_reminders(self):
        """Remind user about habits not logged today at their reminder time"""
        try:
            due_habits = self.assistant.habit_manager.get_due_habit_reminders()
            if not due_habits:
                return

            habit_names = ", ".join([h.get('name', 'Habit') for h in due_habits])
            message = f"⏰ Habit reminder: {habit_names}"
            self.message_area.setText(message)
            QMessageBox.information(self, "⏰ Habit Reminder", message)
            if self.tts:
                self.tts.speak(message, wait=False)
        except Exception as e:
            print(f"[Habits] Reminder error: {e}")
    
    def update_dashboard_metrics(self):
        """Update dashboard metric cards with live data"""
        try:
            tasks = self.assistant.task_manager.get_pending_tasks()
            upcoming_tasks = self.assistant.task_manager.get_upcoming_tasks(7)
            balance = self.assistant.finance_manager.get_balance()
            habits = self.assistant.habit_manager.get_habits()
            habit_ids = [h.get('id') for h in habits if h.get('id') is not None]
            logged_today = self.assistant.habit_manager.get_logged_today_ids(habit_ids)
            insights = self.assistant.habit_manager.analyze_patterns()
            
            if self.dashboard_tab:
                self.dashboard_tab.tasks_value_label.setText(str(len(tasks)))
                self.dashboard_tab.balance_value_label.setText(f"₹{balance:,.2f}")
                self.dashboard_tab.habits_value_label.setText(str(len(habits)))
                suggestions = insights.get('suggestions', [])
                if suggestions:
                    insights_text = "\n".join([f"💡 {item}" for item in suggestions[:2]])
                else:
                    insights_text = "💡 No insights available yet."
                self.dashboard_tab.update_insights(insights_text)

                upcoming_lines = []
                if upcoming_tasks:
                    first = upcoming_tasks[0]
                    title = first.get('title', 'Task')
                    due = (first.get('due_date') or '')[:10]
                    priority = (first.get('priority') or 'medium').upper()
                    upcoming_lines.append(f"📌 {title}")
                    if due:
                        upcoming_lines.append(f"Due: {due} | {priority}")
                else:
                    upcoming_lines.append("📌 No upcoming tasks in the next 7 days.")

                if habits:
                    upcoming_lines.append(f"📝 Habits logged today: {len(logged_today)}/{len(habits)}")
                    next_habit = next((h for h in habits if h.get('id') not in logged_today), None)
                    if next_habit:
                        habit_time = next_habit.get('reminder_time', '20:00')
                        upcoming_lines.append(f"⏳ Next habit: {next_habit.get('name', 'Habit')} @ {habit_time}")
                else:
                    upcoming_lines.append("📝 No habits yet. Add one to start tracking.")

                self.dashboard_tab.update_upcoming("\n".join(upcoming_lines))
        except Exception as e:
            print(f"Error updating dashboard: {e}")
    
    def closeEvent(self, event):
        """Cleanup on close"""
        if self.voice_recognizer:
            self.voice_recognizer.cleanup()
        if self.db:
            self.db.close()
        event.accept()


def main():
    app = __import__('PyQt5.QtWidgets', fromlist=['QApplication']).QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
