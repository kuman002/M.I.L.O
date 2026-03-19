import json
import os
import re
import sys
import wave
from pathlib import Path

import kagglehub
import speech_recognition as sr
from jiwer import cer, wer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from src.voice.voice_recognition_optimized import VoiceRecognizer


def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def wav_to_audio_data(path: Path) -> sr.AudioData:
    with wave.open(str(path), "rb") as wf:
        sample_rate = wf.getframerate()
        sample_width = wf.getsampwidth()
        raw_data = wf.readframes(wf.getnframes())
    return sr.AudioData(raw_data, sample_rate, sample_width)


def main() -> None:
    dataset_path = Path(kagglehub.dataset_download("pavanelisetty/sample-audio-files-for-speech-recognition"))

    # Reference transcript for harvard.wav is the standard CMU/Harvard sentence used in SpeechRecognition examples.
    samples = [
        {
            "file": dataset_path / "harvard.wav",
            "reference": (
                "the stale smell of old beer lingers it takes heat to bring out the odor "
                "a cold dip restores health and zest a salt pickle tastes fine with ham "
                "tacos al pastor are my favorite a zestful food is the hot cross bun"
            ),
            "expected_command": None,
            "expected_speech": True,
        },
        {
            "file": dataset_path / "jackhammer.wav",
            "reference": "",
            "expected_command": None,
            "expected_speech": False,
        },
    ]

    model_size = os.getenv("MILO_EVAL_MODEL", "tiny.en")
    recognizer = VoiceRecognizer(model_size=model_size, device="cpu", language="en")

    if not recognizer.is_available():
        raise RuntimeError("VoiceRecognizer model failed to initialize.")

    report_rows = []
    exact_matches = 0
    command_matches = 0
    speech_detection_matches = 0

    non_empty_ref_pairs = []

    for item in samples:
        path = item["file"]
        audio_data = wav_to_audio_data(path)
        result = recognizer.transcribe_audio_memory(audio_data)

        pred_text_raw = result.get("text", "") if result.get("success") else ""
        pred_text = normalize_text(pred_text_raw)
        ref_text = normalize_text(item["reference"])

        pred_cmd = recognizer.detect_command(pred_text_raw)
        pred_cmd_id = pred_cmd[0] if pred_cmd else None

        exact_match = pred_text == ref_text
        command_match = pred_cmd_id == item["expected_command"]
        speech_match = (bool(pred_text) == bool(item["expected_speech"]))

        if exact_match:
            exact_matches += 1
        if command_match:
            command_matches += 1
        if speech_match:
            speech_detection_matches += 1

        row = {
            "file": str(path),
            "success": bool(result.get("success", False)),
            "predicted_text": pred_text,
            "reference_text": ref_text,
            "exact_match": exact_match,
            "expected_command": item["expected_command"],
            "predicted_command": pred_cmd_id,
            "command_match": command_match,
            "expected_speech": bool(item["expected_speech"]),
            "predicted_speech": bool(pred_text),
            "speech_detection_match": speech_match,
            "model_size": model_size,
        }

        if ref_text:
            row["wer"] = wer(ref_text, pred_text)
            row["cer"] = cer(ref_text, pred_text)
            non_empty_ref_pairs.append((ref_text, pred_text))
        else:
            row["wer"] = None
            row["cer"] = None

        report_rows.append(row)

    total = len(samples)
    summary = {
        "dataset": "pavanelisetty/sample-audio-files-for-speech-recognition",
        "dataset_path": str(dataset_path),
        "total_files": total,
        "exact_match_accuracy": exact_matches / total,
        "command_accuracy": command_matches / total,
        "speech_detection_accuracy": speech_detection_matches / total,
        "model_size": model_size,
    }

    if non_empty_ref_pairs:
        refs = [r for r, _ in non_empty_ref_pairs]
        preds = [p for _, p in non_empty_ref_pairs]
        summary["overall_wer_non_empty_refs"] = wer(refs, preds)
        summary["overall_cer_non_empty_refs"] = cer(refs, preds)
    else:
        summary["overall_wer_non_empty_refs"] = None
        summary["overall_cer_non_empty_refs"] = None

    report = {"summary": summary, "files": report_rows}
    report_path = PROJECT_ROOT / "data" / "voice_accuracy_report_kaggle.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
