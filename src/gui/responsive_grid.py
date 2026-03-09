"""
Responsive Grid Layout for PyQt5
Automatically wraps widgets based on available width (like modern SaaS dashboards)
"""

from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import Qt


class ResponsiveGrid(QWidget):
    """
    Responsive grid that automatically adjusts column count based on window width.
    Widgets automatically reflow when window is resized.
    """
    
    def __init__(self, min_card_width=260, max_columns=None, parent=None):
        """
        Initialize responsive grid.
        
        Args:
            min_card_width: Minimum width of each card (default 260px)
            max_columns: Optional maximum number of columns
            parent: Parent widget
        """
        super().__init__(parent)
        self.min_card_width = min_card_width
        self.max_columns = max_columns
        self.cards = []
        self._reflowing = False  # Guard against recursion
        
        # Setup grid layout
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.grid)
    
    def add_card(self, widget):
        """Add a card widget to the grid"""
        self.cards.append(widget)
        self.reflow()
    
    def add_cards(self, *widgets):
        """Add multiple card widgets at once"""
        for widget in widgets:
            self.cards.append(widget)
        self.reflow()
    
    def remove_card(self, widget):
        """Remove a card widget from the grid"""
        if widget in self.cards:
            self.cards.remove(widget)
            self.reflow()
    
    def clear_cards(self):
        """Remove all cards from the grid"""
        self.cards.clear()
        self.reflow()
    
    def resizeEvent(self, event):
        """Handle window resize - reflow cards"""
        super().resizeEvent(event)
        # Prevent recursion from hide/show triggering more resizeEvent
        if not self._reflowing:
            self._reflowing = True
            self.reflow()
            self._reflowing = False
    
    def reflow(self):
        """
        Recalculate grid layout based on current width.
        Responsively adjusts columns.
        """
        if not self.cards:
            return
        
        # Get available width
        width = self.width()
        if width <= 0:
            return
        
        # Calculate optimal column count
        # Ensure at least 1 column, at most reasonable number
        cols = max(1, width // self.min_card_width)
        if self.max_columns is not None:
            cols = min(cols, self.max_columns)
        
        # Clear existing layout (remove all items without triggering resize)
        while self.grid.count():
            item = self.grid.takeAt(0)
            # Don't hide/show as it triggers layout changes and resizeEvent
        
        # Add cards back with new grid positions
        for i, card in enumerate(self.cards):
            row = i // cols
            col = i % cols
            self.grid.addWidget(card, row, col)
    
    def get_column_count(self):
        """Get current number of columns"""
        width = self.width()
        if width <= 0:
            return 1
        cols = max(1, width // self.min_card_width)
        if self.max_columns is not None:
            cols = min(cols, self.max_columns)
        return cols
    
    def set_min_card_width(self, width):
        """Update minimum card width and reflow"""
        self.min_card_width = width
        self.reflow()

    def set_max_columns(self, max_columns):
        """Update max columns and reflow"""
        self.max_columns = max_columns
        self.reflow()
