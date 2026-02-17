"""
Text-to-Speech Module for MILO
Handles offline text-to-speech using pyttsx3
"""

import pyttsx3
import threading
import queue
from typing import Optional


class TextToSpeech:
    """Offline text-to-speech using pyttsx3"""
    
    def __init__(self):
        """Initialize TTS engine"""
        self.engine = None
        self.is_speaking = False
        self._last_spoken = ""
        self._last_spoken_at = 0.0
        self._queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._stop_event = threading.Event()
        self._engine_lock = threading.Lock()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()
    
    def _init_engine(self):
        """Initialize pyttsx3 engine"""
        try:
            # On Windows, force SAPI5 driver (most stable).
            # Other OSes will ignore/handle accordingly.
            try:
                self.engine = pyttsx3.init(driverName="sapi5")
            except (TypeError, Exception) as e:
                # Older pyttsx3 versions may not accept driverName kwarg
                # or SAPI5 not available, try default
                try:
                    self.engine = pyttsx3.init()
                except Exception:
                    pass
            
            if not self.engine:
                print("Warning: TTS engine initialization failed")
                return
            
            # Set voice properties
            try:
                voices = self.engine.getProperty('voices')
                if voices:
                    # Try to set a female voice if available, else use first available
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                            self.engine.setProperty('voice', voice.id)
                            break
                    else:
                        self.engine.setProperty('voice', voices[0].id)
            except Exception as e:
                print(f"Warning: Could not set voice: {e}")
            
            # Set speech rate - optimized for clarity
            self.engine.setProperty('rate', 140)
            
            # Set volume - full volume for better audibility
            self.engine.setProperty('volume', 1.0)
            
        except Exception as e:
            print(f"Warning: Could not initialize TTS engine: {e}")
            self.engine = None
    
    def is_available(self) -> bool:
        """Check if TTS is available"""
        # We assume it's available if the worker is running
        return self._worker.is_alive()
    
    def speak(self, text: str, wait: bool = False):
        """
        Speak text
        
        Args:
            text: Text to speak
            wait: If True, block until speech completes
        """
        if not text or not text.strip():
            return

        text = text.strip()

        # Skip rapid duplicate messages (simple debounce)
        now = time.time()
        if text == self._last_spoken and (now - self._last_spoken_at) < 2.0:
            return
        self._last_spoken = text
        self._last_spoken_at = now
        
        if wait:
            # For blocking mode, queue the text and wait for completion
            done_event = threading.Event()
            self._queue.put(text)
            self._queue.put(("__MILO_TTS_DONE__", done_event))  # type: ignore[arg-type]
            done_event.wait(timeout=30)
        else:
            # For non-blocking mode, just queue the text
            self._queue.put(text)
    
    def stop(self):
        """Stop current speech"""
        # Best-effort: clear queued items and stop engine
        try:
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass

        with self._engine_lock:
            if self.engine:
                try:
                    self.engine.stop()
                except Exception as e:
                    print(f"Error stopping TTS: {e}")
        self.is_speaking = False
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute, default 150)"""
        with self._engine_lock:
            if self.engine:
                self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        with self._engine_lock:
            if self.engine:
                self.engine.setProperty('volume', max(0.0, min(1.0, volume)))

    def test_speech(self) -> bool:
        """
        Test if TTS is working by speaking a test message
        
        Returns:
            True if test speech completed successfully, False otherwise
        """
        try:
            self.speak("Test message", wait=True)
            return True
        except Exception as e:
            print(f"TTS test failed: {e}")
            return False

    def shutdown(self):
        """Shutdown the TTS worker thread."""
        self._stop_event.set()
        self._queue.put(None)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for better speech synthesis
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text optimized for TTS
        """
        import re
        
        # Remove emoji and special characters that might cause issues
        text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)  # Remove emojis
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;]', '', text)  # Keep only alphanumeric, spaces, and punctuation
        
        # Replace common patterns
        text = text.replace('$', 'dollar ')
        text = text.replace('€', 'euro ')
        text = text.replace('£', 'pound ')
        text = text.replace('₹', 'rupee ')
        text = text.replace('/', ' or ')
        text = text.replace('\\', ' backslash ')
        text = text.replace('_', ' ')
        text = text.replace('-', ' ')
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _worker_loop(self):
        """
        Worker that processes TTS queue items.
        Runs in a dedicated thread with its own COM context.
        """
        import time
        try:
            import pythoncom
            python_com_available = True
        except ImportError:
            python_com_available = False
            
        # Initialize COM context for this thread (Critical for Windows)
        if python_com_available:
            pythoncom.CoInitialize()
            
        # Initialize engine within the thread
        self._init_engine()
        
        while not self._stop_event.is_set():
            try:
                # Get next item from queue
                try:
                    item = self._queue.get(timeout=0.1)
                except queue.Empty:
                    # Just continue and check stop_event
                    continue
                    
                if item is None:
                    break

                # Special protocol item for synchronous waiting
                if isinstance(item, tuple) and len(item) == 2 and item[0] == "__MILO_TTS_DONE__":
                    done_event = item[1]
                    try:
                        done_event.set()
                    except Exception:
                        pass
                    continue

                text = str(item).strip()
                if not text:
                    continue
                
                # Clean up text
                text = self._clean_text(text)
                if not text:
                    continue
                
                self.is_speaking = True
                
                try:
                    if self.engine:
                        self.engine.stop()  # prevent queue buildup
                        self.engine.say(text)
                        try:
                            self.engine.runAndWait()
                        except RuntimeError:
                            # Ignore "run loop already started" or "not started" logic errors
                            # that sometimes happen with pyttsx3 in threads
                            pass
                except Exception as e:
                    print(f"Error during TTS: {e}")
                    # Try to re-init engine on error
                    if python_com_available:
                        try:
                            pythoncom.CoUninitialize()
                            pythoncom.CoInitialize()
                        except:
                            pass
                    self._init_engine()
                finally:
                    self.is_speaking = False
                    
            except Exception as e:
                print(f"Error in worker loop: {e}")
                self.is_speaking = False
        
        # Cleanup
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
                
        if python_com_available:
            try:
                pythoncom.CoUninitialize()
            except:
                pass
