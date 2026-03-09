# M.I.L.O. (Managing Information & Lifestyle Optimizer)

MILO is an offline-first desktop assistant built with Python and PyQt5. It combines voice interaction, NLP intent parsing, local data management, and optional desktop automation in a privacy-centric workflow.

## Features
- Offline speech-to-text with `faster-whisper`
- Offline text-to-speech with `pyttsx3`
- Hybrid NLP parser (LLM route when available + robust local fallback)
- Task management with due-date extraction from natural language
- Finance tracking with encrypted transaction fields
- Habit tracking with streak support and reminder logic
- Dashboard + tabbed UI (Tasks, Finances, Habits, Reminders)
- Optional desktop automation (typing, browser search, OCR click)
- Optional speaker enrollment/verification with Picovoice Eagle

## Current Project Structure

```text
project/
├── src/
│   ├── main.py
│   ├── assistant.py
│   ├── automation/
│   │   ├── computer_use.py
│   │   └── rpa_service.py
│   ├── core/
│   │   └── security.py
│   ├── database/
│   │   └── database.py
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── dashboard_tab.py
│   │   ├── tasks_tab.py
│   │   ├── finances_tab.py
│   │   ├── habits_tab.py
│   │   └── reminders_tab.py
│   ├── managers/
│   │   ├── task_manager.py
│   │   ├── finance_manager.py
│   │   └── habit_manager.py
│   ├── nlp/
│   │   └── nlp_parser.py
│   └── voice/
│       ├── voice_recognition_optimized.py
│       └── text_to_speech.py
├── tests/
├── assets/
├── data/
├── requirements.txt
└── README.md
```

## Setup

1. Install Python 3.10+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python src/main.py
```

Windows launcher (optional):

```bash
launch_milo.bat
```

Notes:
- `faster-whisper` model files are downloaded on first use.
- Some features are optional and degrade gracefully when dependencies are missing.

## Usage

### Voice Flow
- Click `Start Listening`.
- Speak naturally; MILO transcribes, detects command intent, and either executes directly or routes through NLP.

Examples:
- `add task to create ui for tomorrow 4`
- `for food add a 50`
- `remind me to call mom in 10 minutes`
- `check my balance`

### Text Flow
- Use the input bar at the bottom of the app.
- Commands are parsed through the same assistant pipeline.

### Automation Flow (Optional)
- Typing and browser actions are available through automation service.
- Spoken typing commands like `next line`, `enter`, and `tab` are expanded in RPA typing mode.

## Key Commands (Examples)

### Tasks
- `add task to read book tomorrow 6 pm`
- `list tasks`
- `complete task 1`

### Finance
- `add expense 250 for food`
- `for food add a 50`
- `check balance`

### Reminders
- `remind me to stretch in 30 minutes`
- `set reminder to submit report at 5 pm`

### Automation
- `type hello world next line this is milo`
- `search python dateparser in browser`

## Testing

Run all tests:

```bash
python -m pytest -q
```

If you use conda environment `milo_stable`:

```bash
conda run -n milo_stable python -m pytest -q
```

Additional docs:
- `TEST_CASES.md` for test case inventory
- `REVIEW_III_PROJECT_ANALYSIS.md` for review/report content

## Tech Stack
- Python, PyQt5
- faster-whisper, SpeechRecognition, pyttsx3
- SQLite (with indexes + FTS)
- cryptography (vault/encryption)
- optional automation: pyautogui, pygetwindow, easyocr, opencv

## Privacy & Security
- Local-first architecture: app data stays on device (`data/milo.db`).
- No required cloud backend for core assistant behavior.
- Finance records are encrypted through vault integration.
- PIN and optional voice profile enrollment are supported.

## Troubleshooting

1. Voice recognition not responding:
- Check microphone permissions and default input device.
- Verify voice dependencies from `requirements.txt` are installed.

2. Automation not working:
- Install optional automation dependencies (`pyautogui`, `pygetwindow`, `easyocr`, `opencv-python`).
- Keep target window focused when using typing/click actions.

3. Fresh database reset:
- Stop app and remove `data/milo.db`.
- Restart app to recreate schema.
