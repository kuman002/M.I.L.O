"""
Base Tab Class for MILO
Common functionality for all tab modules
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QFont, QColor


class BaseTab(QWidget):
    """Base class for all MILO tabs"""
    
    def __init__(self, assistant, tts, parent=None):
        super().__init__(parent)
        self.assistant = assistant
        self.tts = tts
        self.parent_window = parent
        self.setup_ui()
    
    def setup_ui(self):
        """Override this method in child classes to build the tab UI"""
        raise NotImplementedError("Child classes must implement setup_ui()")
    
    def refresh(self):
        """Override this method in child classes to refresh tab data"""
        pass
    
    def speak(self, message, wait=False):
        """Speak a message using TTS"""
        if self.tts:
            print(f"[TTS] Speaking: {message}")
            self.tts.speak(message, wait=wait)
