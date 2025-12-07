"""
Module: focus_mode_manager.py
Description: Manages Focus Mode logic.
"""

"""
Module: focus_mode_manager.py
Description: Manages Focus Mode logic.
"""
class FocusModeManager:
    def __init__(self, phone_controller):
        self.is_active = False
        self.phone = phone_controller

    def enable_focus_mode(self):
        self.is_active = True
        msg = "Focus Mode Enabled. "
        
        # 1. Logic to silence phone via ADB keyevents
        if self.phone.device:
            # KeyCode 164 is VOLUME_MUTE
            self.phone.device.shell("input keyevent 164") 
            msg += "Phone silenced. "
            
        return msg + "Distractions blocked."

    def disable_focus_mode(self):
        self.is_active = False
        # Logic to unmute could go here (KeyCode 24 is VOLUME_UP)
        if self.phone.device:
             for _ in range(5):
                 self.phone.device.shell("input keyevent 24")
                 
        return "Focus Mode Disabled. Welcome back."