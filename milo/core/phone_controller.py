import logging
import subprocess
import time
import re # <--- Added Regex for better cleaning
from ppadb.client import Client as AdbClient

# --- APP LIBRARY ---
# Maps "What you say" -> "The Technical Package Name"
APP_LIBRARY = {
    # Social
    "whatsapp": "com.whatsapp",
    "instagram": "com.instagram.android",
    "facebook": "com.facebook.katana",
    "twitter": "com.twitter.android",
    "snapchat": "com.snapchat.android",
    "telegram": "org.telegram.messenger",
    "linkedin": "com.linkedin.android",
    "reddit": "com.reddit.frontpage",
    "discord": "com.discord",

    # Entertainment
    "youtube": "com.google.android.youtube",
    "spotify": "com.spotify.music",
    "netflix": "com.netflix.mediaclient",
    "prime video": "com.amazon.avod.thirdpartyclient",
    "hotstar": "in.startv.hotstar",
    "twitch": "tv.twitch.android.app",

    # Google / Tools
    "chrome": "com.android.chrome",
    "google": "com.google.android.googlequicksearchbox",
    "maps": "com.google.android.apps.maps",
    "gmail": "com.google.android.gm",
    "photos": "com.google.android.apps.photos",
    "drive": "com.google.android.apps.docs",
    "calculator": "com.google.android.calculator", # Try generic if this fails
    "calendar": "com.google.android.calendar",
    "camera": "com.android.camera", 
    "clock": "com.google.android.deskclock",
    "settings": "com.android.settings",
    "play store": "com.android.vending",

    # Shopping / Utility
    "amazon": "in.amazon.mShop.android.shopping",
    "flipkart": "com.flipkart.android",
    "paytm": "net.one97.paytm",
    "gpay": "com.google.android.apps.nbu.paisa.user",
    "phonepe": "com.phonepe.app",
    "zomato": "com.application.zomato",
    "swiggy": "in.swiggy.android"
}

class PhoneController:
    def __init__(self, host="127.0.0.1", port=5037):
        self.client = AdbClient(host=host, port=port)
        self.device = None
        self._connect()

    def _connect(self):
        try:
            try:
                self.client.version()
            except RuntimeError:
                subprocess.run(["adb", "start-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)

            devices = self.client.devices()
            if devices:
                self.device = devices[0]
                print(f"DEBUG: Phone connected ({self.device.serial})")
            else:
                self.device = None
                print("DEBUG: ADB running, but no phone found.")
        except Exception as e:
            print(f"DEBUG: Connection failed: {e}")

    def _ensure_connection(self):
        if self.device is None:
            self._connect()
        return self.device is not None

    def launch_app_by_name(self, app_name):
        """
        Smart function to find the package and launch it.
        """
        if not self._ensure_connection():
            return "Phone disconnected."

        # 1. AGGRESSIVE CLEANING
        # Remove 'open', 'launch', 'app' AND remove punctuation (.,?!)
        clean_name = app_name.lower()
        clean_name = re.sub(r'[^\w\s]', '', clean_name) # Remove all punctuation
        clean_name = clean_name.replace("open ", "").replace("launch ", "").replace("app", "").strip()
        
        print(f"DEBUG: Cleaned name -> '{clean_name}'") # Verify cleaning

        # 2. Look up in library
        package = APP_LIBRARY.get(clean_name)
        
        # 3. If not found, search installed packages
        if not package:
            print(f"DEBUG: '{clean_name}' not in library. Searching installed apps...")
            installed_packages = self.device.shell("pm list packages").replace("package:", "")
            
            # Simple fuzzy search in installed packages
            for pkg in installed_packages.splitlines():
                if clean_name in pkg:
                    package = pkg.strip()
                    print(f"DEBUG: Found installed match -> {package}")
                    break
        
        # 4. If still not found, try the guess
        if not package:
            # Try generic calculators since they vary by brand
            if "calculator" in clean_name:
                 package = "com.android.calculator2" # Common alternative
            else:
                 package = f"com.{clean_name}"
            print(f"DEBUG: Guessing -> {package}")
        
        # 5. Launch Sequence
        self.device.shell("input keyevent 26") # Power
        self.device.shell("input keyevent 82") # Unlock

        print(f"DEBUG: Launching Package -> {package}")
        self.device.shell(f"monkey -p {package} -c android.intent.category.LAUNCHER 1")
        
        return f"Opening {clean_name}..."

    def get_battery_level(self):
        if self._ensure_connection():
            res = self.device.shell("dumpsys battery | grep level")
            return f"Battery: {res.split(':')[1].strip()}%"
        return "Not connected"