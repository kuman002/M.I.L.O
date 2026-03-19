"""
Dashboard Tab for MILO - Responsive Modern Design
Displays overview metrics, voice command boxes, and AI insights with responsive grid layout
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from gui.base_tab import BaseTab
from gui.responsive_grid import ResponsiveGrid


class DashboardTab(BaseTab):
    """Dashboard tab showing overview of all MILO features with responsive layout"""

    def setup_ui(self):
        """Build the responsive dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ===== DASHBOARD HEADER =====
        self._dash_header_frame = self._create_header()
        layout.addWidget(self._dash_header_frame)

        # ===== KPI CARDS GRID (Responsive 3 -> 2 -> 1 columns) =====
        kpi_grid = ResponsiveGrid(min_card_width=260, max_columns=3)

        task_card, self.tasks_value_label = self._create_kpi_card("Pending Tasks", "0", "📋", "tasks", "#38BDF8")
        balance_card, self.balance_value_label = self._create_kpi_card("Balance", "₹0.00", "💰", "balance", "#34D399")
        habits_card, self.habits_value_label = self._create_kpi_card("Active Habits", "0", "📈", "habits", "#FBBF24")
        self._all_kpi_cards = [task_card, balance_card, habits_card]

        kpi_grid.add_cards(task_card, balance_card, habits_card)
        layout.addWidget(kpi_grid)

        # ===== TOP SECTION ROW (2 columns) =====
        top_section_grid = ResponsiveGrid(min_card_width=500, max_columns=2)

        self.last_command_card, self.last_command_display = self._create_section_card(
            "Last Command",
            "> Waiting for user input...",
            "⌨️",
            "#94A3B8",
            variant="terminal",
            is_terminal=True,
        )
        top_section_grid.add_card(self.last_command_card)

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

        self.upcoming_card, self.upcoming_label = self._create_section_card(
            "Upcoming Deadlines",
            "No upcoming tasks detected.",
            "✅",
            "#84CC16",
            variant="upcoming",
        )
        bottom_section_grid.add_card(self.upcoming_card)

        self.insights_card, self.insights_label = self._create_section_card(
            "AI Insights",
            "Analyzing recent activity...",
            "✨",
            "#A855F7",
            variant="insights",
        )
        bottom_section_grid.add_card(self.insights_card)

        layout.addWidget(bottom_section_grid)
        self._all_section_cards = [
            self.last_command_card,
            self.reply_card,
            self.upcoming_card,
            self.insights_card,
        ]

    def _create_header(self):
        """Create the dashboard top header banner."""
        header = QFrame()
        header.setObjectName("dashHeader")
        header.setStyleSheet(
            """
            QFrame#dashHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(59, 130, 246, 40),
                    stop:0.5 rgba(99, 102, 241, 26),
                    stop:1 rgba(15, 23, 42, 0));
                border: 1px solid rgba(99, 102, 241, 60);
                border-radius: 14px;
            }
            """
        )
        header.setMaximumHeight(72)

        h = QHBoxLayout(header)
        h.setContentsMargins(22, 12, 22, 12)
        h.setSpacing(0)

        lbl_title = QLabel("Dashboard Overview")
        lbl_title.setStyleSheet(
            "color: #F1F5F9; font-size: 26px; font-weight: 700; background: transparent;"
        )

        lbl_sub = QLabel("MILO Personal Assistant  •  All Systems Online")
        lbl_sub.setStyleSheet(
            "color: #64748B; font-size: 16px; font-weight: 500; background: transparent;"
        )
        lbl_sub.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        h.addWidget(lbl_title)
        h.addStretch()
        h.addWidget(lbl_sub)
        self._dash_header_title = lbl_title
        self._dash_header_sub = lbl_sub
        return header

    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """Return 'r, g, b, a' string (alpha 0-255) from hex and 0-1 float."""
        hx = hex_color.lstrip("#")
        r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
        return f"{r}, {g}, {b}, {int(alpha * 255)}"

    def _create_kpi_card(self, title_text, value_text, icon_text, metric_key, accent_color):
        """Create a KPI metric card with icon, title, and large value."""
        card = QFrame()
        card.setObjectName("kpiCard")

        bg_map = {
            "tasks": ("rgba(30, 58, 138, 140)", "rgba(17, 24, 62, 204)"),
            "balance": ("rgba(6, 78, 59, 140)", "rgba(12, 45, 47, 204)"),
            "habits": ("rgba(120, 53, 15, 140)", "rgba(69, 26, 3, 204)"),
        }
        bg1, bg2 = bg_map.get(metric_key, ("rgba(30, 41, 59, 140)", "rgba(15, 23, 42, 200)"))

        card.setStyleSheet(
            f"""
            QFrame#kpiCard {{
                border-top: 3px solid {accent_color};
                border-left: 1px solid rgba(148, 163, 184, 50);
                border-right: 1px solid rgba(148, 163, 184, 50);
                border-bottom: 1px solid rgba(148, 163, 184, 50);
                border-radius: 14px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg1}, stop:1 {bg2});
            }}
            """
        )
        card.setMinimumHeight(130)
        card.setMaximumHeight(175)

        v = QVBoxLayout(card)
        v.setContentsMargins(22, 16, 22, 18)
        v.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)

        icon_lbl = QLabel(icon_text)
        icon_lbl.setStyleSheet(f"color: {accent_color}; font-size: 24px; background: transparent;")
        icon_lbl.setFixedWidth(32)
        row.addWidget(icon_lbl)

        title_lbl = QLabel(title_text.upper())
        title_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 17px; font-weight: 600; background: transparent;"
        )
        row.addWidget(title_lbl)
        row.addStretch()
        v.addLayout(row)

        value_label = QLabel(value_text)
        value_label.setStyleSheet(
            f"color: {accent_color}; font-size: 48px; font-weight: 700; "
            "background: transparent; padding-top: 2px;"
        )
        v.addWidget(value_label)
        v.addStretch()

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(22)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 90))
        card.setGraphicsEffect(shadow)

        card._metric_key = metric_key
        card._accent_color = accent_color
        card._icon_lbl = icon_lbl
        card._title_lbl = title_lbl

        return card, value_label

    def _create_section_card(self, title_text, placeholder_text, icon_text, accent_color, variant="default", is_terminal=False):
        """Create a section card with an accent header and readable content body."""
        card = QFrame()
        card.setObjectName("sectionCard")

        bg_map = {
            "terminal": ("rgba(12, 20, 42, 242)", "rgba(6, 12, 28, 235)"),
            "reply": ("rgba(16, 32, 60, 240)", "rgba(8, 18, 40, 232)"),
            "upcoming": ("rgba(14, 42, 34, 240)", "rgba(8, 24, 32, 232)"),
            "insights": ("rgba(40, 26, 68, 240)", "rgba(20, 14, 48, 230)"),
            "default": ("rgba(24, 34, 52, 240)", "rgba(12, 18, 36, 232)"),
        }
        bg1, bg2 = bg_map.get(variant, bg_map["default"])

        card.setStyleSheet(
            f"""
            QFrame#sectionCard {{
                border-left: 3px solid {accent_color};
                border-top: 1px solid rgba(148, 163, 184, 45);
                border-right: 1px solid rgba(148, 163, 184, 45);
                border-bottom: 1px solid rgba(148, 163, 184, 45);
                border-radius: 14px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg1}, stop:1 {bg2});
            }}
            """
        )
        card.setMinimumHeight(185)

        v = QVBoxLayout(card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        hdr = QFrame()
        hdr.setObjectName("sectionCardHeader")
        hdr.setStyleSheet(
            f"""
            QFrame#sectionCardHeader {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({self._hex_to_rgba(accent_color, 0.20)}),
                    stop:1 rgba({self._hex_to_rgba(accent_color, 0.03)}));
                border-bottom: 1px solid rgba({self._hex_to_rgba(accent_color, 0.30)});
                border-top-left-radius: 13px;
                border-top-right-radius: 13px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
            """
        )
        hdr_row = QHBoxLayout(hdr)
        hdr_row.setContentsMargins(18, 11, 18, 11)
        hdr_row.setSpacing(10)

        icon_lbl = QLabel(icon_text)
        icon_lbl.setStyleSheet(f"color: {accent_color}; font-size: 22px; background: transparent;")
        icon_lbl.setFixedWidth(30)
        hdr_row.addWidget(icon_lbl)

        title_lbl = QLabel(title_text)
        title_lbl.setStyleSheet("color: #F1F5F9; font-size: 19px; font-weight: 700; background: transparent;")
        hdr_row.addWidget(title_lbl)
        hdr_row.addStretch()
        v.addWidget(hdr)

        content = QLabel(placeholder_text)
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if is_terminal:
            content.setStyleSheet(
                "color: #86EFAC; font-size: 20px; "
                "font-family: 'Consolas', 'Courier New', monospace; "
                "background: transparent; padding: 16px 20px;"
            )
        elif variant == "insights":
            content.setStyleSheet(
                "color: #CBD5E1; font-size: 16px; line-height: 1.6; "
                "background: transparent; padding: 14px 20px;"
            )
        else:
            content.setStyleSheet(
                "color: #CBD5E1; font-size: 18px; "
                "background: transparent; padding: 16px 20px;"
            )
        v.addWidget(content)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(22)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 90))
        card.setGraphicsEffect(shadow)

        card._variant = variant
        card._is_terminal = is_terminal
        card._accent_color = accent_color
        card._icon_lbl = icon_lbl
        card._title_lbl = title_lbl
        card._content = content
        card._hdr = hdr

        return card, content

    def apply_theme(self, dark: bool):
        """Re-style all inline-styled dashboard cards to match active theme."""

        if hasattr(self, "_dash_header_frame"):
            if dark:
                self._dash_header_frame.setStyleSheet(
                    """
                    QFrame#dashHeader {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 rgba(59, 130, 246, 40),
                            stop:0.5 rgba(99, 102, 241, 26),
                            stop:1 rgba(15, 23, 42, 0));
                        border: 1px solid rgba(99, 102, 241, 60);
                        border-radius: 14px;
                    }
                    """
                )
                self._dash_header_title.setStyleSheet("color: #F1F5F9; font-size: 26px; font-weight: 700; background: transparent;")
                self._dash_header_sub.setStyleSheet("color: #64748B; font-size: 16px; font-weight: 500; background: transparent;")
            else:
                self._dash_header_frame.setStyleSheet(
                    """
                    QFrame#dashHeader {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 rgba(59, 130, 246, 22),
                            stop:0.5 rgba(99, 102, 241, 12),
                            stop:1 rgba(241, 245, 249, 0));
                        border: 1px solid rgba(99, 102, 241, 90);
                        border-radius: 14px;
                    }
                    """
                )
                self._dash_header_title.setStyleSheet("color: #1E293B; font-size: 26px; font-weight: 700; background: transparent;")
                self._dash_header_sub.setStyleSheet("color: #64748B; font-size: 16px; font-weight: 500; background: transparent;")

        dark_kpi_bg = {
            "tasks": ("rgba(30, 58, 138, 140)", "rgba(17, 24, 62, 204)"),
            "balance": ("rgba(6, 78, 59, 140)", "rgba(12, 45, 47, 204)"),
            "habits": ("rgba(120, 53, 15, 140)", "rgba(69, 26, 3, 204)"),
        }
        light_kpi_bg = {
            "tasks": ("rgba(219, 234, 254, 220)", "rgba(239, 246, 255, 245)"),
            "balance": ("rgba(220, 252, 231, 220)", "rgba(240, 253, 244, 245)"),
            "habits": ("rgba(254, 243, 199, 220)", "rgba(255, 251, 235, 245)"),
        }
        title_color = "#94A3B8" if dark else "#475569"

        for card in getattr(self, "_all_kpi_cards", []):
            key = getattr(card, "_metric_key", "tasks")
            accent = getattr(card, "_accent_color", "#38BDF8")
            bg_map = dark_kpi_bg if dark else light_kpi_bg
            fallback = ("rgba(30, 41, 59, 140)", "rgba(15, 23, 42, 200)") if dark else ("rgba(248, 250, 252, 220)", "rgba(255, 255, 255, 245)")
            bg1, bg2 = bg_map.get(key, fallback)

            card.setStyleSheet(
                f"""
                QFrame#kpiCard {{
                    border-top: 3px solid {accent};
                    border-left: 1px solid rgba(148, 163, 184, 50);
                    border-right: 1px solid rgba(148, 163, 184, 50);
                    border-bottom: 1px solid rgba(148, 163, 184, 50);
                    border-radius: 14px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {bg1}, stop:1 {bg2});
                }}
                """
            )
            if hasattr(card, "_icon_lbl"):
                card._icon_lbl.setStyleSheet(f"color: {accent}; font-size: 24px; background: transparent;")
            if hasattr(card, "_title_lbl"):
                card._title_lbl.setStyleSheet(f"color: {title_color}; font-size: 17px; font-weight: 600; background: transparent;")

        dark_section_bg = {
            "terminal": ("rgba(12, 20, 42, 242)", "rgba(6, 12, 28, 235)"),
            "reply": ("rgba(16, 32, 60, 240)", "rgba(8, 18, 40, 232)"),
            "upcoming": ("rgba(14, 42, 34, 240)", "rgba(8, 24, 32, 232)"),
            "insights": ("rgba(40, 26, 68, 240)", "rgba(20, 14, 48, 230)"),
            "default": ("rgba(24, 34, 52, 240)", "rgba(12, 18, 36, 232)"),
        }
        light_section_bg = {
            "terminal": ("rgba(248, 250, 252, 255)", "rgba(241, 245, 249, 255)"),
            "reply": ("rgba(240, 253, 244, 255)", "rgba(248, 250, 252, 255)"),
            "upcoming": ("rgba(240, 253, 244, 255)", "rgba(248, 250, 252, 255)"),
            "insights": ("rgba(245, 243, 255, 255)", "rgba(250, 245, 255, 255)"),
            "default": ("rgba(248, 250, 252, 255)", "rgba(255, 255, 255, 255)"),
        }

        for card in getattr(self, "_all_section_cards", []):
            variant = getattr(card, "_variant", "default")
            accent = getattr(card, "_accent_color", "#94A3B8")
            is_term = getattr(card, "_is_terminal", False)
            bg_map = dark_section_bg if dark else light_section_bg
            bg1, bg2 = bg_map.get(variant, bg_map["default"])

            card.setStyleSheet(
                f"""
                QFrame#sectionCard {{
                    border-left: 3px solid {accent};
                    border-top: 1px solid rgba(148, 163, 184, 45);
                    border-right: 1px solid rgba(148, 163, 184, 45);
                    border-bottom: 1px solid rgba(148, 163, 184, 45);
                    border-radius: 14px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {bg1}, stop:1 {bg2});
                }}
                """
            )

            if hasattr(card, "_hdr"):
                a_bg = 0.20 if dark else 0.12
                a_bdr = 0.30 if dark else 0.40
                card._hdr.setStyleSheet(
                    f"""
                    QFrame#sectionCardHeader {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 rgba({self._hex_to_rgba(accent, a_bg)}),
                            stop:1 rgba({self._hex_to_rgba(accent, 0.03)}));
                        border-bottom: 1px solid rgba({self._hex_to_rgba(accent, a_bdr)});
                        border-top-left-radius: 13px;
                        border-top-right-radius: 13px;
                        border-bottom-left-radius: 0px;
                        border-bottom-right-radius: 0px;
                    }}
                    """
                )

            if hasattr(card, "_icon_lbl"):
                card._icon_lbl.setStyleSheet(f"color: {accent}; font-size: 22px; background: transparent;")
            if hasattr(card, "_title_lbl"):
                title_color = "#F1F5F9" if dark else "#1E293B"
                card._title_lbl.setStyleSheet(f"color: {title_color}; font-size: 19px; font-weight: 700; background: transparent;")

            if hasattr(card, "_content"):
                if is_term:
                    text_color = "#86EFAC" if dark else "#166534"
                    card._content.setStyleSheet(
                        f"color: {text_color}; font-size: 18px; "
                        "font-family: 'Consolas', 'Courier New', monospace; "
                        "background: transparent; padding: 16px 20px;"
                    )
                elif variant == "insights":
                    text_color = "#CBD5E1" if dark else "#334155"
                    card._content.setStyleSheet(
                        f"color: {text_color}; font-size: 16px; line-height: 1.6; "
                        "background: transparent; padding: 14px 20px;"
                    )
                else:
                    text_color = "#CBD5E1" if dark else "#334155"
                    card._content.setStyleSheet(
                        f"color: {text_color}; font-size: 18px; "
                        "background: transparent; padding: 16px 20px;"
                    )

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
