"""
TC-KAGGLE-01 to TC-KAGGLE-05
Voice recognition accuracy benchmark using the Kaggle dataset
'pavanelisetty/sample-audio-files-for-speech-recognition'.

These tests wrap the evaluation logic from scripts/evaluate_voice_kaggle.py
into pytest-compatible assertions. A single VoiceRecognizer instance is shared
across all test methods (setUpClass) to avoid re-loading the Whisper model per
test. Requires: kagglehub, jiwer, SpeechRecognition, faster-whisper.
"""

import json
import os
import re
import sys
import unittest
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
for _p in (str(PROJECT_ROOT), str(SRC_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Optional-dependency guards
# ---------------------------------------------------------------------------
try:
    import kagglehub
    _KAGGLEHUB_OK = True
except ImportError:
    _KAGGLEHUB_OK = False

try:
    from jiwer import cer, wer
    _JIWER_OK = True
except ImportError:
    _JIWER_OK = False

try:
    import speech_recognition as sr
    _SR_OK = True
except ImportError:
    _SR_OK = False

VoiceRecognizer = None
for _mod in ("src.voice.voice_recognition_optimized", "voice.voice_recognition_optimized"):
    try:
        import importlib
        _m = importlib.import_module(_mod)
        VoiceRecognizer = getattr(_m, "VoiceRecognizer", None)
        if VoiceRecognizer is not None:
            break
    except Exception:
        continue

_MISSING = (
    "kagglehub" if not _KAGGLEHUB_OK else
    "jiwer" if not _JIWER_OK else
    "SpeechRecognition" if not _SR_OK else
    "VoiceRecognizer" if VoiceRecognizer is None else
    None
)

# ---------------------------------------------------------------------------
# Helpers (mirrors scripts/evaluate_voice_kaggle.py)
# ---------------------------------------------------------------------------

HARVARD_REFERENCE = (
    "the stale smell of old beer lingers it takes heat to bring out the odor "
    "a cold dip restores health and zest a salt pickle tastes fine with ham "
    "tacos al pastor are my favorite a zestful food is the hot cross bun"
)


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _wav_to_audio_data(path: Path) -> "sr.AudioData":
    with wave.open(str(path), "rb") as wf:
        rate = wf.getframerate()
        width = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())
    return sr.AudioData(raw, rate, width)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@unittest.skipIf(_MISSING is not None, f"Required dependency unavailable: {_MISSING}")
class TestVoiceKaggleAccuracy(unittest.TestCase):
    """Pytest-compatible accuracy tests driven by the Kaggle audio benchmark dataset."""

    _recognizer = None
    _dataset_path: Path = None
    _results: dict = {}

    @classmethod
    def setUpClass(cls):
        cls._dataset_path = Path(
            kagglehub.dataset_download(
                "pavanelisetty/sample-audio-files-for-speech-recognition"
            )
        )
        model_size = os.getenv("MILO_EVAL_MODEL", "tiny.en")
        cls._recognizer = VoiceRecognizer(model_size=model_size, device="cpu", language="en")

        # Pre-run inference once so every test method uses cached results.
        for filename, expected_speech in [("harvard.wav", True), ("jackhammer.wav", False)]:
            fpath = cls._dataset_path / filename
            audio_data = _wav_to_audio_data(fpath)
            result = cls._recognizer.transcribe_audio_memory(audio_data)
            pred_raw = result.get("text", "") if result.get("success") else ""
            cls._results[filename] = {
                "result": result,
                "pred_text": _normalize(pred_raw),
                "pred_raw": pred_raw,
                "expected_speech": expected_speech,
            }

    # ------------------------------------------------------------------
    # TC-KAGGLE-01  harvard.wav — speech must be detected
    # ------------------------------------------------------------------
    def test_TC_KAGGLE_01_harvard_speech_detected(self):
        """harvard.wav contains clear speech; recognizer must return a non-empty transcription."""
        r = self._results["harvard.wav"]
        self.assertTrue(
            bool(r["pred_text"]),
            f"Expected non-empty transcription for harvard.wav, got: '{r['pred_text']}'",
        )

    # ------------------------------------------------------------------
    # TC-KAGGLE-02  jackhammer.wav — noise gate must reject non-speech
    # ------------------------------------------------------------------
    def test_TC_KAGGLE_02_jackhammer_noise_rejected(self):
        """jackhammer.wav is background-noise only; recognizer must not mark it as successful speech."""
        r = self._results["jackhammer.wav"]
        self.assertFalse(
            r["result"].get("success", False),
            "Noise-only audio should not be returned with success=True.",
        )
        self.assertEqual(
            r["pred_text"],
            "",
            f"Expected empty transcription for jackhammer.wav, got: '{r['pred_text']}'",
        )

    # ------------------------------------------------------------------
    # TC-KAGGLE-03  command intent must be None for both non-command clips
    # ------------------------------------------------------------------
    def test_TC_KAGGLE_03_no_milo_command_detected_in_benchmark_clips(self):
        """Neither audio clip should trigger a MILO command intent (expected_command=None for both)."""
        for filename in ("harvard.wav", "jackhammer.wav"):
            pred_raw = self._results[filename]["pred_raw"]
            detected = self._recognizer.detect_command(pred_raw)
            self.assertIsNone(
                detected,
                f"{filename}: unexpected MILO command detected: {detected}",
            )

    # ------------------------------------------------------------------
    # TC-KAGGLE-04  WER for harvard.wav must be below 1.0 (tiny.en baseline)
    # ------------------------------------------------------------------
    def test_TC_KAGGLE_04_harvard_wer_within_tiny_en_baseline(self):
        """WER for harvard.wav must be < 1.0 with the tiny.en model (deletion-dominated error regime)."""
        reference = _normalize(HARVARD_REFERENCE)
        hypothesis = self._results["harvard.wav"]["pred_text"]
        score = wer(reference, hypothesis)
        self.assertLess(
            score,
            1.0,
            f"WER {score:.4f} exceeds the 1.0 ceiling expected for tiny.en on harvard.wav.",
        )

    # ------------------------------------------------------------------
    # TC-KAGGLE-05  report JSON exists and contains required keys
    # ------------------------------------------------------------------
    def test_TC_KAGGLE_05_report_json_exists_and_is_valid(self):
        """evaluate_voice_kaggle.py must produce a valid JSON report at data/voice_accuracy_report_kaggle.json."""
        report_path = PROJECT_ROOT / "data" / "voice_accuracy_report_kaggle.json"
        self.assertTrue(report_path.exists(), f"Report file not found: {report_path}")
        with open(report_path, encoding="utf-8") as fh:
            report = json.load(fh)
        self.assertIn("summary", report)
        self.assertIn("files", report)
        for key in ("total_files", "exact_match_accuracy", "command_accuracy", "speech_detection_accuracy"):
            self.assertIn(key, report["summary"], f"Missing key in summary: {key}")
        self.assertEqual(report["summary"]["total_files"], 2)


if __name__ == "__main__":
    unittest.main()
