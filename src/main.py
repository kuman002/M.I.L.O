"""
MILO - Managing Information & Lifestyle Optimizer
Main Entry Point
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """Main application entry point"""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("MILO")
    app.setOrganizationName("Annamalai University")
    app.setFont(QFont("Segoe UI", 11))
    
    # Create main window (will show itself after authentication)
    window = MainWindow()
    if not getattr(window, "authenticated", False):
        return
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
