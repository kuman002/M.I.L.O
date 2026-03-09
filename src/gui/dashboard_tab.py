"""
Dashboard Tab for MILO - Responsive Modern Design
Displays overview metrics, voice command boxes, and AI insights with responsive grid layout
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
from gui.base_tab import BaseTab
from gui.responsive_grid import ResponsiveGrid


class DashboardTab(BaseTab):
    """Dashboard tab showing overview of all MILO features with responsive layout"""
    
    def setup_ui(self):
        """Build the responsive dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        
        # ===== KPI CARDS GRID (Responsive 3 → 2 → 1 columns) =====
        kpi_grid = ResponsiveGrid(min_card_width=260, max_columns=3)
        
        # Create KPI cards with stored references
        task_card, self.tasks_value_label = self._create_kpi_card("Pending Tasks", "0", "📋", "tasks", "#38BDF8")
        balance_card, self.balance_value_label = self._create_kpi_card("Balance", "₹0.00", "💰", "balance", "#34D399")
        habits_card, self.habits_value_label = self._create_kpi_card("Active Habits", "0", "📈", "habits", "#F59E0B")
        
        kpi_grid.add_cards(task_card, balance_card, habits_card)
        layout.addWidget(kpi_grid)
        
        # ===== TOP SECTION ROW (2 columns) =====
        top_section_grid = ResponsiveGrid(min_card_width=500, max_columns=2)
        
        # Last Command Box
        self.last_command_card, self.last_command_display = self._create_section_card(
            "Last Command",
            "> Waiting for user input...",
            "⌨️",
            "#94A3B8",
            variant="terminal",
            is_terminal=True,
        )
        top_section_grid.add_card(self.last_command_card)

        # MILO's Reply Box
        self.reply_card, self.milo_reply_display = self._create_section_card(
            "MILO's Reply",
            "Ready to assist. All systems are online.",
            "💬",
            "#34D399",
            variant="reply",
        )
        top_section_grid.add_card(self.reply_card)

        layout.addWidget(top_section_grid)

        # ===== BOTTOM SECTION ROW (2 columns) =====
        bottom_section_grid = ResponsiveGrid(min_card_width=500, max_columns=2)
        
        # Upcoming Deadlines
        self.upcoming_card, self.upcoming_label = self._create_section_card(
            "Upcoming Deadlines",
            "No upcoming tasks detected.",
            "✅",
            "#84CC16",
            variant="upcoming",
        )
        bottom_section_grid.add_card(self.upcoming_card)
        
        # AI Insights
        self.insights_card, self.insights_label = self._create_section_card(
            "AI Insights",
            "Analyzing recent activity...",
            "✨",
            "#A855F7",
            variant="insights",
        )
        bottom_section_grid.add_card(self.insights_card)

        layout.addWidget(bottom_section_grid)
    
    def _create_kpi_card(self, title_text, value_text, icon_text, metric_key, accent_color):
        """
        Create a KPI metric card with title and value
        
        Args:
            title_text: Card title (e.g., "📋 Pending Tasks")
            value_text: Initial value to display
            intent_type: Intent type for styling (tasks, balance, habits)
            
        Returns:
            Tuple of (card_widget, value_label)
        """
        card = QFrame()
        card.setObjectName("card")

        bg_map = {
            "tasks": ("rgba(39, 75, 148, 238)", "rgba(27, 46, 84, 232)"),
            "balance": ("rgba(42, 108, 84, 238)", "rgba(27, 62, 56, 232)"),
            "habits": ("rgba(156, 96, 38, 238)", "rgba(88, 52, 23, 232)"),
        }
        bg_stop_1, bg_stop_2 = bg_map.get(metric_key, ("rgba(30, 41, 59, 240)", "rgba(15, 23, 42, 235)"))

        card.setStyleSheet(
            f"""
            QFrame#card {{
                border-top: 3px solid {accent_color};
                border-radius: 10px;
                border: 1px solid rgba(148, 163, 184, 0.35);
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg_stop_1},
                    stop:1 {bg_stop_2});
            }}
            """
        )
        card.setMinimumHeight(112)
        card.setMaximumHeight(170)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 18)
        layout.setSpacing(8)
        
        # Title first (top)
        title_label = QLabel(f"{icon_text}  {title_text}")
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label)
        
        # Value second (bottom) - using CSS styling (56px)
        value_label = QLabel(value_text)
        value_label.setObjectName(f"{metric_key}Value")
        layout.addWidget(value_label)
        
        layout.addStretch()
        
        # Add shadow effect for elevation
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 64))  # rgba(0,0,0,0.25)
        card.setGraphicsEffect(shadow)
        
        return card, value_label
    
    def _create_section_card(self, title_text, placeholder_text, icon_text, accent_color, variant="default", is_terminal=False):
        """
        Create a section card with custom header and content body
        
        Args:
            title_text: Card title
            placeholder_text: Initial placeholder text
            
        Returns:
            Tuple of (card_widget, content_widget)
        """
        card = QFrame()
        card.setObjectName("panelCard")

        bg_stop_1 = "rgba(30, 41, 59, 238)"
        bg_stop_2 = "rgba(15, 23, 42, 228)"
        min_height = 180

        if variant == "terminal":
            bg_stop_1 = "rgba(26, 36, 56, 240)"
            bg_stop_2 = "rgba(9, 16, 36, 232)"
            min_height = 180
        elif variant == "upcoming":
            bg_stop_1 = "rgba(34, 56, 52, 236)"
            bg_stop_2 = "rgba(20, 34, 50, 230)"
            min_height = 180
        elif variant == "reply":
            bg_stop_1 = "rgba(34, 46, 66, 236)"
            bg_stop_2 = "rgba(19, 31, 49, 230)"
            min_height = 170
        elif variant == "insights":
            bg_stop_1 = "rgba(48, 40, 74, 236)"
            bg_stop_2 = "rgba(26, 25, 52, 228)"
            min_height = 170

        card.setStyleSheet(
            f"""
            QFrame#panelCard {{
                border-left: 3px solid {accent_color};
                border-radius: 10px;
                border: 1px solid rgba(148, 163, 184, 0.30);
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg_stop_1},
                    stop:1 {bg_stop_2});
            }}
            """
        )
        card.setMinimumHeight(min_height)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("panelHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(0)
        
        title_label = QLabel(f"{icon_text}  {title_text}")
        title_label.setObjectName("sectionTitle")
        header_layout.addWidget(title_label)
        layout.addWidget(header)
        
        content = QLabel(placeholder_text)
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content.setObjectName("panelBodyTerminal" if is_terminal else "panelBody")
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if is_terminal:
            content.setStyleSheet("background-color: transparent;")
        layout.addWidget(content)
        
        # Add shadow effect for elevation
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 64))  # rgba(0,0,0,0.25)
        card.setGraphicsEffect(shadow)
        
        return card, content

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
        self.insights_label.setText(insights_text)

    def update_upcoming(self, upcoming_text: str):
        """Update upcoming deadlines text"""
        self.upcoming_label.setText(upcoming_text)

    def update_metric(self, metric_name, value):
        """Update a specific KPI metric"""
        if metric_name == "tasks":
            self.tasks_value_label.setText(str(value))
        elif metric_name == "balance":
            self.balance_value_label.setText(str(value))
        elif metric_name == "habits":
            self.habits_value_label.setText(str(value))

