# main.py
import logging
import sys
import datetime
import subprocess 
import time

# --- IMPORT MODULES ---
from milo.core.voice_engine import VoiceEngine
from milo.core.phone_controller import PhoneController
from milo.managers.memory_manager import MemoryManager
from milo.managers.reminder_manager import ReminderManager
from milo.managers.expenses_manager import ExpensesManager
from milo.analysis.finance_analyzer import FinanceAnalyzer
from milo.security.crypto_manager import CryptoManager
from milo.features.focus_mode_manager import FocusModeManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class MiloApp:
    def __init__(self):
        print("\n" + "="*40)
        print("   SYSTEM BOOT: M.I.L.O. ASSISTANT   ")
        print("="*40)
        
        self.voice = VoiceEngine() 
        
        print("Initializing Phone Controller...")
        try:
            subprocess.run(["adb", "start-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
        except:
            pass
        self.phone = PhoneController()
        
        self.memory = MemoryManager()
        self.reminders = ReminderManager()
        self.expenses = ExpensesManager()
        self.finance_viz = FinanceAnalyzer()
        self.security = CryptoManager()
        self.focus = FocusModeManager(self.phone)
        
        self.voice.speak("Milo is online.")

    def process_command(self, text):
        text = text.lower()
        print(f"DEBUG: Processing -> '{text}'") 

        # --- DYNAMIC APP OPENER (The New Logic) ---
        if "open" in text or "launch" in text:
            # Logic: "open whatsapp" -> extracts "whatsapp"
            # Logic: "launch google maps" -> extracts "google maps"
            
            # Remove the trigger words to get the app name
            app_name = text.replace("open ", "").replace("launch ", "").replace("please ", "").strip()
            
            if app_name:
                self.voice.speak(f"Opening {app_name}")
                # Call the new smart function in phone_controller
                result = self.phone.launch_app_by_name(app_name)
                print(f"Phone Log: {result}")
            else:
                self.voice.speak("Which app should I open?")
            return # Stop processing other commands

        # --- TIME CHECK ---
        elif "time" in text and "what" in text:
            now = datetime.datetime.now().strftime("%I:%M %p")
            self.voice.speak(f"The time is {now}")

        # --- PHONE STATUS ---
        elif "battery" in text:
            level = self.phone.get_battery_level()
            self.voice.speak(level)

        # --- EXPENSES ---
        elif "log expense" in text:
            try:
                parts = text.split()
                amount = next((float(s) for s in parts if s.replace('.', '', 1).isdigit()), None)
                category = parts[-1] 
                if amount:
                    self.expenses.log_expense(amount, category)
                    self.voice.speak(f"Logged {amount} for {category}.")
                else:
                    self.voice.speak("I didn't hear the amount.")
            except:
                self.voice.speak("Please say: log expense [amount] for [category]")

        elif "spending summary" in text:
            summary = self.finance_viz.get_summary()
            print(summary)
            self.voice.speak("Summary printed to console.")

        # --- MEMORY ---
        elif "remember that" in text:
            if " is " in text:
                clean = text.replace("remember that ", "")
                key, value = clean.split(" is ", 1)
                self.memory.remember(key.strip(), value.strip())
                self.voice.speak(f"Remembered: {key} is {value}")
        
        elif "what is" in text:
            key = text.replace("what is ", "").replace("?", "").strip()
            val = self.memory.recall(key)
            if val:
                self.voice.speak(f"{key} is {val}")
            else:
                self.voice.speak(f"I don't have a record for {key}.")

        # --- EXIT ---
        elif "goodbye" in text or "stop" in text:
            self.voice.speak("Goodbye, Sir.")
            sys.exit(0)

        # --- FALLBACK ---
        else:
            self.voice.speak("I heard you, but I don't know that command.")

    def run(self):
        while True:
            try:
                command = self.voice.listen_for_command()
                if command and len(command) > 2:
                    self.process_command(command)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"Error: {e}")

if __name__ == "__main__":
    app = MiloApp()
    app.run()