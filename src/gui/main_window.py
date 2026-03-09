"""
Clean MILO Main Window
Modularized interface
"""
import sys
import os
import warnings
import datetime

# Suppress matplotlib layout and math warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
warnings.filterwarnings('ignore', category=RuntimeWarning, module='matplotlib')

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTabWidget,
    QMessageBox, QFrame, QInputDialog, QGraphicsBlurEffect, QStyle,
    QProgressDialog, QApplication
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


from database.database import Database
from assistant import MILOAssistant
from voice.voice_recognition_optimized import VoiceRecognizer
from voice.text_to_speech import TextToSpeech
from core.security import PinManager, capture_intruder

from gui.dashboard_tab import DashboardTab
from gui.tasks_tab import TasksTab
from gui.finances_tab import FinancesTab
from gui.habits_tab import HabitsTab
from gui.reminders_tab import RemindersTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.authenticated = False
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
        
        # Initialize PIN manager
        self.pin_manager = PinManager()
        
        # Initialize core
        self.db = Database()
        self.tts = TextToSpeech()
        self.assistant = MILOAssistant(self.db, tts=self.tts)
        
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
        self._is_closing = False
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(30000)
        
        # Show window with blur effect and authenticate
        self.showMaximized()
        self._apply_blur()
        QApplication.processEvents()  # Ensure window is rendered before PIN dialog

        # PIN check with blurred background
        if not self._ensure_pin():
            self.close()
            return

        self.authenticated = True
        self._remove_blur()

        # Prompt user to enroll voice profile after successful unlock
        QTimer.singleShot(700, self.prompt_voice_enrollment_if_needed)

    def _voice_prompt_marker_path(self) -> str:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        return os.path.join(base_dir, "assets", ".voice_enroll_prompt_seen")

    def _has_seen_voice_prompt(self) -> bool:
        return os.path.exists(self._voice_prompt_marker_path())

    def _mark_voice_prompt_seen(self):
        marker = self._voice_prompt_marker_path()
        try:
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            with open(marker, "w", encoding="utf-8") as f:
                f.write("seen\n")
        except Exception as e:
            print(f"[GUI] Failed to persist voice prompt state: {e}")
    
    def get_styles(self):
        """Modern Dark MILO UI Theme - PyQt Stylesheet"""
        return """
/* ================= MAIN ================= */
QMainWindow, QWidget {
    background-color: #0F172A;
    color: #E5E7EB;
    font-family: Segoe UI, Inter, Arial;
}

QLabel {
    background-color: transparent;
}

QTabWidget::pane {
    border: none;
    top: 0px;
}

/* ================= TABS ================= */
QTabBar::tab {
    background-color: transparent;
    color: #94A3B8;
    padding: 10px 18px;
    margin-right: 2px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 14px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: transparent;
    color: #38BDF8;
    border-bottom: 2px solid #38BDF8;
    font-weight: 600;
}

QTabBar::tab:hover {
    color: #CBD5E1;
}

QPushButton#headerLink {
    background-color: transparent;
    border: none;
    color: #94A3B8;
    font-size: 15px;
    font-weight: 500;
    padding: 6px 4px;
}

QPushButton#headerLink:hover {
    color: #CBD5E1;
}

QLabel#headerBrand {
    color: #F8FAFC;
    font-size: 36px;
    font-weight: 700;
}

QLabel#headerSub {
    color: #94A3B8;
    font-size: 15px;
}

QLabel#statusReady {
    background-color: transparent;
    color: #34D399;
    border: none;
    padding: 0;
    font-size: 15px;
    font-weight: 600;
}

QLabel#statusListening {
    background-color: transparent;
    color: #38BDF8;
    border: none;
    padding: 0;
    font-size: 15px;
    font-weight: 600;
}

QLabel#statusError {
    background-color: transparent;
    color: #FB7185;
    border: none;
    padding: 0;
    font-size: 15px;
    font-weight: 600;
}

/* ================= CARDS ================= */
QFrame#card {
    background-color: #1E293B;
    border: 1px solid #1F2937;
    border-radius: 8px;
    padding: 16px;
}

QFrame#card:hover {
    border: 1px solid #374151;
}

QFrame#panelCard {
    background-color: #1E293B;
    border: 1px solid #1F2937;
    border-radius: 8px;
}

QFrame#panelCard:hover {
    border: 1px solid #374151;
}

QFrame#panelHeader {
    background-color: transparent;
    border: none;
    border-bottom: 1px solid #334155;
}

/* ================= TITLES ================= */
QLabel#sectionTitle {
    font-size: 16px;
    font-weight: 600;
    color: #E5E7EB;
    background-color: transparent;
}

QLabel#cardTitle {
    font-size: 18px;
    font-weight: 500;
    color: #94A3B8;
    background-color: transparent;
}

QLabel#value {
    font-size: 28px;
    font-weight: 700;
    color: #E5E7EB;
}

QLabel#tasksValue {
    color: #38BDF8;
    font-size: 56px;
    font-weight: 700;
}

QLabel#balanceValue {
    color: #34D399;
    font-size: 56px;
    font-weight: 700;
}

QLabel#habitsValue {
    color: #F59E0B;
    font-size: 56px;
    font-weight: 700;
}

QLabel#panelBody {
    color: #D1D5DB;
    font-size: 18px;
    padding: 24px;
    background-color: transparent;
    border: none;
    line-height: 1.6;
}

QLabel#panelBodyTerminal {
    color: #D1D5DB;
    font-size: 18px;
    padding: 24px;
    background-color: #0B1120;
    border: none;
    font-family: Consolas, "Courier New", monospace;
    line-height: 1.6;
}

/* ================= KPI COLORS ================= */
QLabel#tasks { color: #3B82F6; }
QLabel#balance { color: #22C55E; }
QLabel#habits { color: #F59E0B; }

/* ================= PANELS ================= */
QTextEdit, QPlainTextEdit {
    background-color: #0F172A;
    border: 1px solid #1F2937;
    border-radius: 10px;
    padding: 8px;
    color: #D1D5DB;
    font-size: 13px;
}

QLineEdit, QComboBox, QDateEdit, QTimeEdit {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 8px 10px;
    color: #E5E7EB;
    font-size: 14px;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus {
    border: 2px solid #3B82F6;
}

QLineEdit#footerInput {
    background-color: transparent;
    border: none;
    color: #F8FAFC;
    font-size: 17px;
}

QPushButton#footerSend {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 15px;
    font-weight: 700;
}

QPushButton#footerSend:hover {
    background-color: #334155;
}

/* ================= BUTTONS ================= */
QPushButton {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 8px 14px;
    color: #E5E7EB;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #374151;
    border-color: #4B5563;
}

QPushButton#primary {
    background-color: #3B82F6;
    border: none;
    color: white;
    font-weight: 600;
    padding: 10px 16px;
}

QPushButton#primary:hover {
    background-color: #2563EB;
}

QPushButton#success {
    background-color: #22C55E;
    border: none;
    color: white;
    font-weight: 600;
}

QPushButton#success:hover {
    background-color: #16A34A;
}

QPushButton#danger {
    background-color: #EF4444;
    border: none;
    color: white;
    font-weight: 600;
}

QPushButton#danger:hover {
    background-color: #DC2626;
}

/* ================= TABLES ================= */
QTableWidget {
    background-color: #0F172A;
    alternate-background-color: #111C33;
    gridline-color: #1F2937;
    border: 1px solid #1F2937;
    border-radius: 8px;
    color: #D1D5DB;
    font-size: 16px;
    selection-background-color: #1D4ED8;
    selection-color: #FFFFFF;
}

QTableWidget::item {
    background-color: transparent;
    padding: 12px 12px;
    border-bottom: 1px solid #1F2937;
    color: #D1D5DB;
}

QTableWidget::item:selected {
    background-color: #1D4ED8;
    color: #FFFFFF;
}

QTableWidget::item:hover {
    background-color: #1E293B;
}

QHeaderView::section {
    background-color: #18253B;
    color: #B8C3D6;
    padding: 12px 10px;
    border: none;
    border-bottom: 2px solid #374151;
    font-weight: 600;
    font-size: 14px;
}

QTableCornerButton::section {
    background-color: #18253B;
    border: none;
    border-bottom: 2px solid #374151;
}

/* ================= PROGRESS BAR ================= */
QProgressBar {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 6px;
    text-align: center;
    color: #E5E7EB;
}

QProgressBar::chunk {
    background-color: #3B82F6;
    border-radius: 4px;
}

/* ================= SCROLLBAR ================= */
QScrollBar:vertical {
    background-color: #0F172A;
    width: 8px;
}

QScrollBar::handle:vertical {
    background-color: #374151;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4B5563;
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
        self.tabs.setDocumentMode(True)
        main_layout.addWidget(self.tabs)
        
        # Create modular tabs
        self.dashboard_tab = DashboardTab(self.assistant, self.tts, self)
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        
        self.tasks_tab = TasksTab(self.assistant, self.tts, self)
        self.tabs.addTab(self.tasks_tab, "Tasks")
        
        self.finances_tab = FinancesTab(self.assistant, self.tts, self)
        self.tabs.addTab(self.finances_tab, "Finances")
        
        self.habits_tab = HabitsTab(self.assistant, self.tts, self)
        self.tabs.addTab(self.habits_tab, "Habits")
        
        self.reminders_tab = RemindersTab(self.assistant, self.tts, self)
        self.tabs.addTab(self.reminders_tab, "Reminders")
        
        # Footer
        footer = self.create_footer()
        main_layout.addWidget(footer)
    
    def create_header(self):
        """Create header with controls"""
        header = QFrame()
        header.setStyleSheet("background-color: #0B132B; border-bottom: 1px solid #1F2937;")
        header.setMaximumHeight(50)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(22, 8, 22, 8)
        layout.setSpacing(14)
        
        title = QLabel("🤖 MILO")
        title.setObjectName("headerBrand")
        layout.addWidget(title)
        
        subtitle = QLabel("Managing Information & Lifestyle Optimizer")
        subtitle.setObjectName("headerSub")
        layout.addWidget(subtitle)
        
        layout.addStretch()
        
        self.listen_btn = QPushButton("🎙 Start Listening")
        self.listen_btn.setObjectName("headerLink")
        self.listen_btn.clicked.connect(self.toggle_voice)
        layout.addWidget(self.listen_btn)
        
        help_btn = QPushButton("❔ Help")
        help_btn.setObjectName("headerLink")
        help_btn.clicked.connect(self.show_commands_help)
        layout.addWidget(help_btn)
        
        calibrate_btn = QPushButton("⚙ Calibrate")
        calibrate_btn.setObjectName("headerLink")
        calibrate_btn.clicked.connect(self.calibrate_voice)
        layout.addWidget(calibrate_btn)

        enroll_btn = QPushButton("👆 Enroll Voice")
        enroll_btn.setObjectName("headerLink")
        enroll_btn.clicked.connect(self.enroll_voice_profile)
        layout.addWidget(enroll_btn)
        
        self.status_label = QLabel("✔ Ready")
        self.status_label.setObjectName("statusReady")
        layout.addWidget(self.status_label)
        
        return header
    
    def create_footer(self):
        """Create footer with message area and input"""
        footer = QFrame()
        footer.setStyleSheet("background-color: #111827; border-top: 1px solid #1F2937;")
        footer.setMaximumHeight(72)
        
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(22, 10, 22, 10)
        layout.setSpacing(0)

        self.message_area = QTextEdit()
        self.message_area.hide()

        input_wrap = QFrame()
        input_wrap.setStyleSheet("QFrame { background-color: #0B1120; border: 1px solid #334155; border-radius: 8px; }")
        input_layout = QHBoxLayout(input_wrap)
        input_layout.setContentsMargins(12, 6, 8, 6)
        input_layout.setSpacing(10)

        icon_label = QLabel("〉_")
        icon_label.setStyleSheet("color: #94A3B8; font-weight: 600;")
        input_layout.addWidget(icon_label)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask MILO anything...")
        self.input_field.setObjectName("footerInput")
        self.input_field.returnPressed.connect(self.process_input)
        input_layout.addWidget(self.input_field)
        
        send_btn = QPushButton("➤ Send")
        send_btn.setObjectName("footerSend")
        send_btn.clicked.connect(self.process_input)
        input_layout.addWidget(send_btn)
        
        layout.addWidget(input_wrap)
        
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
            self.listen_btn.setText("◼ Stop Listening")
            self.status_label.setObjectName("statusListening")
            self.status_label.setText("🎙 Starting...")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
            
            # Try to start listening
            success = self.voice_recognizer.start_listening(self.voice_callback)
            
            if success:
                self.status_label.setObjectName("statusListening")
                self.status_label.setText("🎙 Listening...")
                self.status_label.style().unpolish(self.status_label)
                self.status_label.style().polish(self.status_label)
            else:
                # Failed to start
                self.is_listening = False
                self.listen_btn.setText("🎙 Start Listening")
                self.status_label.setObjectName("statusError")
                self.status_label.setText("✖ Microphone Error")
                self.status_label.style().unpolish(self.status_label)
                self.status_label.style().polish(self.status_label)
                QMessageBox.critical(
                    self,
                    "Microphone Error",
                    "Could not access microphone.\n\n"
                    "Please check:\n"
                    "• Microphone is connected\n"
                    "• No other app is using it\n"
                    "• Audio drivers are working\n\n"
                    "Check terminal output for details."
                )
        else:
            self.listen_btn.setText("🎙 Start Listening")
            self.status_label.setObjectName("statusReady")
            self.status_label.setText("✔ Ready")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
            if self.voice_recognizer:
                self.voice_recognizer.stop_listening()
    
    def voice_callback(self, text: str):
        """Callback from voice recognition thread - emits signal to main thread"""
        if text and text.strip():  # Only process non-empty text
            self.voice_emitter.voice_command_detected.emit(text)
    
    def handle_voice_command(self, text: str):
        """Handle voice command (runs in main thread via signal)"""
        if not text or not text.strip():
            return
        
        # Update UI immediately to show we heard something
        self.update_status(f"🗣️ Processing: {text[:50]}...")
        print(f"[Voice] Transcribed: '{text}'")  # Debug log
        
        try:
            command = self.voice_recognizer.detect_command(text)
            
            if command:
                command_id, matched_phrase, confidence = command
                print(f"[Voice] Matched command: {command_id} ('{matched_phrase}') with confidence {confidence}%")  # Debug log
                self.update_status(f"✅ Command: {matched_phrase} ({confidence:.0f}%)")
                
                if command_id == "ADD_TASK":
                    # If spoken text already contains details, execute directly.
                    response = self.assistant.process_command(text)
                    if response.get("intent") == "create_task" and response.get("success"):
                        message = response.get("message", "Task added.")
                        self.message_area.setText(message)
                        self.tabs.setCurrentIndex(1)
                        self.log_command(text, message, "voice")
                        self.refresh_all()
                    else:
                        self.add_task_dialog()
                        self.log_command(text, "Opening add task dialog", "voice")
                elif command_id == "ADD_EXPENSE":
                    response = self.assistant.process_command(text)
                    if response.get("intent") == "add_expense" and response.get("success"):
                        message = response.get("message", "Expense added.")
                        self.message_area.setText(message)
                        self.tabs.setCurrentIndex(2)
                        self.log_command(text, message, "voice")
                        self.refresh_all()
                    else:
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
                        self.tts.speak(response, wait=False)
                        self.log_command(text, response, "voice")
                elif command_id == "REFRESH":
                    self.refresh_all()
                    self.update_status("✅ Refreshed")
                    self.log_command(text, "Dashboard refreshed", "voice")
                elif command_id == "NEXT_SLIDE":
                    res = self.assistant.rpa.next_slide()
                    self.update_status(f"✅ {res}")
                    self.tts.speak(res, wait=False)
                elif command_id == "PREV_SLIDE":
                    res = self.assistant.rpa.prev_slide()
                    self.update_status(f"✅ {res}")
                    self.tts.speak(res, wait=False)
                elif command_id == "OPEN_APP":
                    # Let NLP handle the extraction of app name for complex patterns
                    self.process_voice_text(text)
                elif command_id == "GOOGLE_SEARCH":
                    # Direct search trigger
                    self.update_status("🔍 Searching...")
                    self.process_voice_text(text)
                elif command_id == "WAKE_WORD":
                    import re
                    remainder = re.sub(r"\b(?:hey|hello|hi)?\s*milo\b", "", text, flags=re.IGNORECASE)
                    remainder = re.sub(r"\s+", " ", remainder).strip(" ,.!?-")

                    if remainder and len(remainder) >= 3:
                        print(f"[Voice] Wake word + command detected. Remaining text: '{remainder}'")
                        self.update_status("👂 MILO heard command after wake word...")
                        self.process_voice_text(remainder)
                    else:
                        self.update_status("👂 MILO listening...")
                        self.tts.speak("Yes, I'm listening", wait=False)
                        self.log_command(text, "MILO activated and listening", "voice")
                else:
                    self.process_voice_text(text)
            else:
                print(f"[Voice] No command match. Sending to NLP parser...")  # Debug log
                self.process_voice_text(text)
                
            # Reset status after processing
            QTimer.singleShot(3000, lambda: self.update_status("🎤 Listening..."))
            
        except Exception as e:
            error_msg = f"Voice command error: {str(e)}"
            self.handle_voice_error(error_msg)
            self.log_command(text, error_msg, "voice")
    
    def process_voice_text(self, text: str):
        """Process voice text through assistant"""
        self.message_area.setText(f"Processing: {text}...")
        try:
            response = self.assistant.process_command(text)
            print(f"[Assistant] Intent: {response.get('intent')}, Success: {response.get('success')}")  # Debug log
            message = response.get('message', 'Done')
            self.message_area.setText(message)
            
            self.log_command(text, message, "voice")
            self.refresh_all()
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"[Assistant] Error: {e}")  # Debug log
            import traceback
            print(f"[Assistant] Traceback: {traceback.format_exc()}")
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

    def enroll_voice_profile(self):
        """Enroll speaker profile for voice biometrics"""
        if not self.voice_recognizer or not self.voice_recognizer.is_available():
            QMessageBox.warning(self, "Voice Recognition", "Voice recognition is not available.")
            return

        QMessageBox.information(self, "Voice Enrollment", "You will be asked to speak a few short phrases.")

        progress_dialog = QProgressDialog("Preparing voice enrollment...", None, 0, 100, self)
        progress_dialog.setWindowTitle("Voice Enrollment")
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setAutoClose(False)
        progress_dialog.setAutoReset(False)
        progress_dialog.setValue(0)
        progress_dialog.show()
        QApplication.processEvents()

        def update_enrollment_progress(sample_idx: int, sample_total: int, percent: float):
            bounded_value = max(0.0, min(100.0, float(percent)))
            bounded_bar = int(round(bounded_value))
            progress_dialog.setLabelText(
                f"Enrollment sample {sample_idx}/{sample_total} - please speak...\n"
                f"Progress reached: {bounded_value:.1f}%"
            )
            progress_dialog.setValue(bounded_bar)
            QApplication.processEvents()

        self.status_label.setText("🎙️ Enrolling voice...")
        ok, message = self.voice_recognizer.enroll_speaker_profile(
            samples=5,
            progress_callback=update_enrollment_progress,
        )
        progress_dialog.close()

        if ok:
            self.status_label.setText("✅ Voice profile enrolled")
            QMessageBox.information(self, "Voice Enrollment", message)
        else:
            self.status_label.setText("❌ Voice enrollment failed")
            QMessageBox.warning(self, "Voice Enrollment", message)

    def prompt_voice_enrollment_if_needed(self):
        """Ask user to enroll voice profile if biometrics is available and not enrolled yet."""
        try:
            if self._has_seen_voice_prompt():
                return

            if not self.voice_recognizer:
                return

            biometrics = getattr(self.voice_recognizer, "voice_biometrics", None)
            if not biometrics or not biometrics.is_available() or biometrics.has_profile():
                return

            self._mark_voice_prompt_seen()

            choice = QMessageBox.question(
                self,
                "Voice Enrollment",
                "No voice profile is enrolled yet.\n\nDo you want to enroll your voice now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if choice == QMessageBox.Yes:
                self.enroll_voice_profile()
        except Exception as e:
            print(f"[GUI] Voice enrollment prompt skipped: {e}")

    def _ensure_pin(self) -> bool:
        """Prompt for PIN and trigger intruder capture on repeated failure"""
        if not self.pin_manager.has_pin():
            QMessageBox.information(self, "Set PIN", "Create a new PIN to secure MILO.")
            while True:
                pin = self._prompt_pin("Set PIN", "Enter a new PIN (4-10 digits):")
                if pin is None:
                    return False
                if not self._is_valid_pin(pin):
                    QMessageBox.warning(self, "Invalid PIN", "PIN must be 4-10 digits.")
                    continue

                confirm = self._prompt_pin("Confirm PIN", "Re-enter your PIN:")
                if confirm is None:
                    return False
                if confirm != pin:
                    QMessageBox.warning(self, "PIN Mismatch", "PINs do not match. Try again.")
                    continue

                self.pin_manager.set_pin(pin)
                return True

        for attempt in range(1, 4):
            pin = self._prompt_pin("Unlock MILO", f"Enter PIN (attempt {attempt} of 3):")
            if pin is None:
                return False
            if self.pin_manager.verify_pin(pin):
                return True

        capture_intruder()
        QMessageBox.critical(self, "Access Denied", "Too many failed attempts.")
        return False

    def _prompt_pin(self, title: str, label: str) -> str:
        pin, ok = QInputDialog.getText(self, title, label, QLineEdit.Password)
        return pin if ok else None
    
    def _apply_blur(self):
        """Apply blur effect to the central widget"""
        try:
            blur_effect = QGraphicsBlurEffect()
            blur_effect.setBlurRadius(15)
            self.centralWidget().setGraphicsEffect(blur_effect)
        except Exception as e:
            print(f"[GUI] Failed to apply blur: {e}")
    
    def _remove_blur(self):
        """Remove blur effect from the central widget"""
        try:
            self.centralWidget().setGraphicsEffect(None)
        except Exception as e:
            print(f"[GUI] Failed to remove blur: {e}")

    def _is_valid_pin(self, pin: str) -> bool:
        return pin.isdigit() and 4 <= len(pin) <= 10
    
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
            
            self.log_command(text, response_msg, "text")
            self.refresh_all()
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.message_area.setText(error_msg)
            self.log_command(text, error_msg, "text")
    
    def refresh_all(self):
        """Refresh all data"""
        if getattr(self, '_is_closing', False):
            return
            
        try:
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
        except Exception as e:
            if not getattr(self, '_is_closing', False):
                print(f"[GUI] Refresh error: {e}")

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
            # Use the assistant's dashboard data which now includes ML recommendations
            dashboard_data = self.assistant.get_dashboard_data()
            ml_rec = dashboard_data.get('ml_recommendation', {})
            upcoming_tasks = dashboard_data.get('upcoming_tasks', [])
            habits = dashboard_data.get('habits', [])
            
            # Need logged_today for habit summary
            habit_ids = [h.get('id') for h in habits if h.get('id') is not None]
            logged_today = self.assistant.habit_manager.get_logged_today_ids(habit_ids)
            
            if self.dashboard_tab:
                # Update KPI labels
                self.dashboard_tab.tasks_value_label.setText(str(dashboard_data['pending_tasks_count']))
                self.dashboard_tab.balance_value_label.setText(f"₹{dashboard_data['balance']:,.2f}")
                self.dashboard_tab.habits_value_label.setText(str(len(habits)))
                
                # Update AI Insights with ML recommendation
                rule_suggestions = dashboard_data.get('suggestions', [])
                insights_parts = []
                
                if ml_rec and ml_rec.get('confidence', 0) > 0:
                    rec = ml_rec['suggestion']
                    conf = ml_rec['confidence']
                    now = datetime.datetime.now()
                    time_str = now.strftime("%I:%M %p")
                    tasks_count = dashboard_data['pending_tasks_count']
                    
                    greeting = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 17 else "Good evening"
                    ml_msg = (
                        f"✨ <b>{greeting}</b>. It's {time_str} and you have {tasks_count} tasks pending. "
                        f"Based on your routine, there is a <b>{conf}%</b> chance you want to <b>{rec}</b>. "
                        f"Should I help you with that?"
                    )
                    insights_parts.append(ml_msg)
                
                if rule_suggestions:
                    for sug in rule_suggestions[:2]:
                        insights_parts.append(f"💡 {sug}")
                
                if not insights_parts:
                    insights_text = "💡 No insights available yet. Keep using MILO to generate patterns!"
                else:
                    insights_text = "<br><br>".join(insights_parts)
                
                self.dashboard_tab.update_insights(insights_text)

                # Update Upcoming Deadlines
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
        self._is_closing = True
        
        # Stop timers first to prevent background tasks using closed connection
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
            
        if self.voice_recognizer:
            self.voice_recognizer.cleanup()
        if self.tts:
            self.tts.shutdown()
        if self.db:
            try:
                self.db.close()
            except Exception as e:
                print(f"[GUI] Error closing database: {e}")
        event.accept()


def main():
    app = __import__('PyQt5.QtWidgets', fromlist=['QApplication']).QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
