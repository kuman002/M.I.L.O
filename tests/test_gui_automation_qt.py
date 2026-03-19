import time
import os
import sys

import pytest
from PyQt5.QtCore import QTimer

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

pytest.importorskip("pytestqt")

try:
    import src.gui.main_window as main_window_module
except Exception:
    import gui.main_window as main_window_module


class _FakeVoiceRecognizer:
    def __init__(self, model_size="base"):
        self.model_size = model_size

    def is_available(self):
        return False

    def start_listening(self, _callback):
        return True

    def stop_listening(self):
        return None

    def cleanup(self):
        return None

    def detect_command(self, _text):
        return None

    def parse_reminder_command(self, _text):
        return None

    def calibrate_noise(self, duration=2.0):
        return True

    def enroll_speaker_profile(self, samples=5, progress_callback=None):
        return (False, "disabled in test")

    def run_pre_enrollment_diagnostics(self, duration=1.5):
        return {"ok": True, "message": "ok"}


def _build_window(monkeypatch):
    monkeypatch.setattr(main_window_module, "VoiceRecognizer", _FakeVoiceRecognizer)
    monkeypatch.setattr(main_window_module.MainWindow, "_ensure_pin", lambda self: True)
    monkeypatch.setattr(main_window_module.MainWindow, "_apply_blur", lambda self: None)
    monkeypatch.setattr(main_window_module.MainWindow, "_remove_blur", lambda self: None)
    monkeypatch.setattr(main_window_module.MainWindow, "prompt_voice_enrollment_if_needed", lambda self: None)

    win = main_window_module.MainWindow()

    def _slow_command(_text):
        time.sleep(0.9)
        return {
            "intent": "chitchat",
            "message": "Async done",
            "data": None,
            "success": True,
        }

    win.assistant.process_command = _slow_command
    return win


def test_dashboard_remains_responsive_during_heavy_nlp(qtbot, monkeypatch):
    win = _build_window(monkeypatch)
    qtbot.addWidget(win)
    win.show()

    ticks = {"count": 0}

    timer = QTimer()
    timer.setInterval(50)
    timer.timeout.connect(lambda: ticks.__setitem__("count", ticks["count"] + 1))
    timer.start()

    win.input_field.setText("simulate heavy nlp")
    win.process_input()

    # Programmatic dashboard navigation while NLP is running.
    for idx in [1, 2, 3, 4, 0]:
        win.tabs.setCurrentIndex(idx)
        qtbot.wait(70)

    qtbot.waitUntil(lambda: win.message_area.toPlainText() == "Async done", timeout=3000)

    timer.stop()
    assert ticks["count"] >= 6
    assert win.tabs.currentIndex() == 0
