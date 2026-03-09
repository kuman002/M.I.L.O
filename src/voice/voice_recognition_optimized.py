"""
MILO Voice Recognition - High-Accuracy Recognition Engine
Optimized for Indian-English command recognition, aggressive anti-hallucination,
and sub-second RAM-based transcription.
"""

import datetime
import os
import re
import sys
import threading
import time
from functools import lru_cache
from typing import Any, Callable, Dict, Optional, Tuple

import numpy as np
import speech_recognition as sr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    print("WARNING: rapidfuzz not installed. Fuzzy matching disabled.", file=sys.stderr)

try:
    from faster_whisper import BatchedInferencePipeline, WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    BatchedInferencePipeline = None
    print("WARNING: faster-whisper not installed.", file=sys.stderr)

try:
    import torch
except ImportError:
    torch = None


# ---------------------------------------------------------------------------
# Pre-compiled phonetic replacement rules (Indian-English accent)
# ---------------------------------------------------------------------------
_INDIAN_ENGLISH_REGEX_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(google|gugel|gugle)\b"),                                             "google"),
    (re.compile(r"\b(remindar|remainder|remeender)\b"),                                   "reminder"),
    (re.compile(r"\b(expence|expans|expenses)\b"),                                        "expense"),
    (re.compile(r"\b(balans|balance)\b"),                                                 "balance"),
    (re.compile(r"\b(slaid|slite)\b"),                                                    "slide"),
    (re.compile(r"\b(previus|pervious)\b"),                                               "previous"),
    (re.compile(r"\b(toss)\b"),                                                           "task"),
    (re.compile(r"\b(todo)\b"),                                                           "to do"),
    (re.compile(r"\b(add a toss|add it ask|had a task|had it asked)\b"),                 "add task"),
    (re.compile(r"\b(check my balans|check ma balance)\b"),                               "check balance"),
    (re.compile(r"\b(go previous|go to previous)\b"),                                     "previous"),
    (re.compile(r"\b(move next)\b"),                                                      "next"),
    (re.compile(r"\b(note\s*pad|not\s*pad|not\s*bad|north\s*bad|noth\s*bad|noths\s*bad|north\s*pad)\b"), "notepad"),
    (re.compile(r"\b(i ask)\b"),                                                          "task"),
    (re.compile(r"\b(b\.m\.|b\.m|b m)\b"),                                               "pm"),
    (re.compile(r"\b(a\.m\.|a\.m|a m)\b"),                                               "am"),
    (re.compile(r"\b(worth)\b"),                                                          "for"),
    (re.compile(r"\b(your feet|my being)\b"),                                             ""),
    (re.compile(r"\b(rupees|rupess|rupee|rs\.?|inr)\b"),                                  "rupees"),
    (re.compile(r"\b(kharcha|karcha|expensea)\b"),                                          "expense"),
    (re.compile(r"\b(remind me na|remind me please)\b"),                                    "remind me"),
    (re.compile(r"\b(checking balance|check the balance)\b"),                               "check balance"),
]

_PHANTOM_ARTIFACTS: frozenset[str] = frozenset({"you", "the", "thank you", "thanks", "a", "i", "it", "okay", "ok"})
_SAFE_SHORT_WORDS: frozenset[str] = frozenset({"hi", "no", "yes", "go", "do", "next", "back"})
_FILLER_RE = re.compile(r"^(ha|ah|uh|um)+$")
_NON_ASCII_RE = re.compile(r"[^\x00-\x7F]+")

# Relative time: "in 5 minutes", "3 hours"
_REL_TIME_RE = re.compile(r"(?:in\s+)?(\d+)\s*(second|seconds|minute|minutes|hour|hours|day|days)\b")
# Absolute time: "at 3:30 pm"
_ABS_TIME_RE = re.compile(r"\bat\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b")
_REMINDER_STRIP_RE = re.compile(r"\b(remind me|set reminder|add reminder)\b")


class VoiceRecognizer:
    SAMPLE_RATE = 16000
    SAMPLE_WIDTH = 2

    HOTWORDS = [
        "task", "reminder", "expense", "balance", "slide", "previous", "next",
        "google", "search", "browser", "refresh", "milo", "rupees", "inr", "kharcha",
    ]

    KEYWORD_COMMAND_MAP: dict[str, str] = {
        "task":    "ADD_TASK",
        "expense": "ADD_EXPENSE",
        "reminder":"REMIND_ME",
        "slide":   "NEXT_SLIDE",
        "balance": "CHECK_BALANCE",
        "google":  "GOOGLE_SEARCH",
    }

    COMMANDS: dict[str, str] = {
        "task add": "ADD_TASK",       "add task": "ADD_TASK",
        "create task": "ADD_TASK",    "add to do": "ADD_TASK",
        "to do add": "ADD_TASK",      "new task": "ADD_TASK",
        "expense add": "ADD_EXPENSE", "add expense": "ADD_EXPENSE",
        "log expense": "ADD_EXPENSE", "spent": "ADD_EXPENSE",
        "add spending": "ADD_EXPENSE", "add kharcha": "ADD_EXPENSE",
        "log kharcha": "ADD_EXPENSE", "log spending": "ADD_EXPENSE",
        "reminder put": "REMIND_ME",  "set reminder": "REMIND_ME",
        "add reminder": "REMIND_ME",  "remind me": "REMIND_ME",
        "remind me at": "REMIND_ME",  "remind me in": "REMIND_ME",
        "next slide": "NEXT_SLIDE",   "move next slide": "NEXT_SLIDE",
        "move forward": "NEXT_SLIDE", "slide next": "NEXT_SLIDE",
        "previous slide": "PREV_SLIDE", "go previous slide": "PREV_SLIDE",
        "go back": "PREV_SLIDE",      "slide previous": "PREV_SLIDE",
        "check balance": "CHECK_BALANCE", "show balance": "CHECK_BALANCE",
        "balance check": "CHECK_BALANCE", "check my balance": "CHECK_BALANCE",
        "what is my balance": "CHECK_BALANCE", "how much balance": "CHECK_BALANCE",
        "google search": "GOOGLE_SEARCH", "search in google": "GOOGLE_SEARCH",
        "search google": "GOOGLE_SEARCH", "search": "GOOGLE_SEARCH",
        "open browser": "OPEN_BROWSER", "close window": "CLOSE_WINDOW",
        "shutdown": "SHUTDOWN",         "refresh": "REFRESH",
        "hey milo": "WAKE_WORD",        "hello milo": "WAKE_WORD",
        "hi milo": "WAKE_WORD",         "milo": "WAKE_WORD",
    }

    MODEL_ALIASES: dict[str, str] = {
        "tiny":      "Systran/faster-whisper-tiny",
        "tiny.en":   "Systran/faster-whisper-tiny.en",
        "base":      "Systran/faster-whisper-base",
        "base.en":   "Systran/faster-whisper-base.en",
        "small":     "Systran/faster-whisper-small",
        "small.en":  "Systran/faster-whisper-small.en",
        "medium":    "Systran/faster-whisper-medium",
        "medium.en": "Systran/faster-whisper-medium.en",
        "large-v1":  "Systran/faster-whisper-large-v1",
        "large-v2":  "Systran/faster-whisper-large-v2",
        "large-v3":  "Systran/faster-whisper-large-v3",
    }

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    @classmethod
    def _resolve_model_source(cls, model_size: str) -> str:
        if model_size in cls.MODEL_ALIASES:
            if os.path.isdir(model_size):
                print(f"[Voice] Local folder '{model_size}' shadowed by remote alias.")
            return cls.MODEL_ALIASES[model_size]
        return model_size

    def __init__(
        self,
        model_size: str = "small",
        device: Optional[str] = None,
        language: Optional[str] = "en",
    ) -> None:
        print("[Voice] Initializing High-Accuracy Voice Engine...")

        self.model: Optional[WhisperModel] = None
        self.batched_model = None
        self.language = language
        self.is_listening = False
        self._stop_event = threading.Event()
        self._last_calibration_ts = 0.0
        self.initial_prompt = (
            "MILO voice assistant. Indian English accent context. "
            "Common phrases: add task, create task, add expense, log kharcha, set reminder, remind me in, remind me at, "
            "check my balance, what is my balance, google search, open browser, next slide, previous slide, refresh. "
            "Currency words: rupees, INR."
        )
        self._hotwords_csv = ", ".join(self.HOTWORDS)
        self._command_items = tuple(self.COMMANDS.items())
        self._keyword_items = tuple(self.KEYWORD_COMMAND_MAP.items())
        self._command_first_tokens = tuple(
            (phrase, cmd_id, phrase.split(" ", 1)[0]) for phrase, cmd_id in self._command_items
        )

        # Listening sensitivity/duration tuning (override with env vars if needed)
        self.listen_phrase_time_limit = float(os.getenv("MILO_LISTEN_PHRASE_LIMIT", "10.0"))
        self.listen_timeout_bg = float(os.getenv("MILO_LISTEN_TIMEOUT_BG", "1.8"))
        self.listen_timeout_once = float(os.getenv("MILO_LISTEN_TIMEOUT_ONCE", "6.0"))

        # Acoustic tuning
        rec = sr.Recognizer()
        rec.energy_threshold = 600
        rec.pause_threshold = 1.8
        rec.dynamic_energy_threshold = True
        rec.dynamic_energy_adjustment_damping = 0.10
        rec.dynamic_energy_ratio = 2.0
        rec.non_speaking_duration = 0.5          # must stay < pause_threshold
        self.recognizer = rec

        # Optional voice biometrics
        self.voice_biometrics = None
        for module_path in ("core.security", "src.core.security"):
            try:
                from importlib import import_module
                mod = import_module(module_path)
                self.voice_biometrics = mod.VoiceBiometrics()
                break
            except Exception:
                continue
        if not self.voice_biometrics:
            print("[Voice] Speaker verification unavailable.")

        if not WHISPER_AVAILABLE:
            return

        # Hardware detection
        self.device: str = device or ("cuda" if torch and torch.cuda.is_available() else "cpu")
        self.compute_type: str = (
            os.getenv("MILO_WHISPER_COMPUTE_TYPE")
            or ("int8_float16" if self.device == "cuda" else "int8")
        )
        default_threads = max(1, (os.cpu_count() or 4) - 1)
        self.cpu_threads  = int(os.getenv("MILO_WHISPER_CPU_THREADS",  str(default_threads)))
        self.num_workers  = int(os.getenv("MILO_WHISPER_NUM_WORKERS",  "2" if self.device == "cuda" else "1"))
        self.batch_size   = int(os.getenv("MILO_WHISPER_BATCH_SIZE",   "8" if self.device == "cuda" else "4"))

        print(
            f"[Voice] Hardware: {self.device.upper()} | Precision: {self.compute_type} | "
            f"Threads: {self.cpu_threads} | Workers: {self.num_workers}"
        )

        try:
            self.model = WhisperModel(
                self._resolve_model_source(model_size),
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=self.cpu_threads,
                num_workers=self.num_workers,
            )
            if BatchedInferencePipeline:
                try:
                    self.batched_model = BatchedInferencePipeline(model=self.model)
                except Exception:
                    self.batched_model = None
            print("[Voice] Neural Engine loaded successfully!")
        except Exception as e:
            print(f"[Voice] ERROR loading model: {e}")

        self._transcribe_base_kwargs: dict[str, Any] = {
            "language": self.language,
            "beam_size": 1,
            "best_of": 1,
            "temperature": 0.0,
            "vad_filter": True,
            "vad_parameters": {"min_silence_duration_ms": 450, "speech_pad_ms": 120},
            "repetition_penalty": 1.02,
            "initial_prompt": self.initial_prompt,
            "no_speech_threshold": 0.55,
            "condition_on_previous_text": False,
            "without_timestamps": True,
            "hotwords": self._hotwords_csv,
        }

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return self.model is not None

    # ------------------------------------------------------------------
    # Hallucination filter
    # ------------------------------------------------------------------

    def _is_hallucination(self, text: str) -> bool:
        t = text.lower().strip()
        if t in _PHANTOM_ARTIFACTS:
            return True
        words = t.split()
        if len(words) > 4 and len(set(words)) / len(words) < 0.35:
            return True
        if len(t) < 4 and t not in _SAFE_SHORT_WORDS:
            return True
        if _FILLER_RE.fullmatch(t):
            return True
        if len(words) == 1 and t in {"hmm", "uh", "ah"}:
            return True
        return False

    # ------------------------------------------------------------------
    # Transcript normalization (Indian-English)
    # ------------------------------------------------------------------

    def normalize_transcript(self, text: str) -> str:
        return _normalize_indian_english_cached(text or "")

    # ------------------------------------------------------------------
    # Core transcription (RAM-based, no temp files)
    # ------------------------------------------------------------------

    def transcribe_audio_memory(self, audio_data: sr.AudioData) -> Dict[str, Any]:
        if not self.is_available():
            return {"text": "", "success": False}

        try:
            wav_bytes = audio_data.get_raw_data(
                convert_rate=self.SAMPLE_RATE, convert_width=self.SAMPLE_WIDTH
            )
            audio_np = np.frombuffer(wav_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            # Too short
            if audio_np.size < int(0.35 * self.SAMPLE_RATE):
                return {"text": "", "success": False}

            # Too quiet
            rms  = float(np.sqrt(np.dot(audio_np, audio_np) / audio_np.size))
            peak = float(np.max(np.abs(audio_np)))
            if rms < 0.008 and peak < 0.04:
                return {"text": "", "success": False}

            transcribe_kwargs = dict(self._transcribe_base_kwargs)

            audio_seconds = audio_np.size / float(self.SAMPLE_RATE)
            use_batched = self.batched_model is not None and audio_seconds >= 20.0

            def _run_transcribe(**kwargs):
                if use_batched:
                    return self.batched_model.transcribe(
                        audio_np, batch_size=self.batch_size, **kwargs
                    )
                return self.model.transcribe(audio_np, **kwargs)

            try:
                segments, info = _run_transcribe(**transcribe_kwargs)
            except Exception as e:
                err = str(e).lower()
                if "strip" in err or "hotword" in err:
                    transcribe_kwargs.pop("hotwords", None)
                    segments, info = _run_transcribe(**transcribe_kwargs)
                else:
                    raise

            raw_text   = " ".join(seg.text for seg in segments).strip()
            clean_text = _NON_ASCII_RE.sub("", raw_text).strip()

            if not clean_text or self._is_hallucination(clean_text):
                return {"text": "", "success": False}

            return {
                "text":     self.normalize_transcript(clean_text),
                "language": info.language,
                "success":  True,
            }

        except Exception as e:
            print(f"❌ Transcription Error: {e}")
            return {"text": "", "success": False}

    # ------------------------------------------------------------------
    # Command detection
    # ------------------------------------------------------------------

    def detect_command(self, text: str) -> Optional[Tuple[str, str, float]]:
        t = text.lower()
        if not t:
            return None

        # 1. Exact substring match
        for phrase, cmd_id in self._command_items:
            if phrase in t:
                return (cmd_id, phrase, 100.0)

        # 2. Keyword shortcut
        for keyword, cmd_id in self._keyword_items:
            if keyword in t:
                return (cmd_id, keyword, 85.0)

        # 3. Fuzzy fallback
        if RAPIDFUZZ_AVAILABLE:
            tokens = set(t.split())
            best_score = 0.0
            best_match: Optional[Tuple[str, str, float]] = None
            for phrase, cmd_id, first_token in self._command_first_tokens:
                if first_token not in tokens and len(phrase) > 6:
                    continue
                score = float(fuzz.partial_ratio(phrase, t))
                if score > best_score:
                    best_score = score
                    best_match = (cmd_id, phrase, score)
                    if score >= 99.0:
                        break
            if best_score > 85.0 and best_match:
                return best_match

        return None

    # ------------------------------------------------------------------
    # Reminder parsing
    # ------------------------------------------------------------------

    def parse_reminder_command(self, text: str) -> Optional[Dict[str, Any]]:
        text_lower = (text or "").strip().lower()
        if not text_lower:
            return None

        now = datetime.datetime.now()

        # --- Relative time ---
        rel = _REL_TIME_RE.search(text_lower)
        if rel:
            amount = int(rel.group(1))
            unit   = rel.group(2)
            if   "second" in unit: seconds = amount
            elif "minute" in unit: seconds = amount * 60
            elif "hour"   in unit: seconds = amount * 3600
            else:                  seconds = amount * 86400

            target_time  = now + datetime.timedelta(seconds=seconds)
            message = _build_reminder_message(text_lower, rel.group(0))
            return {"message": message, "datetime": target_time.strftime("%Y-%m-%d %H:%M"), "seconds": seconds}

        # --- Absolute time ---
        abs_m = _ABS_TIME_RE.search(text_lower)
        if abs_m:
            hour     = int(abs_m.group(1))
            minute   = int(abs_m.group(2) or "0")
            meridiem = abs_m.group(3)

            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0

            if hour > 23 or minute > 59:
                return None

            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_time <= now:
                target_time += datetime.timedelta(days=1)

            seconds = max(1, int((target_time - now).total_seconds()))
            message = _build_reminder_message(text_lower, "")
            return {"message": message, "datetime": target_time.strftime("%Y-%m-%d %H:%M"), "seconds": seconds}

        return None

    # ------------------------------------------------------------------
    # Noise calibration
    # ------------------------------------------------------------------

    def calibrate_noise(self, duration: float = 2.0) -> bool:
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=max(0.1, float(duration)))
            return True
        except Exception as e:
            print(f"[Voice] Noise calibration failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Speaker enrollment
    # ------------------------------------------------------------------

    def enroll_speaker_profile(
        self,
        samples: int = 5,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
    ) -> Tuple[bool, str]:
        vb = self.voice_biometrics
        if not vb or not vb.is_available():
            reason = "Voice biometrics is unavailable."
            if vb and hasattr(vb, "get_unavailable_reason"):
                try:
                    reason = vb.get_unavailable_reason() or reason
                except Exception:
                    pass
            return False, reason

        target_samples = max(6, int(samples))
        collected      = 0
        attempts       = 0
        max_attempts   = max(18, target_samples * 4)
        best_percent   = 0.0
        last_feedback  = ""

        # Reset profiler if supported
        try:
            if hasattr(vb, "_profiler") and hasattr(vb._profiler, "reset"):
                vb._profiler.reset()
        except Exception:
            pass

        try:
            with sr.Microphone(sample_rate=vb.sample_rate) as source:
                try:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    self.recognizer.energy_threshold = max(120, int(self.recognizer.energy_threshold * 0.7))
                except Exception:
                    pass

                while collected < target_samples and attempts < max_attempts:
                    attempts += 1
                    print(f"[Voice] Enrollment sample {collected + 1}/{target_samples} - please speak...")
                    if progress_callback:
                        progress_callback(collected + 1, target_samples, best_percent)

                    try:
                        audio_data = self.recognizer.record(source, duration=4.0)
                    except sr.WaitTimeoutError:
                        continue

                    raw_audio = audio_data.get_raw_data(convert_rate=vb.sample_rate, convert_width=2)
                    if not raw_audio or len(raw_audio) < vb.frame_length * 2 * 8:
                        continue

                    audio_np = np.frombuffer(raw_audio, dtype=np.int16)
                    if audio_np.size == 0 or float(np.mean(np.abs(audio_np))) < 250.0:
                        last_feedback = "No clear voice detected"
                        continue

                    result = vb.enroll_audio_bytes(raw_audio, include_feedback=True)
                    if isinstance(result, tuple):
                        percent, feedback = result
                    else:
                        percent, feedback = result, ""

                    if percent is None:
                        continue

                    if feedback:
                        last_feedback = feedback

                    best_percent = max(best_percent, float(percent))
                    collected   += 1

                    if progress_callback:
                        progress_callback(collected, target_samples, best_percent)

                    if percent >= 100:
                        return True, "Voice profile enrolled successfully."

            if vb.has_profile():
                return True, "Voice profile enrolled successfully."

            hint = f" Last feedback: {last_feedback}." if last_feedback else ""
            return False, (
                f"Could not complete enrollment (reached {best_percent:.0f}%).{hint} "
                "Keep microphone close and speak continuously for 4 seconds per sample."
            )
        except Exception as e:
            return False, f"Voice enrollment failed: {e}"

    # ------------------------------------------------------------------
    # Speaker verification
    # ------------------------------------------------------------------

    def _verify_speaker(self, audio_data: sr.AudioData) -> bool:
        vb = self.voice_biometrics
        if not vb or not vb.is_available() or not vb.has_profile():
            return True
        try:
            raw = audio_data.get_raw_data(convert_rate=vb.sample_rate, convert_width=2)
            score = vb.verify_audio_bytes(raw)
            return True if score is None else score >= vb.threshold
        except Exception:
            return True

    # ------------------------------------------------------------------
    # Periodic recalibration
    # ------------------------------------------------------------------

    def _maybe_recalibrate(self, source, min_interval_sec: float = 45.0) -> None:
        now = time.time()
        if now - self._last_calibration_ts < min_interval_sec:
            return
        try:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.12)
            self._last_calibration_ts = now
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Single-shot listen
    # ------------------------------------------------------------------

    def listen_once(self, timeout: float = 6.0) -> str:
        if not self.is_available():
            return ""
        try:
            with sr.Microphone() as source:
                print("🎤 Listening...")
                self._maybe_recalibrate(source, min_interval_sec=20.0)
                effective_timeout = timeout if timeout is not None else self.listen_timeout_once
                audio_data = self.recognizer.listen(
                    source,
                    timeout=effective_timeout,
                    phrase_time_limit=self.listen_phrase_time_limit,
                )

                if not self._verify_speaker(audio_data):
                    print("[Voice] 🚨 Unauthorized Speaker.")
                    return ""

                print("⚡ Processing...")
                result = self.transcribe_audio_memory(audio_data)
                if result["success"] and result["text"]:
                    text = result["text"]
                    print(f"📝 Heard: '{text}'")
                    cmd = self.detect_command(text)
                    if cmd:
                        print(f"🎯 Intent Detected: {cmd[0]} (Confidence: {cmd[2]}%)")
                    return text
                return ""
        except sr.WaitTimeoutError:
            return ""
        except Exception as e:
            print(f"❌ Error: {e}")
            return ""

    # ------------------------------------------------------------------
    # Background listen loop
    # ------------------------------------------------------------------

    def start_listening(self, callback: Callable[[str], None]) -> bool:
        if not self.is_available():
            print("❌ Voice engine not available")
            return False

        if not _check_microphone():
            return False

        self.is_listening = True
        self._stop_event.clear()
        threading.Thread(target=self._listen_loop, args=(callback,), daemon=True).start()
        return True

    def stop_listening(self) -> None:
        self.is_listening = False
        self._stop_event.set()

    def cleanup(self) -> None:
        self.stop_listening()

    def _listen_loop(self, callback: Callable[[str], None]) -> None:
        print("🎧 Background listening active...")
        consecutive_errors = 0
        max_errors         = 10      # fatal threshold for assertion/mic errors
        max_soft_errors    = 50      # threshold for general errors

        while self.is_listening and not self._stop_event.is_set():
            try:
                with sr.Microphone() as source:
                    try:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        print("🎤 Mic calibrated - ready for commands!")
                    except Exception as e:
                        print(f"⚠️ Mic calibration warning: {e}")

                    while self.is_listening and not self._stop_event.is_set():
                        try:
                            self._maybe_recalibrate(source, min_interval_sec=45.0)
                            audio_data = self.recognizer.listen(
                                source,
                                timeout=self.listen_timeout_bg,
                                phrase_time_limit=self.listen_phrase_time_limit,
                            )

                            if not self._verify_speaker(audio_data):
                                continue

                            result = self.transcribe_audio_memory(audio_data)
                            if result["success"] and result["text"]:
                                print(f"🗣️ Detected: '{result['text']}'")
                                callback(result["text"])

                            consecutive_errors = 0

                        except sr.WaitTimeoutError:
                            consecutive_errors = 0   # silence is normal
                            continue

                        except AssertionError as e:
                            consecutive_errors += 1
                            if consecutive_errors == 1:
                                import traceback
                                print(f"⚠️ Audio assertion failed: {e}\n{traceback.format_exc()}")
                            if consecutive_errors >= max_errors:
                                print("❌ Mic access failed. Stopping voice recognition.")
                                self.is_listening = False
                                return
                            time.sleep(0.2)

                        except Exception as e:
                            consecutive_errors += 1
                            if consecutive_errors <= 3:
                                import traceback
                                print(f"⚠️ Listen error ({type(e).__name__}): {e}\n{traceback.format_exc()}")
                            if consecutive_errors >= max_soft_errors:
                                print(f"❌ Too many errors ({consecutive_errors}). Stopping.")
                                self.is_listening = False
                                return
                            time.sleep(0.1)

            except Exception as e:
                import traceback
                print(f"❌ Microphone open failed: {type(e).__name__}: {e}\n{traceback.format_exc()}")
                # Back off and retry opening the mic (handles transient USB disconnects)
                if not self.is_listening or self._stop_event.is_set():
                    break
                time.sleep(2.0)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=2048)
def _normalize_indian_english_cached(text: str) -> str:
    normalized = text.lower()
    for pattern, replacement in _INDIAN_ENGLISH_REGEX_MAP:
        normalized = pattern.sub(replacement, normalized)
    return normalized.strip()


def _build_reminder_message(text_lower: str, relative_fragment: str) -> str:
    msg = _REMINDER_STRIP_RE.sub("", text_lower).strip(" ,.")
    msg = re.sub(r"\bto\b", "", msg, count=1).strip(" ,.")
    if relative_fragment:
        msg = msg.replace(relative_fragment, "").strip(" ,.")
    return msg or "reminder"


def _check_microphone() -> bool:
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        has_input = any(
            p.get_device_info_by_index(i).get("maxInputChannels", 0) > 0
            for i in range(p.get_device_count())
        )
        p.terminate()
        if not has_input:
            print("❌ No microphone device found. Please connect a microphone.")
            return False
        return True
    except ImportError:
        print("⚠️ PyAudio not available - skipping mic check")
        return True
    except Exception as e:
        print(f"⚠️ Could not verify microphone: {e}")
        return True
