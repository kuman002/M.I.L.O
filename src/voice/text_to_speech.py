"""
MILO TTS — Stable Optimized Version
Fixes: double speech + silence bug
"""

import pyttsx3
import threading
import queue
import time
import sys
import re
from dataclasses import dataclass
from typing import Optional

# ========= PRECOMPILED =========
EMOJI_PATTERN = re.compile(r'[\U0001F300-\U0001F9FF]')
CLEANUP_PATTERN = re.compile(r'[^\w\s\.\,\!\?\-\:\;]')
SPACES_PATTERN = re.compile(r'\s+')

CHAR_REPLACEMENTS = str.maketrans({
    '$': 'dollar ', '€': 'euro ', '£': 'pound ', '₹': 'rupee ',
    '/': ' or ', '\\': ' backslash ', '_': ' ', '-': ' '
})


@dataclass(slots=True)
class SpeakItem:
    text: str
    done: Optional[threading.Event] = None


class TextToSpeech:
    def __init__(self):
        self.engine = None
        self.is_speaking = False

        self._queue: queue.Queue[Optional[SpeakItem]] = queue.Queue()
        self._stop_event = threading.Event()

        self._last_spoken = ""
        self._last_spoken_at = 0.0

        self._is_windows = sys.platform == "win32"
        self._reinit_each_utterance = self._is_windows
        self._worker: Optional[threading.Thread] = None
        self._start_worker()

    def _start_worker(self):
        if self._worker and self._worker.is_alive():
            return
        self._stop_event.clear()
        self._worker = threading.Thread(
            target=self._worker_loop,
            name="MILO-TTS",
            daemon=True
        )
        self._worker.start()

    # ========= ENGINE =========
    def _init_engine(self):
        """Init ONLY inside worker thread"""
        if self.engine:
            return

        try:
            if self._is_windows:
                self.engine = pyttsx3.init(driverName="sapi5")
            else:
                self.engine = pyttsx3.init()

            voices = self.engine.getProperty("voices") or []
            for v in voices:
                n = v.name.lower()
                if "zira" in n or "female" in n:
                    self.engine.setProperty("voice", v.id)
                    break

            self.engine.setProperty("rate", 155)
            self.engine.setProperty("volume", 1.0)

        except Exception as e:
            print(f"[TTS] init failed: {e}")
            self.engine = None

    def is_available(self) -> bool:
        return self._worker.is_alive()

    # ========= PUBLIC =========
    def speak(self, text: str, wait: bool = False):
        if not text:
            return

        text = text.strip()
        if not text:
            return

        now = time.time()
        if text == self._last_spoken and now - self._last_spoken_at < 2:
            return

        # Auto-recover if worker died after a TTS engine error
        if not self._worker or not self._worker.is_alive():
            print("[TTS] Worker was not alive. Restarting...")
            self.engine = None
            self._start_worker()

        self._last_spoken = text
        self._last_spoken_at = now

        evt = threading.Event() if wait else None
        self._queue.put(SpeakItem(text, evt))

        if wait:
            evt.wait(30)

    def stop(self):
        """Stop current speech and clear queue safely"""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

        if self.engine and self.is_speaking:
            try:
                self.engine.stop()
            except Exception:
                pass

    def shutdown(self):
        self._stop_event.set()
        self._queue.put(None)
        if self._worker and self._worker.is_alive():
            self._worker.join(2)

    # ========= CLEAN =========
    def _clean(self, text: str) -> str:
        text = text.translate(CHAR_REPLACEMENTS)
        text = EMOJI_PATTERN.sub("", text)
        text = CLEANUP_PATTERN.sub("", text)
        return SPACES_PATTERN.sub(" ", text).strip()

    # ========= WORKER =========
    def _worker_loop(self):
        # COM init (Windows)
        pythoncom = None
        if self._is_windows:
            try:
                import pythoncom as pc
                # Try to initialize with apartment threaded (standard for UI/SAPI5)
                # If already initialized with a different mode, PyQt/Ole might have handled it.
                try:
                    pc.CoInitializeEx(pc.COINIT_APARTMENTTHREADED)
                except Exception:
                    pc.CoInitialize() # Fallback
                pythoncom = pc
            except Exception as e:
                print(f"[TTS] COM init failed: {e}")

        # IMPORTANT: init engine here once
        self._init_engine()

        try:
            while not self._stop_event.is_set():
                try:
                    item = self._queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if item is None:
                    break

                text = self._clean(item.text)
                if not text:
                    if item.done:
                        item.done.set()
                    continue

                if not self.engine:
                    self._init_engine()
                    if not self.engine:
                        if item.done:
                            item.done.set()
                        continue

                try:
                    self.is_speaking = True

                    # Windows SAPI can become silent after first run on reused engine.
                    # Recreate engine per utterance for stable continuous speech.
                    if self._reinit_each_utterance:
                        try:
                            if self.engine:
                                self.engine.stop()
                        except Exception:
                            pass
                        self.engine = None
                        self._init_engine()
                        if not self.engine:
                            continue

                    self.engine.say(text)
                    self.engine.runAndWait()

                    if self._reinit_each_utterance:
                        try:
                            self.engine.stop()
                        except Exception:
                            pass
                        self.engine = None

                except RuntimeError:
                    # pyttsx3 loop glitch — reinit safely
                    try:
                        self.engine.stop()
                    except Exception:
                        pass
                    self.engine = None
                    self._init_engine()
                except Exception as e:
                    print(f"[TTS] speak error: {e}")
                    try:
                        if self.engine:
                            self.engine.stop()
                    except Exception:
                        pass
                    self.engine = None
                    self._init_engine()

                finally:
                    self.is_speaking = False
                    if item.done:
                        item.done.set()

        finally:
            if self.engine:
                try:
                    self.engine.stop()
                except Exception:
                    pass

            if pythoncom:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
