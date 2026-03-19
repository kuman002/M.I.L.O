import math
import struct
import time
import os
import sys

import speech_recognition as sr

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

try:
    from src.voice.voice_recognition_optimized import VoiceRecognizer
    from src.automation.computer_use import MiloEyes, MiloHands
except Exception:
    from voice.voice_recognition_optimized import VoiceRecognizer
    from automation.computer_use import MiloEyes, MiloHands


class _FakeInfo:
    language = "en"


class _FakeSegment:
    def __init__(self, text: str):
        self.text = text


class _FakeWhisperModel:
    def transcribe(self, audio_np, **kwargs):
        return ([_FakeSegment("add task tomorrow 5 pm")], _FakeInfo())


def _build_audio_data(seconds: float = 1.2, sample_rate: int = 16000) -> sr.AudioData:
    samples = []
    frequency = 220.0
    total = int(sample_rate * seconds)
    for i in range(total):
        val = int(12000 * math.sin(2 * math.pi * frequency * (i / sample_rate)))
        samples.append(struct.pack("<h", val))
    raw = b"".join(samples)
    return sr.AudioData(raw, sample_rate, 2)


def test_inject_wav_bytes_into_voice_pipeline_without_live_mic():
    vr = VoiceRecognizer.__new__(VoiceRecognizer)
    vr.model = _FakeWhisperModel()
    vr.batched_model = None
    vr.language = "en"
    vr.enable_audio_preprocess = False
    vr.enable_noise_reduce = False
    vr.batch_size = 1
    vr._transcribe_base_kwargs = {
        "language": "en",
        "beam_size": 1,
        "best_of": 1,
        "temperature": 0.0,
        "without_timestamps": True,
    }

    audio_data = _build_audio_data()
    result = vr.transcribe_audio_memory(audio_data)

    assert result["success"] is True
    assert "add task" in result["text"]


def test_inject_static_screenshot_into_ocr_lookup(monkeypatch):
    eyes = MiloEyes(gpu=False)

    class _FakeReader:
        def readtext(self, _image):
            return [
                (
                    [(10, 20), (90, 20), (90, 60), (10, 60)],
                    "Open Notepad",
                    0.96,
                )
            ]

    monkeypatch.setattr(eyes, "is_available", lambda: True)
    monkeypatch.setattr(eyes, "_capture_screen", lambda: [[0, 0], [0, 0]])
    monkeypatch.setattr(eyes, "_get_reader", lambda: _FakeReader())

    clicked = {}

    def _fake_click(x, y, duration=0.12):
        clicked["x"] = x
        clicked["y"] = y
        return {"success": True, "x": x, "y": y}

    monkeypatch.setattr(MiloHands, "click_at", staticmethod(_fake_click))

    result = eyes.find_and_click_text("notepad")

    assert result["success"] is True
    assert clicked == {"x": 50, "y": 40}
