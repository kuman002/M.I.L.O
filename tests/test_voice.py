import time
import sys
import os

# Ensure both project root and src are importable when running this file directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

try:
    from src.voice.voice_recognition_optimized import VoiceRecognizer
except Exception as e1:
    try:
        from voice.voice_recognition_optimized import VoiceRecognizer
    except Exception as e2:
        print("❌ Error: Could not import VoiceRecognizer.")
        print(f"   src import failed: {e1}")
        print(f"   voice import failed: {e2}")
        sys.exit(1)

def run_diagnostics():
    print("="*50)
    print("      🎙️ M.I.L.O. VOICE ENGINE DIAGNOSTICS      ")
    print("="*50)
    
    # Initialize the engine
    vr = VoiceRecognizer(model_size="base")
    
    if not vr.is_available():
        print("\n❌ FAILED: Engine is not available. Check your faster-whisper installation.")
        return

    # ---------------------------------------------------------
    print("\n[TEST 1] Testing Command Mapping Logic...")
    # ---------------------------------------------------------
    test_phrases = [
        "hey milo are you there",
        "please add task to buy groceries",
        "can you check balance for me",
        "just random talking without a command"
    ]
    
    for phrase in test_phrases:
        match = vr.detect_command(phrase)
        if match:
            print(f"  ✅ '{phrase}' -> Mapped to: {match[0]}")
        else:
            print(f"  ⚠️ '{phrase}' -> No command detected.")

    # ---------------------------------------------------------
    print("\n[TEST 2] Testing Live Microphone (RAM Processing)...")
    # ---------------------------------------------------------
    print("  👉 When you see 'Listening...', say: 'Milo, add task learn Python'")
    time.sleep(1) # Give you a second to read the prompt
    
    result = vr.listen_once(timeout=5.0)
    
    if result:
        print(f"  ✅ SUCCESS! Transcribed: '{result}'")
    else:
        print("  ❌ FAILED: Did not hear anything or transcription failed.")

    # ---------------------------------------------------------
    print("\n[TEST 3] Testing Background Continuous Listening...")
    # ---------------------------------------------------------
    print("  👉 The mic will now stay open in the background.")
    print("  👉 Say a few random things. Say 'stop listening' to end the test.")
    
    # Define what happens when speech is heard in the background
    def on_speech_heard(text):
        print(f"  🗣️ Background Thread Heard: '{text}'")
        if "stop" in text.lower() or "exit" in text.lower():
            print("  🛑 Stop command recognized. Shutting down background thread...")
            vr.stop_listening()

    # Start the background thread
    vr.start_listening(on_speech_heard)
    
    # Keep the main program running while the background thread listens
    try:
        while vr.is_listening:
            time.sleep(0.5)
    except KeyboardInterrupt:
        # Catch CTRL+C to close gracefully
        vr.stop_listening()
        print("\n  🛑 Force quit detected.")

    print("\n" + "="*50)
    print("              🎉 DIAGNOSTICS COMPLETE             ")
    print("="*50)

if __name__ == "__main__":
    run_diagnostics()