"""
Voice Recognition Module for MILO
Handles speech-to-text using SpeechRecognition and Faster-Whisper
"""

import os
import threading
import speech_recognition as sr
from faster_whisper import WhisperModel
import time

# Configuration matches user request
LOCAL_MODEL_PATH = os.path.join("assets", "milo_brain")
DEFAULT_MODEL_SIZE = "small"   # Upgraded from "base" for better accuracy
DEVICE = "cpu"           # "cuda" if you have NVIDIA GPU, else "cpu"
COMPUTE_TYPE = "int8"    # Optimized for speed on CPU
TEMP_FILENAME = "temp_voice.wav"

class VoiceRecognizer:
    """Voice recognition using SpeechRecognition and Faster-Whisper"""

    def __init__(self, model_size: str = DEFAULT_MODEL_SIZE):
        """Initialize the voice engine"""
        self.model = None
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self._stop_event = threading.Event()
        
        # Sensitivity settings
        self.recognizer.energy_threshold = 300 
        self.recognizer.pause_threshold = 0.8
        self.recognizer.dynamic_energy_threshold = True

        print(f"⚡ Initializing Voice Engine...")
        
        try:
            if os.path.exists(LOCAL_MODEL_PATH):
                print(f"   📂 Loading from local folder: {LOCAL_MODEL_PATH}")
                self.model = WhisperModel(LOCAL_MODEL_PATH, device=DEVICE, compute_type=COMPUTE_TYPE)
            else:
                print(f"   ⚠️ Local folder not found. Downloading/Loading '{model_size}' from cache...")
                self.model = WhisperModel(model_size, device=DEVICE, compute_type=COMPUTE_TYPE)
                
            print("✅ Voice Engine Ready.")
            
        except Exception as e:
            print(f"❌ Critical Error loading model: {e}")
            self.model = None

    def cleanup(self):
        """Cleanup resources"""
        self.stop_listening()
        
    def is_available(self) -> bool:
        """Check if voice recognition is ready"""
        return self.model is not None

    def calibrate_noise(self, duration: float = 3.0) -> bool:
        """Calibrate ambient noise levels"""
        try:
            with sr.Microphone() as source:
                print(f"🎤 Calibrating noise for {duration} seconds...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                print(f"✅ Calibration complete. New energy threshold: {self.recognizer.energy_threshold}")
                return True
        except Exception as e:
            print(f"❌ Calibration failed: {e}")
            return False

    def start_listening(self, callback):
        """Start continuous listening in a background thread"""
        if not self.is_available():
            print("❌ AI Brain is not loaded. Cannot listen.")
            return False
            
        self.is_listening = True
        self._stop_event.clear()
        
        # Run the listen loop in a daemon thread
        thread = threading.Thread(target=self._listen_loop, args=(callback,), daemon=True)
        thread.start()
        return True

    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        self._stop_event.set()

    def _listen_loop(self, callback):
        """Loop that continually listens and transcribes"""
        print("🎤 continuous listening started...")
        
        # Keep microphone open for duration of listening vs opening/closing every second
        try:
            with sr.Microphone() as source:
                # Initial adjustment for ambient noise
                # print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                while self.is_listening and not self._stop_event.is_set():
                    text = self._listen_and_transcribe(source)
                    if text:
                        callback(text)
                    
                    # Tiny sleep to yield thread
                    time.sleep(0.005)
        except Exception as e:
            print(f"❌ Microphone error: {e}")
            self.is_listening = False

    def _listen_and_transcribe(self, source) -> str:
        """
        Listens to the microphone until silence is detected,
        then uses Faster-Whisper to transcribe the audio offline.
        """
        if self._stop_event.is_set():
            return ""

        try:
            try:
                # Listen with short timeout to allow loop to check stop_event
                # But pharse_time_limit ensures we capture full commands
                # print("⚡ Listening...")
                audio_data = self.recognizer.listen(source, timeout=1.0, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                # Just silence, loop again
                return ""

            print("⚡ Thinking...")

            # Save raw audio to a temporary file
            with open(TEMP_FILENAME, "wb") as f:
                f.write(audio_data.get_wav_data())

            # --- 3. Transcribe Audio (The Brain) ---
            if self._stop_event.is_set():
                return ""

            # Transcribe with faster-whisper
            # Optimization: beam_size=5, vad_filter=True, and initial_prompt for accuracy
            segments, _ = self.model.transcribe(
                TEMP_FILENAME, 
                beam_size=5,            
                best_of=5,              
                temperature=0.0,        
                condition_on_previous_text=False, 
                vad_filter=True,        
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=400
                ), 
                repetition_penalty=1.1, 
                initial_prompt="Milo, task, create, expense, habit, balance, list, complete, delete." 
            )
            
            # Merge segments
            final_text = " ".join([segment.text for segment in segments]).strip()
            
            # --- 4. Cleanup ---
            if os.path.exists(TEMP_FILENAME):
                try:
                    os.remove(TEMP_FILENAME)
                except:
                    pass

            if final_text:
                print(f"📝 Heard: '{final_text}'")
                return final_text
            
            return ""

        except Exception as e:
            print(f"❌ Error in processing audio: {e}")
            return ""
