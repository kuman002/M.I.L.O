"""
Modern CSS Styles for MILO Assistant
Provides a premium dark-mode aesthetic with vibrant colors and glassmorphism.
"""

APP_STYLES = """
QMainWindow {
    background-color: #0f172a;
}

QWidget {
    color: #f1f5f9;
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
}

QLabel {
    color: #f1f5f9;
}

/* Tab Widget Styling */
QTabWidget::pane {
    border: 1px solid #334155;
    background: #111827;
    border-radius: 16px;
    top: -1px;
    padding: 10px;
}

QTabBar::tab {
    background: #1e293b;
    color: #94a3b8;
    padding: 12px 24px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    margin-right: 4px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #334155;
    border-bottom: none;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3b82f6, stop:1 #2563eb);
    color: white;
    border-color: #3b82f6;
}

QTabBar::tab:hover:!selected {
    background: #334155;
    color: #f1f5f9;
}

/* Input Fields */
QLineEdit {
    background-color: #1e293b;
    border: 2px solid #334155;
    border-radius: 10px;
    padding: 10px 15px;
    color: #f1f5f9;
    font-size: 14px;
    selection-background-color: #3b82f6;
}

QLineEdit:focus {
    border: 2px solid #3b82f6;
    background-color: #243048;
}

QTextEdit {
    background-color: #1e293b;
    border: 2px solid #334155;
    border-radius: 12px;
    padding: 12px;
    color: #cbd5e1;
    font-size: 14px;
    line-height: 1.5;
}

/* Buttons */
QPushButton {
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #2563eb;
}

QPushButton:pressed {
    background-color: #1d4ed8;
    padding-top: 11px;
    padding-bottom: 9px;
}

QPushButton:disabled {
    background-color: #334155;
    color: #64748b;
}

QPushButton#voice_btn_active {
    background-color: #ef4444;
    border: 2px solid #fecaca;
}

QPushButton#voice_btn_active:hover {
    background-color: #dc2626;
}

/* Tables */
QTableWidget {
    background-color: #1e293b;
    gridline-color: #334155;
    border: 1px solid #334155;
    border-radius: 12px;
    color: #f1f5f9;
    outline: none;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 12px;
    border: none;
    border-bottom: 2px solid #334155;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.8px;
}

QTableWidget::item {
    padding: 12px;
    border-bottom: 1px solid #334155;
}

QTableWidget::item:selected {
    background-color: #3b82f622;
    color: #3b82f6;
}

/* List Widgets */
QListWidget {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 8px;
    color: #f1f5f9;
    outline: none;
}

QListWidget::item {
    padding: 14px;
    border-radius: 8px;
    margin-bottom: 4px;
    border: 1px solid transparent;
}

QListWidget::item:hover {
    background-color: #334155;
}

QListWidget::item:selected {
    background-color: #3b82f611;
    border-color: #3b82f644;
    color: #3b82f6;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0f172a;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

/* Dashboard Cards */
QLabel#card_title {
    color: #94a3b8;
    font-size: 11px;
    text-transform: uppercase;
    font-weight: 800;
    letter-spacing: 1px;
}

QLabel#card_value {
    color: #ffffff;
    font-size: 28px;
    font-weight: bold;
}

/* Progress bar style can be used for habit completion */
QProgressBar {
    border: none;
    background-color: #334155;
    height: 6px;
    border-radius: 3px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 3px;
}

/* Dashboard Styling */
.task-card-item {
    background-color: #1e293b;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 8px;
    border-left: 5px solid #3b82f6;
}

.insight-card-item {
    background-color: #1e293b;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 8px;
    border-left: 5px solid #10b981;
}

QLabel#item-title {
    font-weight: bold;
    color: #f1f5f9;
}

QLabel#item-subtitle {
    font-size: 11px;
    color: #94a3b8;
}
"""

def get_card_style(color_hex):
    return f"""
        background-color: {color_hex}15;
        border: 1px solid {color_hex}40;
        border-radius: 16px;
        padding: 20px;
    """
