"""
Module: smart_plug_controller.py
Description: Controls smart plugs.
"""

# milo/iot/smart_plug_controller.py
class SmartPlugController:
    def turn_on(self, device_name):
        # In real life, use library 'pytuya' or 'kasa' here
        return f"Turning ON smart plug: {device_name}"

    def turn_off(self, device_name):
        return f"Turning OFF smart plug: {device_name}"