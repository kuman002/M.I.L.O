"""
MILO Voice Recognition - Optimized Version
Integrates GPU-accelerated Whisper with existing MILO structure
"""

import os
import threading
import speech_recognition as sr
import time
import sys
from typing import Optional, Dict, Tuple, Callable

# Try to import whisper, fallback to None if not available
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    try:
        print("WARNING: openai-whisper not installed. Install with: pip install openai-whisper", file=sys.stderr)
    except:
        pass

# Try to import torch, fallback to None if not available
try:
    import torch
except ImportError:
    torch = None

# Try to import numpy, fallback to None if not available
try:
    import numpy as np
except ImportError:
    np = None

# Configuration
TEMP_FILENAME = "temp_voice.wav"

class VoiceRecognizer:
    """
    Optimized Voice Recognition for MILO
    - GPU acceleration (if available)
    - Command-based recognition
    - Wake word detection ("Hey Milo")
    - Confidence scoring
    """
    
    # Command mappings for MILO
    COMMANDS = {
        # Task management
        "add task": "ADD_TASK",
        "create task": "ADD_TASK",
        "new task": "ADD_TASK",
        "delete task": "DELETE_TASK",
        "remove task": "DELETE_TASK",
        "complete task": "COMPLETE_TASK",
        "finish task": "COMPLETE_TASK",
        
        # Finance tracking
        "add expense": "ADD_EXPENSE",
        "add income": "ADD_INCOME",
        "check balance": "CHECK_BALANCE",
        "show balance": "CHECK_BALANCE",
        
        # Habit tracking
        "add habit": "ADD_HABIT",
        "create habit": "ADD_HABIT",
        "create a habit": "ADD_HABIT",
        "create a new habit": "ADD_HABIT",
        "new habit": "ADD_HABIT",
        "start habit": "ADD_HABIT",
        "begin habit": "ADD_HABIT",
        "log habit": "LOG_HABIT",
        "log my habit": "LOG_HABIT",
        "track habit": "LOG_HABIT",
        
        # Reminder commands (with relative time - handled specially)
        "remind me": "REMIND_ME",
        "set reminder": "REMIND_ME",
        "add reminder": "REMIND_ME",
        
        # System commands
        "open browser": "OPEN_BROWSER",
        "close window": "CLOSE_WINDOW",
        "shutdown": "SHUTDOWN",
        "refresh": "REFRESH",
        
        # Wake word
        "hey milo": "WAKE_WORD",
        "hello milo": "WAKE_WORD",
        "hi milo": "WAKE_WORD",
    }
    
    def __init__(
        self,
        model_size: str = "medium",
        device: Optional[str] = None,
        language: str = "en"
    ):
        """
        Initialize MILO Voice Recognition
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: 'cuda' for GPU, 'cpu' for CPU (auto-detect if None)
            language: Language code (default: English)
        """
        print("[Voice] Initializing MILO Voice Recognition...")
        
        self.model = None
        self.device = None
        self.language = language
        
        # Initialize threading/listening early (always needed)
        self.is_listening = False
        self._stop_event = threading.Event()
        self.recognizer = sr.Recognizer()
        # Optimized settings for faster recognition
        self.recognizer.energy_threshold = 400  # Increased from 300 for better noise filtering
        self.recognizer.pause_threshold = 0.5   # Reduced from 0.8 for faster response
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.phrase_threshold = 0.2  # Lower for faster start
        self.recognizer.non_speaking_duration = 0.3  # Faster detection of end of speech
        
        # Check if whisper is available
        if not WHISPER_AVAILABLE:
            print("[Voice] ERROR: openai-whisper not installed")
            print("[Voice] Install with: pip install openai-whisper")
            return
        
        # Auto-detect device
        if device is None:
            self.device = "cuda" if (torch and torch.cuda.is_available()) else "cpu"
        else:
            self.device = device
        
        print(f"[Voice] Device: {self.device.upper()}")
        
        if self.device == "cuda" and torch:
            try:
                print(f"[Voice] GPU: {torch.cuda.get_device_name(0)}")
            except:
                pass
        
        # Load Whisper model
        print(f"[Voice] Loading Whisper {model_size} model...")
        try:
            self.model = whisper.load_model(model_size, device=self.device)
            print("[Voice] Model loaded successfully!")
        except Exception as e:
            print(f"[Voice] ERROR: Failed to load model: {e}")
            print("[Voice] Make sure openai-whisper is installed: pip install openai-whisper")
            self.model = None
            return
        
        self.sample_rate = 16000  # Whisper's native sample rate
        
        # Performance settings - Optimized for speed
        self.fp16 = self.device == "cuda"  # Use FP16 on GPU for 2x speed boost
        self.temperature = 0.0  # Prevent hallucinations
        self.no_speech_threshold = 0.6  # Filter silence
        self.beam_size = 1  # Faster decoding (greedy search instead of beam search)
        self.best_of = 1  # Don't generate multiple candidates
        
        # Command prompt for better accuracy with common MILO commands
        self.initial_prompt = (
            "MILO voice assistant. Commands: add task, create task, add expense, "
            "check balance, add habit, create habit, log habit, track habit, remind me, refresh. "
            "Examples: add habit read, create a new habit exercise, log habit meditate."
        )
        
        print("[Voice] Voice Recognition Ready!")
    
    def is_available(self) -> bool:
        """Check if voice recognition is ready"""
        return self.model is not None
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_listening()
        if os.path.exists(TEMP_FILENAME):
            try:
                os.remove(TEMP_FILENAME)
            except:
                pass
    
    def calibrate_noise(self, duration: float = 3.0) -> bool:
        """Calibrate ambient noise levels"""
        try:
            with sr.Microphone() as source:
                print(f"🎤 Calibrating noise for {duration} seconds...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                print(f"✅ Calibration complete. Threshold: {self.recognizer.energy_threshold}")
                return True
        except Exception as e:
            print(f"❌ Calibration failed: {e}")
            return False
    
    def transcribe_audio_file(self, audio_file: str) -> Dict[str, any]:
        """
        Transcribe audio file using Whisper
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Dictionary with transcription and metadata
        """
        if not self.is_available():
            return {"text": "", "success": False, "error": "Model not loaded"}
        
        try:
            # Transcribe with optimized settings for speed
            result = self.model.transcribe(
                audio_file,
                language=self.language,
                fp16=self.fp16,
                temperature=self.temperature,
                initial_prompt=self.initial_prompt,
                no_speech_threshold=self.no_speech_threshold,
                beam_size=self.beam_size,  # Use greedy search for 2-3x speed boost
                best_of=self.best_of,  # Don't generate multiple candidates
                condition_on_previous_text=False  # Don't use previous context (faster)
            )
            
            text = result["text"].strip()
            
            return {
                "text": text,
                "language": result.get("language", self.language),
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return {"text": "", "success": False, "error": str(e)}
    
    def detect_command(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Detect command from transcribed text
        
        Args:
            text: Transcribed text
            
        Returns:
            Tuple of (command_id, matched_phrase) or None
        """
        text_lower = text.lower()
        
        for phrase, command_id in self.COMMANDS.items():
            if phrase in text_lower:
                return (command_id, phrase)
        
        return None
    
    def parse_reminder_command(self, text: str) -> Optional[Dict[str, any]]:
        """
        Parse reminder commands with relative time
        Examples: 'remind me in 10 seconds', 'remind me to call mom in 5 minutes'
        
        Args:
            text: Full command text
            
        Returns:
            Dict with 'message' and 'seconds' or None
        """
        import re
        import datetime
        
        text_lower = text.lower()
        
        # Try to match "remind me [to <action>] in <time>"
        # Pattern: remind me [to <action>] in <number> <unit>
        pattern = r"remind\s+me\s+(?:to\s+)?(.+?)\s+in\s+(\d+)\s+(second|minute|hour)s?"
        match = re.search(pattern, text_lower)
        
        if match:
            message = match.group(1).strip()
            time_value = int(match.group(2))
            time_unit = match.group(3).lower()
            
            # Convert to seconds
            if time_unit == "second":
                seconds = time_value
            elif time_unit == "minute":
                seconds = time_value * 60
            elif time_unit == "hour":
                seconds = time_value * 3600
            else:
                return None
            
            # Calculate target datetime
            now = datetime.datetime.now()
            target_time = now + datetime.timedelta(seconds=seconds)
            
            # Format: YYYY-MM-DD HH:MM
            datetime_str = target_time.strftime("%Y-%m-%d %H:%M")
            
            print(f"[Voice] Parsed reminder: '{message}' at {datetime_str} (in {seconds}s)")
            
            return {
                'message': message,
                'datetime': datetime_str,
                'seconds': seconds
            }
        
        return None
    
    def listen_once(self, timeout: float = 5.0) -> str:
        """
        Listen for a single command
        
        Args:
            timeout: Maximum time to wait for audio
            
        Returns:
            Transcribed text
        """
        if not self.is_available():
            print("❌ Voice recognition not available")
            return ""
        
        try:
            with sr.Microphone() as source:
                print("🎤 Listening...")
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen
                audio_data = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
                print("⚡ Thinking...")
                
                # Save audio
                with open(TEMP_FILENAME, "wb") as f:
                    f.write(audio_data.get_wav_data())
                
                # Transcribe
                result = self.transcribe_audio_file(TEMP_FILENAME)
                
                # Cleanup
                if os.path.exists(TEMP_FILENAME):
                    try:
                        os.remove(TEMP_FILENAME)
                    except:
                        pass
                
                if result["success"]:
                    text = result["text"]
                    if text:
                        print(f"📝 Heard: '{text}'")
                        return text
                
                return ""
                
        except sr.WaitTimeoutError:
            print("⏱️ Timeout - no speech detected")
            return ""
        except Exception as e:
            print(f"❌ Error: {e}")
            return ""
    
    def start_listening(self, callback: Callable[[str], None]):
        """
        Start continuous listening in background thread
        
        Args:
            callback: Function to call with transcribed text
        """
        if not self.is_available():
            print("❌ Voice recognition not available")
            return False
        
        self.is_listening = True
        self._stop_event.clear()
        
        # Run in daemon thread
        thread = threading.Thread(target=self._listen_loop, args=(callback,), daemon=True)
        thread.start()
        return True
    
    def stop_listening(self):
        """Stop continuous listening"""
        self.is_listening = False
        self._stop_event.set()
    
    def _listen_loop(self, callback: Callable[[str], None]):
        """Continuous listening loop"""
        print("🎧 Continuous listening started...")
        
        try:
            with sr.Microphone() as source:
                # Initial adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                while self.is_listening and not self._stop_event.is_set():
                    text = self._listen_and_transcribe(source)
                    if text:
                        callback(text)
                    
                    # Small sleep to yield thread
                    time.sleep(0.005)
                    
        except Exception as e:
            print(f"❌ Microphone error: {e}")
            self.is_listening = False
    
    def _listen_and_transcribe(self, source) -> str:
        """
        Listen and transcribe from microphone source
        
        Args:
            source: Microphone source
            
        Returns:
            Transcribed text
        """
        if self._stop_event.is_set():
            return ""
        
        try:
            # Listen with timeout
            audio_data = self.recognizer.listen(source, timeout=1.0, phrase_time_limit=10)
            
            print("⚡ Thinking...")
            
            # Save audio
            with open(TEMP_FILENAME, "wb") as f:
                f.write(audio_data.get_wav_data())
            
            if self._stop_event.is_set():
                return ""
            
            # Transcribe
            result = self.transcribe_audio_file(TEMP_FILENAME)
            
            # Cleanup
            if os.path.exists(TEMP_FILENAME):
                try:
                    os.remove(TEMP_FILENAME)
                except:
                    pass
            
            if result["success"]:
                text = result["text"]
                if text:
                    print(f"📝 Heard: '{text}'")
                    return text
            
            return ""
            
        except sr.WaitTimeoutError:
            # Silence - continue loop
            return ""
        except Exception as e:
            print(f"❌ Error processing audio: {e}")
            return ""
    
    def get_performance_stats(self) -> Dict[str, str]:
        """Get performance statistics"""
        return {
            "device": self.device,
            "fp16_enabled": self.fp16,
            "language": self.language,
            "sample_rate": self.sample_rate,
            "gpu_name": torch.cuda.get_device_name(0) if self.device == "cuda" else "N/A",
            "model_available": self.is_available()
        }


# Backward compatibility alias
VoiceRecognition = VoiceRecognizer
