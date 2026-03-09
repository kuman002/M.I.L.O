import subprocess
import threading
import time
import webbrowser
import re
from typing import Dict, Optional
from urllib.parse import quote_plus

from automation.computer_use import ContextEngine, MiloHands, MiloEyes

try:
    import pyautogui
    from pywinauto import Application, Desktop  # noqa: F401  (reserved for future window-specific flows)
    RPA_AVAILABLE = True
except ImportError:
    pyautogui = None
    RPA_AVAILABLE = False


class RPAService:
    """High-level automation layer for MILO."""

    def __init__(self):
        self.available = RPA_AVAILABLE
        # Backward compatibility for existing call sites
        self.is_available = self.available
        self.eyes = MiloEyes(gpu=False)

        if self.available:
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.15

        MiloHands.configure()

    # ------------------------------------------------
    # Utility
    # ------------------------------------------------

    def _run_async(self, func):
        threading.Thread(target=func, daemon=True).start()

    def _fail(self, message: str) -> Dict:
        return {"success": False, "message": message}

    def _expand_spoken_keys(self, text: str) -> str:
        """Map spoken formatting commands to control characters while preserving spaces."""
        if not text:
            return ""

        expanded = text
        substitutions = [
            (r"\b(next\s+line|new\s+line)\b", "\n"),
            (r"\b(enter)\b", "\n"),
            (r"\b(tab)\b", "\t"),
        ]

        for pattern, repl in substitutions:
            expanded = re.sub(pattern, repl, expanded, flags=re.IGNORECASE)

        return expanded

    def get_active_context(self) -> str:
        return ContextEngine.get_active_context()

    # ------------------------------------------------
    # Basic Controls
    # ------------------------------------------------

    def type_text(self, text: str) -> Dict:
        if not self.available:
            return self._fail("RPA tools not installed")

        prepared_text = self._expand_spoken_keys(text)
        print("[MILO typing]:", repr(prepared_text))

        # If no control chars are present, use bulk write for speed and spacing stability.
        if "\n" not in prepared_text and "\t" not in prepared_text:
            result = MiloHands.type_text(prepared_text, interval=0.01)
        else:
            # Handle line breaks/tabs explicitly for reliable editor behavior.
            ok = True
            for ch in prepared_text:
                if ch == "\n":
                    res = MiloHands.press_key("enter")
                elif ch == "\t":
                    res = MiloHands.press_key("tab")
                else:
                    res = MiloHands.type_text(ch, interval=0.01)

                if not res.get("success"):
                    ok = False
                    result = res
                    break

            if ok:
                result = {"success": True, "message": "Typed with spoken key expansion"}

        if result.get("success"):
            result["context"] = self.get_active_context()
        return result

    def press_key(self, key: str) -> Dict:
        if not self.available:
            return self._fail("RPA tools not installed")
        return MiloHands.press_key(key)

    def click_at(self, x: int, y: int) -> Dict:
        if not self.available:
            return self._fail("RPA tools not installed")
        return MiloHands.click_at(x, y)

    def click_text(self, text: str) -> Dict:
        if not self.available:
            return self._fail("Vision engine unavailable")
        return self.eyes.find_and_click_text(text)

    # ------------------------------------------------
    # Browser Automation
    # ------------------------------------------------

    def search_in_browser_context(self, query: str) -> Dict:
        if not query or not query.strip():
            return self._fail("Search query is empty")

        context = self.get_active_context()
        if context == "browser":
            focus = MiloHands.hotkey("ctrl", "l")
            if not focus.get("success"):
                return focus

            typed = MiloHands.type_text(query)
            if not typed.get("success"):
                return typed

            pressed = MiloHands.press_key("enter")
            if not pressed.get("success"):
                return pressed

            return {
                "success": True,
                "message": f"Searched: {query}",
                "context": context,
            }

        try:
            webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
            return {
                "success": True,
                "message": f"Opened browser search: {query}",
                "context": context,
            }
        except Exception as e:
            return self._fail(f"Search failed: {e}")

    # ------------------------------------------------
    # Window Management
    # ------------------------------------------------

    def snap_window_left(self):
        if self.available:
            pyautogui.hotkey("win", "left")

    def snap_window_right(self):
        if self.available:
            pyautogui.hotkey("win", "right")

    # ------------------------------------------------
    # Development Environment Setup
    # ------------------------------------------------

    def open_vscode(self, workspace: Optional[str] = None):
        if not self.available:
            return False

        try:
            cmd = ["code"]
            if workspace:
                cmd.append(workspace)

            subprocess.Popen(cmd)
            time.sleep(2)
            self.snap_window_left()
            return True
        except Exception as e:
            print("[RPA] VSCode error:", e)
            return False

    # Backward compatibility alias used by older call sites
    def open_vscode_and_setup(self, workspace_path: Optional[str] = None):
        return self.open_vscode(workspace_path)

    def setup_coding_environment(self, project_path: Optional[str] = None):
        if not self.available:
            return "Automation tools unavailable"

        def task():
            try:
                print("[RPA] Opening VSCode")
                self.open_vscode(project_path)

                print("[RPA] Opening Terminal")
                subprocess.Popen(["cmd.exe", "/k", f"cd /d {project_path or '.'}"])
                time.sleep(1.5)

                print("[RPA] Opening Browser")
                webbrowser.open("http://localhost:3000")
                time.sleep(2)
                self.snap_window_right()

                print("[RPA] Setup complete")
            except Exception as e:
                print("[RPA] Setup failed:", e)

        self._run_async(task)
        return "Setting up coding environment..."

    # ------------------------------------------------
    # Spotify Automation
    # ------------------------------------------------

    def play_spotify_lofi(self):
        if not self.available:
            return "Spotify automation unavailable"

        def task():
            try:
                subprocess.Popen(["start", "spotify"], shell=True)
                time.sleep(4)

                pyautogui.hotkey("ctrl", "l")
                pyautogui.write("Lofi Focus Playlist", interval=0.08)
                pyautogui.press("enter")
                time.sleep(2)
                pyautogui.press("space")
            except Exception as e:
                print("[RPA] Spotify failed:", e)

        self._run_async(task)
        return "Opening Spotify and playing Lofi."

    # ------------------------------------------------
    # Presentation Controls
    # ------------------------------------------------

    def next_slide(self):
        if self.available:
            pyautogui.press("right")
        return "Next slide"

    def prev_slide(self):
        if self.available:
            pyautogui.press("left")
        return "Previous slide"
