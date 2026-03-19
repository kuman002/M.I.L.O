"""
TC-ENROLL-01 to TC-ENROLL-19
Unit tests for VoiceRecognizer.calibrate_noise(),
VoiceRecognizer.run_pre_enrollment_diagnostics(), and
VoiceRecognizer.enroll_speaker_profile().

TC-ENROLL-01 to 13: mic-free fast-path / exception-path coverage.
TC-ENROLL-14 to 19: production loop coverage — mic and biometrics are both
  mocked so the actual enrollment processing loop is exercised. These tests
  exist specifically because production enrollment fails when biometrics or
  the microphone are unavailable; without them, the earlier tests only
  validate the fast-fail guard ("biometrics is None") and never touch the
  real audio-processing and streak-tracking logic.
"""

import importlib
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
for _p in (str(PROJECT_ROOT), str(SRC_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import speech_recognition as sr
    _SR_OK = True
except ImportError:
    _SR_OK = False

VoiceRecognizer = None
for _mod in ("src.voice.voice_recognition_optimized", "voice.voice_recognition_optimized"):
    try:
        _m = importlib.import_module(_mod)
        VoiceRecognizer = getattr(_m, "VoiceRecognizer", None)
        if VoiceRecognizer is not None:
            break
    except Exception:
        continue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_vr() -> "VoiceRecognizer":
    """Construct a VoiceRecognizer without __init__ (skips Whisper model load and mic)."""
    vr = VoiceRecognizer.__new__(VoiceRecognizer)
    vr.recognizer = sr.Recognizer()
    vr.voice_biometrics = None
    vr._enrollment_active = False
    vr.SAMPLE_RATE = VoiceRecognizer.SAMPLE_RATE
    vr.SAMPLE_WIDTH = VoiceRecognizer.SAMPLE_WIDTH
    vr.enable_audio_preprocess = False
    vr.enable_noise_reduce = False
    vr._command_items = tuple(VoiceRecognizer.COMMANDS.items())
    vr._keyword_items = tuple(VoiceRecognizer.KEYWORD_COMMAND_MAP.items())
    vr._command_first_tokens = tuple(
        (phrase, cmd_id, phrase.split(" ", 1)[0])
        for phrase, cmd_id in vr._command_items
    )
    return vr


def _make_audio_data(samples_int16: np.ndarray) -> "sr.AudioData":
    """Wrap a numpy int16 array into sr.AudioData at the engine's native sample rate."""
    raw = samples_int16.astype(np.int16).tobytes()
    return sr.AudioData(raw, VoiceRecognizer.SAMPLE_RATE, VoiceRecognizer.SAMPLE_WIDTH)


def _patch_mic(mock_source: MagicMock) -> MagicMock:
    """Return a context-manager mock that yields mock_source on __enter__."""
    cm = MagicMock()
    cm.__enter__.return_value = mock_source
    cm.__exit__.return_value = False
    return cm


# Enrollment loop helpers
_ENROLL_FRAME_LENGTH = 512          # matches typical pveagle frame_length
_ENROLL_SAMPLE_RATE = VoiceRecognizer.SAMPLE_RATE if VoiceRecognizer else 16000
_MIN_BYTES = _ENROLL_FRAME_LENGTH * 2 * 8   # = 8192 — the too-short threshold


def _mock_biometrics() -> MagicMock:
    """Biometrics stub that reports itself available with concrete int attributes."""
    vb = MagicMock()
    vb.is_available.return_value = True
    vb.sample_rate = _ENROLL_SAMPLE_RATE
    vb.frame_length = _ENROLL_FRAME_LENGTH
    vb.has_profile.return_value = False
    return vb


def _good_audio() -> "sr.AudioData":
    """Audio that satisfies both length (>= min_bytes) and voice-level (mean_abs >= 55) gates."""
    samples = np.full(_ENROLL_FRAME_LENGTH * 16, 1000, dtype=np.int16)
    return sr.AudioData(samples.tobytes(), _ENROLL_SAMPLE_RATE, 2)


def _short_audio() -> "sr.AudioData":
    """Audio shorter than frame_length * 2 * 8 bytes → triggers AUDIO_TOO_SHORT branch."""
    return sr.AudioData(bytes(100), _ENROLL_SAMPLE_RATE, 2)


def _quiet_audio() -> "sr.AudioData":
    """Long-enough but all-zero audio → triggers 'No clear voice detected' branch."""
    return sr.AudioData(bytes(_MIN_BYTES * 2), _ENROLL_SAMPLE_RATE, 2)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@unittest.skipIf(
    VoiceRecognizer is None or not _SR_OK,
    "VoiceRecognizer or SpeechRecognition unavailable in this environment",
)
class TestVoiceEnrollCalibrate(unittest.TestCase):

    # ------------------------------------------------------------------ #
    # calibrate_noise                                                     #
    # ------------------------------------------------------------------ #

    def test_TC_ENROLL_01_calibrate_returns_bool_without_mic(self):
        """calibrate_noise always returns bool and never raises, even without a physical mic."""
        vr = _build_vr()
        result = vr.calibrate_noise(duration=0.1)
        self.assertIsInstance(result, bool)

    def test_TC_ENROLL_02_calibrate_returns_true_with_patched_mic(self):
        """calibrate_noise returns True and calls adjust_for_ambient_noise when mic is available."""
        vr = _build_vr()
        source = MagicMock()
        with patch("speech_recognition.Microphone", return_value=_patch_mic(source)):
            with patch.object(vr.recognizer, "adjust_for_ambient_noise") as mock_adj:
                result = vr.calibrate_noise(duration=0.5)
        self.assertTrue(result)
        mock_adj.assert_called_once_with(source, duration=0.5)

    def test_TC_ENROLL_03_calibrate_clamps_zero_duration_to_0_1(self):
        """calibrate_noise clamps duration=0.0 to a minimum of 0.1 before the underlying call."""
        vr = _build_vr()
        source = MagicMock()
        with patch("speech_recognition.Microphone", return_value=_patch_mic(source)):
            with patch.object(vr.recognizer, "adjust_for_ambient_noise") as mock_adj:
                vr.calibrate_noise(duration=0.0)
        _, call_kwargs = mock_adj.call_args
        self.assertGreaterEqual(call_kwargs["duration"], 0.1)

    def test_TC_ENROLL_04_calibrate_returns_false_on_mic_exception(self):
        """calibrate_noise returns False (never raises) when sr.Microphone raises an OSError."""
        vr = _build_vr()
        with patch("speech_recognition.Microphone", side_effect=OSError("no device")):
            result = vr.calibrate_noise(duration=0.2)
        self.assertFalse(result)
        self.assertIsInstance(result, bool)

    # ------------------------------------------------------------------ #
    # run_pre_enrollment_diagnostics                                      #
    # ------------------------------------------------------------------ #

    def test_TC_ENROLL_05_diagnostics_required_keys_always_present(self):
        """run_pre_enrollment_diagnostics always returns a dict with all five required keys."""
        vr = _build_vr()
        # No-mic path exercises the exception branch which returns the default dict.
        result = vr.run_pre_enrollment_diagnostics(duration=0.1)
        for key in ("ok", "rms", "peak", "clipping_ratio", "message"):
            self.assertIn(key, result, f"Missing required key in diagnostics: {key}")

    def test_TC_ENROLL_06_diagnostics_no_mic_returns_ok_false_with_message(self):
        """run_pre_enrollment_diagnostics returns ok=False with a non-empty message when mic is absent."""
        vr = _build_vr()
        with patch("speech_recognition.Microphone", side_effect=OSError("no device")):
            result = vr.run_pre_enrollment_diagnostics(duration=0.1)
        self.assertFalse(result["ok"])
        self.assertGreater(len(result["message"]), 0)

    # Helper: inject synthetic audio into the diagnostics method.
    def _diag_with_audio(self, vr, audio_np: np.ndarray) -> dict:
        audio_data = _make_audio_data(audio_np)
        source = MagicMock()
        with patch("speech_recognition.Microphone", return_value=_patch_mic(source)):
            with patch.object(vr.recognizer, "adjust_for_ambient_noise"):
                with patch.object(vr.recognizer, "record", return_value=audio_data):
                    return vr.run_pre_enrollment_diagnostics(duration=0.5)

    def test_TC_ENROLL_07_diagnostics_silent_audio_reports_too_quiet(self):
        """All-zero audio (rms=0) triggers the 'too quiet' diagnostic message and ok=False."""
        vr = _build_vr()
        silent = np.zeros(VoiceRecognizer.SAMPLE_RATE, dtype=np.int16)
        result = self._diag_with_audio(vr, silent)
        self.assertFalse(result["ok"])
        self.assertIn("quiet", result["message"].lower())

    def test_TC_ENROLL_08_diagnostics_clipping_audio_reports_clipping(self):
        """Fully-saturated audio (all ±32767, clipping_ratio=1.0 > 0.08) triggers the clipping message."""
        vr = _build_vr()
        clipping = np.full(VoiceRecognizer.SAMPLE_RATE, 32767, dtype=np.int16)
        result = self._diag_with_audio(vr, clipping)
        self.assertFalse(result["ok"])
        self.assertIn("clipping", result["message"].lower())

    def test_TC_ENROLL_09_diagnostics_healthy_audio_passes(self):
        """Injected healthy audio (rms ~0.17, peak ~0.3, no clipping) returns ok=True."""
        vr = _build_vr()
        # Uniform random ints in ±10000: rms≈0.17, peak≈0.30, clipping_ratio=0.0 → passes all gates.
        rng = np.random.default_rng(42)
        healthy = rng.integers(-10000, 10000, size=VoiceRecognizer.SAMPLE_RATE, dtype=np.int16)
        result = self._diag_with_audio(vr, healthy)
        self.assertTrue(result["ok"], f"Expected ok=True for healthy audio, got: {result}")
        self.assertGreater(result["rms"], 0.0)
        self.assertGreater(result["peak"], 0.0)
        self.assertEqual(result["clipping_ratio"], 0.0)

    # ------------------------------------------------------------------ #
    # enroll_speaker_profile                                              #
    # ------------------------------------------------------------------ #

    def test_TC_ENROLL_10_enroll_returns_false_str_when_no_biometrics(self):
        """enroll_speaker_profile returns (False, non-empty str) immediately when biometrics is None."""
        vr = _build_vr()
        vr.voice_biometrics = None
        success, message = vr.enroll_speaker_profile(samples=3)
        self.assertFalse(success)
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)

    def test_TC_ENROLL_11_enroll_resets_enrollment_active_flag_after_failure(self):
        """_enrollment_active is always False after enroll_speaker_profile returns, even on failure."""
        vr = _build_vr()
        vr.voice_biometrics = None
        vr._enrollment_active = False
        vr.enroll_speaker_profile(samples=2)
        self.assertFalse(vr._enrollment_active)

    def test_TC_ENROLL_12_enroll_surfaces_biometrics_unavailable_reason(self):
        """When biometrics.is_available() is False, the returned message contains the reason string."""
        vr = _build_vr()
        mock_vb = MagicMock()
        mock_vb.is_available.return_value = False
        mock_vb.get_unavailable_reason.return_value = "pveagle license not found"
        vr.voice_biometrics = mock_vb
        success, message = vr.enroll_speaker_profile(samples=3)
        self.assertFalse(success)
        self.assertIn("pveagle license not found", message)

    def test_TC_ENROLL_13_enroll_progress_callback_not_invoked_on_fast_fail(self):
        """progress_callback is never called when biometrics is unavailable (enrollment fast-fails)."""
        vr = _build_vr()
        vr.voice_biometrics = None
        callback = MagicMock()
        vr.enroll_speaker_profile(samples=3, progress_callback=callback)
        callback.assert_not_called()

    # ------------------------------------------------------------------ #
    # enroll_speaker_profile — PRODUCTION LOOP coverage                  #
    # (TC-ENROLL-10..13 only hit the fast-fail guard; these tests drive   #
    #  the real audio-processing and streak-tracking loop body.)          #
    # ------------------------------------------------------------------ #

    def _run_enroll(self, vr, record_side_effect, enroll_bytes_side_effect=None, samples=2, callback=None):
        """Drive enroll_speaker_profile with a fully mocked mic + biometrics."""
        vr.voice_biometrics = _mock_biometrics()
        if enroll_bytes_side_effect is not None:
            vr.voice_biometrics.enroll_audio_bytes.side_effect = enroll_bytes_side_effect
        source = MagicMock()
        with patch("speech_recognition.Microphone", return_value=_patch_mic(source)):
            with patch.object(vr.recognizer, "adjust_for_ambient_noise"):
                with patch.object(vr.recognizer, "record", side_effect=record_side_effect):
                    return vr.enroll_speaker_profile(samples=samples, progress_callback=callback)

    def test_TC_ENROLL_14_enroll_succeeds_when_biometrics_returns_100_percent(self):
        """
        Production happy-path: mic available, good audio, biometrics returns 100% on first
        sample → enroll_speaker_profile returns (True, success message).
        This test was absent before; TC-ENROLL-10..13 never entered the loop body.
        """
        vr = _build_vr()
        success, message = self._run_enroll(
            vr,
            record_side_effect=[_good_audio()] * 20,
            enroll_bytes_side_effect=[(100.0, "ok")],
        )
        self.assertTrue(success, f"Expected True but got False: {message}")
        self.assertIn("enrolled successfully", message.lower())

    def test_TC_ENROLL_15_enrollment_active_flag_true_inside_callback(self):
        """
        _enrollment_active must be True while the loop is running (production guards against
        concurrent listen calls during enrollment). The progress callback captures the flag.
        """
        vr = _build_vr()
        flag_states = []

        def capture_callback(current, total, pct):
            flag_states.append(vr._enrollment_active)

        self._run_enroll(
            vr,
            record_side_effect=[_good_audio()] * 20,
            enroll_bytes_side_effect=[(100.0, "ok")],
            callback=capture_callback,
        )
        self.assertTrue(
            any(flag_states),
            "_enrollment_active was never True during the enrollment loop.",
        )
        self.assertFalse(vr._enrollment_active, "_enrollment_active not reset to False after completion.")

    def test_TC_ENROLL_16_too_short_audio_streak_returns_false(self):
        """
        10 consecutive AUDIO_TOO_SHORT chunks → enroll_speaker_profile returns (False, message)
        mentioning the short-audio cause. This matches the real production failure when the mic
        captures near-silence clips or the buffer is undersized.
        """
        vr = _build_vr()
        success, message = self._run_enroll(
            vr,
            record_side_effect=[_short_audio()] * 30,
        )
        self.assertFalse(success)
        self.assertTrue(
            any(word in message.lower() for word in ("short", "audio", "4 second")),
            f"Expected short-audio failure message, got: {message}",
        )

    def test_TC_ENROLL_17_too_quiet_audio_streak_returns_false(self):
        """
        10 consecutive below-threshold (silent) chunks → enroll_speaker_profile returns
        (False, message) mentioning voice detection. This is the most common production
        failure — mic gain too low or user stops speaking between samples.
        """
        vr = _build_vr()
        success, message = self._run_enroll(
            vr,
            record_side_effect=[_quiet_audio()] * 30,
        )
        self.assertFalse(success)
        self.assertTrue(
            any(word in message.lower() for word in ("voice", "speak", "mic")),
            f"Expected quiet-audio failure message, got: {message}",
        )

    def test_TC_ENROLL_18_enroll_bytes_returning_none_streak_returns_false(self):
        """
        Good audio reaches enroll_audio_bytes, but it returns None 10+ times
        (e.g., pveagle frame validation fails internally) → returns (False, message)
        referencing unusable voice frames.
        """
        vr = _build_vr()
        success, message = self._run_enroll(
            vr,
            record_side_effect=[_good_audio()] * 30,
            enroll_bytes_side_effect=[(None, "")] * 30,
        )
        self.assertFalse(success)
        self.assertTrue(
            any(word in message.lower() for word in ("frame", "voice", "microphone")),
            f"Expected usable-frames failure message, got: {message}",
        )

    def test_TC_ENROLL_19_bad_feedback_streak_from_biometrics_returns_false(self):
        """
        enroll_audio_bytes returns a non-None percent but feedback='TOO_SHORT' with
        non-increasing percent (typical pveagle response when audio is marginal) → streak
        counter increments and eventually fails. Validates the feedback-parsing branch.
        """
        vr = _build_vr()
        # Same low percent every time, feedback always TOO_SHORT → best_percent never
        # advances → streak keeps incrementing until it hits 10.
        success, message = self._run_enroll(
            vr,
            record_side_effect=[_good_audio()] * 30,
            enroll_bytes_side_effect=[(10.0, "AUDIO_TOO_SHORT")] * 30,
        )
        self.assertFalse(success)
        self.assertGreater(len(message), 0)


if __name__ == "__main__":
    unittest.main()
