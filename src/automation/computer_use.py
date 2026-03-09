from typing import Any, Dict, Optional, Tuple

# Optional dependencies
try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    HANDS_AVAILABLE = True
except ImportError:
    pyautogui = None
    HANDS_AVAILABLE = False

try:
    import pygetwindow as gw
    CONTEXT_AVAILABLE = True
except ImportError:
    gw = None
    CONTEXT_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV_AVAILABLE = False

try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    easyocr = None
    OCR_AVAILABLE = False


class ContextEngine:
    APP_PATTERNS = {
        "notepad": ["notepad"],
        "browser": ["chrome", "brave", "edge", "firefox", "opera", "browser"],
        "vscode": ["visual studio code", " vscode", " - code", "code - "],
        "terminal": ["powershell", "terminal", "command prompt", "cmd.exe"],
    }

    @staticmethod
    def get_active_context() -> str:
        if not CONTEXT_AVAILABLE:
            return "unknown"

        try:
            window = gw.getActiveWindow()
            if not window or not window.title:
                return "unknown"

            title = window.title.lower()
            for app_name, patterns in ContextEngine.APP_PATTERNS.items():
                if any(pattern in title for pattern in patterns):
                    return app_name
            return "unknown"
        except Exception:
            return "unknown"


class MiloHands:
    @staticmethod
    def is_available() -> bool:
        return HANDS_AVAILABLE

    @staticmethod
    def configure() -> None:
        if not HANDS_AVAILABLE:
            return
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

    @staticmethod
    def type_text(text: str, interval: float = 0.02) -> Dict[str, Any]:
        if not HANDS_AVAILABLE:
            return {"success": False, "message": "pyautogui not installed"}

        try:
            pyautogui.write(text, interval=interval)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def press_key(key: str) -> Dict[str, Any]:
        if not HANDS_AVAILABLE:
            return {"success": False}

        try:
            pyautogui.press(key)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def hotkey(*keys: str) -> Dict[str, Any]:
        if not HANDS_AVAILABLE:
            return {"success": False}

        try:
            pyautogui.hotkey(*keys)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def click_at(x: int, y: int, duration: float = 0.12) -> Dict[str, Any]:
        if not HANDS_AVAILABLE:
            return {"success": False}

        try:
            pyautogui.moveTo(x, y, duration=duration)
            pyautogui.click(x, y)
            return {"success": True, "x": x, "y": y}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def scroll(amount: int) -> None:
        if HANDS_AVAILABLE:
            pyautogui.scroll(amount)


class MiloEyes:
    _reader = None  # Cached OCR engine for faster repeated calls

    def __init__(self, gpu: bool = False):
        self.gpu = gpu

    def is_available(self) -> bool:
        return HANDS_AVAILABLE and CV_AVAILABLE and OCR_AVAILABLE

    def _get_reader(self):
        if MiloEyes._reader is None:
            MiloEyes._reader = easyocr.Reader(["en"], gpu=self.gpu)
        return MiloEyes._reader

    def _capture_screen(self):
        screenshot = pyautogui.screenshot()

        # Fast RGB->BGR conversion for OCR
        image = np.asarray(screenshot)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return image

    def find_text_center(self, target_text: str, min_prob: float = 0.5) -> Optional[Tuple[int, int, str]]:
        if not self.is_available() or not target_text or not target_text.strip():
            return None

        try:
            image = self._capture_screen()
            reader = self._get_reader()
            results = reader.readtext(image)
        except Exception:
            return None

        target = target_text.lower().strip()
        best_match = None
        best_score = 0.0

        for bbox, text, prob in results:
            text_lower = (text or "").lower().strip()

            if target not in text_lower and text_lower not in target:
                continue

            if prob < min_prob:
                continue

            (x1, y1), _, (x2, y2), _ = bbox
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            score = float(prob) + (0.2 if text_lower == target else 0.0)

            if score > best_score:
                best_score = score
                best_match = (center_x, center_y, text)

        return best_match

    def find_and_click_text(self, target_text: str, min_prob: float = 0.5) -> Dict[str, Any]:
        match = self.find_text_center(target_text, min_prob=min_prob)

        if not match:
            return {"success": False, "message": f"{target_text} not found"}

        x, y, matched_text = match
        click_result = MiloHands.click_at(x, y)

        if click_result.get("success"):
            return {"success": True, "text": matched_text, "x": x, "y": y}

        return click_result
