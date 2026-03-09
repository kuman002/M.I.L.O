import os
import sys
import unittest
import importlib

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

VoiceRecognizer = None
for module_name in ("src.voice.voice_recognition_optimized", "voice.voice_recognition_optimized"):
    try:
        module = importlib.import_module(module_name)
        VoiceRecognizer = getattr(module, "VoiceRecognizer", None)
        if VoiceRecognizer is not None:
            break
    except Exception:
        continue


@unittest.skipIf(VoiceRecognizer is None, "VoiceRecognizer import unavailable in this environment")
class TestVoiceRecognitionModule(unittest.TestCase):
    def _build_voice_instance_without_init(self):
        vr = VoiceRecognizer.__new__(VoiceRecognizer)
        # Minimal attributes required by detect_command when __init__ is bypassed.
        vr._command_items = tuple(VoiceRecognizer.COMMANDS.items())
        vr._keyword_items = tuple(VoiceRecognizer.KEYWORD_COMMAND_MAP.items())
        vr._command_first_tokens = tuple(
            (phrase, cmd_id, phrase.split(" ", 1)[0])
            for phrase, cmd_id in vr._command_items
        )
        return vr

    def test_normalize_phonetic_task_and_time(self):
        vr = self._build_voice_instance_without_init()
        text = "had it asked for creating ui by tomorrow 5 b.m."
        normalized = vr.normalize_transcript(text)
        self.assertIn("task", normalized)
        self.assertIn("pm", normalized)

    def test_normalize_notepad_mishear(self):
        vr = self._build_voice_instance_without_init()
        normalized = vr.normalize_transcript("open north bad")
        self.assertIn("notepad", normalized)

    def test_detect_command_wake_word(self):
        vr = self._build_voice_instance_without_init()
        command = vr.detect_command("hello milo can you hear me")
        self.assertIsNotNone(command)
        self.assertEqual(command[0], "WAKE_WORD")

    def test_parse_relative_reminder(self):
        vr = self._build_voice_instance_without_init()
        data = vr.parse_reminder_command("remind me to call mom in 5 minutes")
        self.assertIsNotNone(data)
        self.assertEqual(data["seconds"], 300)
        self.assertIn("datetime", data)


if __name__ == "__main__":
    unittest.main()
