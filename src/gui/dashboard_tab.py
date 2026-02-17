"""
Dashboard Tab for MILO
Displays overview metrics, voice command boxes, and AI insights
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QFrame
)
from PyQt5.QtGui import QFont
from gui.base_tab import BaseTab


class DashboardTab(BaseTab):
    """Dashboard tab showing overview of all MILO features"""
    
    def setup_ui(self):
        """Build the dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Metrics row
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(20)
        
        # Task card - store reference to value label
        task_card, self.tasks_value_label = self.create_metric_card("📋 Pending Tasks", "0", "#2ecc71")
        metrics_layout.addWidget(task_card)
        
        # Balance card - store reference to value label
        balance_card, self.balance_value_label = self.create_metric_card("💰 Balance", "₹0.00", "#3498db")
        metrics_layout.addWidget(balance_card)
        
        # Habits card - store reference to value label
        habits_card, self.habits_value_label = self.create_metric_card("🎯 Active Habits", "0", "#e74c3c")
        metrics_layout.addWidget(habits_card)
        
        layout.addLayout(metrics_layout)
        
        # Command & Reply Section
        command_reply_layout = QHBoxLayout()
        command_reply_layout.setSpacing(15)
        
        # Last Command Box
        command_group = QFrame()
        command_group.setStyleSheet("""
            QFrame {
                background-color: #252c3c;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        command_layout = QVBoxLayout(command_group)
        command_title = QLabel("🎤 Last Command")
        command_title.setFont(QFont("Arial", 11, QFont.Bold))
        command_layout.addWidget(command_title)
        
        self.last_command_display = QTextEdit()
        self.last_command_display.setReadOnly(True)
        self.last_command_display.setMaximumHeight(120)
        self.last_command_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1f2e;
                color: #3b82f6;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self.last_command_display.setText("No command yet...")
        command_layout.addWidget(self.last_command_display)
        
        command_reply_layout.addWidget(command_group, 1)
        
        # MILO's Reply Box
        reply_group = QFrame()
        reply_group.setStyleSheet("""
            QFrame {
                background-color: #252c3c;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        reply_layout = QVBoxLayout(reply_group)
        reply_title = QLabel("💬 MILO's Reply")
        reply_title.setFont(QFont("Arial", 11, QFont.Bold))
        reply_layout.addWidget(reply_title)
        
        self.milo_reply_display = QTextEdit()
        self.milo_reply_display.setReadOnly(True)
        self.milo_reply_display.setMaximumHeight(120)
        self.milo_reply_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1f2e;
                color: #10b981;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self.milo_reply_display.setText("Ready to assist...")
        reply_layout.addWidget(self.milo_reply_display)
        
        command_reply_layout.addWidget(reply_group, 1)
        
        layout.addLayout(command_reply_layout)
        
        # Info sections
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)
        
        # Upcoming deadlines
        upcoming_group = QFrame()
        upcoming_group.setStyleSheet("""
            QFrame {
                background-color: #252c3c;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        upcoming_layout = QVBoxLayout(upcoming_group)
        upcoming_title = QLabel("📅 Upcoming Deadlines")
        upcoming_title.setFont(QFont("Arial", 11, QFont.Bold))
        upcoming_layout.addWidget(upcoming_title)
        self.upcoming_label = QLabel("📌 No upcoming tasks yet.")
        self.upcoming_label.setWordWrap(True)
        self.upcoming_label.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        upcoming_layout.addWidget(self.upcoming_label)
        upcoming_layout.addStretch()
        info_layout.addWidget(upcoming_group)
        
        # AI Insights
        insights_group = QFrame()
        insights_group.setStyleSheet("""
            QFrame {
                background-color: #252c3c;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        insights_layout = QVBoxLayout(insights_group)
        insights_title = QLabel("✨ AI Insights")
        insights_title.setFont(QFont("Arial", 11, QFont.Bold))
        insights_layout.addWidget(insights_title)
        self.insights_label = QLabel("💡 Loading insights...")
        self.insights_label.setWordWrap(True)
        self.insights_label.setStyleSheet("color: #e2e8f0; font-size: 13px;")
        insights_layout.addWidget(self.insights_label)
        insights_layout.addStretch()
        info_layout.addWidget(insights_group)
        
        layout.addLayout(info_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh Dashboard")
        refresh_btn.clicked.connect(self.refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)
        
        layout.addStretch()
    
    def create_metric_card(self, title, value, color):
        """Create a metric card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}22;
                border: 1px solid {color};
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #999999; font-size: 12px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        layout.addStretch()
        
        return card, value_label  # Return both card and label for updates
    
    def refresh(self):
        """Refresh dashboard metrics"""
        if self.parent_window:
            self.parent_window.update_dashboard_metrics()
    
    def update_command_display(self, command):
        """Update the last command display"""
        self.last_command_display.setText(command)
    
    def update_reply_display(self, reply):
        """Update MILO's reply display"""
        self.milo_reply_display.setText(reply)

    def update_insights(self, insights_text: str):
        """Update AI insights text"""
        if self.insights_label:
            self.insights_label.setText(insights_text)

    def update_upcoming(self, upcoming_text: str):
        """Update upcoming deadlines text"""
        if self.upcoming_label:
            self.upcoming_label.setText(upcoming_text)
