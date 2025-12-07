"""
Module: voice_engine.py
Description: High-Accuracy Offline Speech Recognition using Faster-Whisper.
"""
import logging
import os
import pyttsx3
import speech_recognition as sr
from faster_whisper import WhisperModel

# --- CONFIGURATION ---
# Options: "tiny", "base", "small", "medium"
# "base.en" is a great balance of speed and accuracy for laptops.
# "small.en" is smarter but slower.
MODEL_SIZE = "base.en" 
DEVICE = "cpu" # Change to "cuda" if you have an NVIDIA GPU
COMPUTE_TYPE = "int8" # "float16" for GPU, "int8" for CPU

class VoiceEngine:
    def __init__(self):
        print(f"--- INITIALIZING VOICE ENGINE ({MODEL_SIZE}) ---")
        
        # 1. Load the Whisper Model
        try:
            print("Loading Faster-Whisper model... (First run downloads data)")
            self.model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
            print("Model Loaded Successfully.")
        except Exception as e:
            logging.error(f"Failed to load Whisper: {e}")
            raise

        # 2. Initialize Microphone (SpeechRecognition)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Calibrate for noise immediately
        with self.microphone as source:
            print("Adjusting for ambient noise... (Please stay silent for 1s)")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.recognizer.dynamic_energy_threshold = True

    def listen_for_command(self):
        """
        Records audio until silence is detected, then transcribes.
        """
        print("\nListening... (Speak now)", end="", flush=True)
        
        try:
            with self.microphone as source:
                # This automatically waits for you to stop speaking!
                # timeout=5 means it waits 5s for you to START talking.
                # phrase_time_limit=10 means it cuts you off after 10s.
                audio_data = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            print("\nProcessing...", end="", flush=True)
            
            # Save to temporary file because Whisper reads files best
            with open("temp_command.wav", "wb") as f:
                f.write(audio_data.get_wav_data())

            # Transcribe
            segments, info = self.model.transcribe("temp_command.wav", beam_size=5)
            
            # Combine all segments into one string
            text = " ".join([segment.text for segment in segments]).strip()
            
            if text:
                print(f"\n✅ Recognized: '{text}'")
                
                # Cleanup
                if os.path.exists("temp_command.wav"):
                    os.remove("temp_command.wav")
                    
                return text
                
        except sr.WaitTimeoutError:
            print("\nTimeout: No speech detected.")
            return None
        except Exception as e:
            print(f"\nError: {e}")
            return None

    def speak(self, text):
        print(f"\n🤖 Milo: {text}")
        try:
            # Re-initialize engine to avoid audio driver conflicts
            engine = pyttsx3.init(driverName='sapi5')
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
            del engine
        except Exception as e:
            print(f"TTS Error: {e}")