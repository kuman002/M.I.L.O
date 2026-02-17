# MILO System Documentation

This document explains how MILO works internally so you can prepare detailed documentation for users or developers.

## 1) Voice Recognition (speech to text)

### Purpose
Converts spoken input into text that the assistant can parse. It also supports a command shortcut layer so common phrases are handled quickly.

### Core file
- src/voice/voice_recognition_optimized.py

### How it works
1. Audio capture
   - Uses the speech_recognition library to open the microphone stream.
   - Energy thresholds and pause thresholds are tuned to detect speech quickly and reduce latency.

2. Transcription
   - Audio is saved to a temp file and transcribed with the Whisper model.
   - The Whisper model is loaded once and reused.
   - The model runs on GPU if available, otherwise CPU.

3. Command detection
   - After transcription, the text is compared against a command phrase map.
   - If a phrase matches, it yields a command ID (e.g., ADD_TASK, ADD_HABIT).
   - If no command matches, the full text is forwarded to the NLP pipeline.

4. Reminder parsing
   - A dedicated parser detects phrases like "remind me to X in Y minutes".
   - It returns both the reminder message and a target datetime.

### Key controls
- Model size: configurable (tiny/base/small/medium/large).
- GPU acceleration: automatically used if CUDA is available.
- Noise calibration: calibrates ambient noise for better capture.

---

## 2) NLP Parser (text understanding)

### Purpose
Determines the user intent (task, finance, habit, reminder, etc.) and extracts entities (title, amount, category, date).

### Core file
- src/nlp/nlp_parser.py

### How it works
1. Pattern matching phase
   - Regex patterns attempt to match intent-specific phrases.
   - Each pattern has a confidence weight.

2. Keyword scoring phase
   - If pattern confidence is weak, keyword weights are used to score intents.

3. Intent decision
   - The highest score becomes the final intent.

4. Entity extraction
   - Extracts title, amount, category, date, priority, and task id based on the selected intent.
   - Title extraction removes command words and time phrases to get a clean name.

### Output
- intent
- entities
- confidence score
- original text

---

## 3) Assistant (command routing)

### Purpose
Coordinates all modules by interpreting parsed intents and calling the appropriate manager.

### Core file
- src/assistant.py

### How it works
1. Accepts raw text (from voice or text input).
2. Uses NLP Parser to determine intent + entities.
3. Routes the intent to the correct manager:
   - Task Manager for task creation/deletion/complete/list
   - Finance Manager for expense/income/balance
   - Habit Manager for habit creation/logging
   - Reminder creation through the database
4. Returns a response dictionary with message and success status.

---

## 4) Task Management

### Purpose
Create, list, complete, and delete tasks, including priority and due date support.

### Core files
- src/managers/task_manager.py
- src/database/database.py (tasks table)

### How it works
1. Task creation writes into the tasks table.
2. Task retrieval filters by status and due date as needed.
3. Task updates mark tasks completed or deleted.
4. Charts use aggregated counts for dashboards.

---

## 5) Reminder System

### Purpose
Create reminders and notify users when they are due.

### Core files
- src/gui/main_window.py (reminder checks)
- src/database/database.py (reminders table)

### How it works
1. Reminders are stored with message, datetime, and status.
2. A periodic refresh checks for reminders due at or before now.
3. When due:
   - Shows a popup and message area update.
   - Uses TTS to speak the reminder.
   - Marks reminder as completed.

---

## 6) Finance Management

### Purpose
Track income and expenses, summarize balance, and show dashboards.

### Core files
- src/managers/finance_manager.py
- src/database/database.py (finances table)
- src/gui/finances_tab.py
- src/gui/dashboards.py

### How it works
1. Adds income/expense records into finances table.
2. Uses cached summary queries for balance and charts.
3. Chart modules visualize:
   - Income vs expenses
   - Expenses by category
   - Budget status

---

## 7) Habit Management

### Purpose
Create habits, log daily completions, track streaks, and remind users.

### Core files
- src/managers/habit_manager.py
- src/database/database.py (habits + habit_logs tables)
- src/gui/habits_tab.py

### How it works
1. Habits are stored with a reminder_time field.
2. Habit logs are stored in habit_logs with date and notes.
3. Cache is used for frequent reads.
4. Daily log detection prevents duplicate logs.
5. Reminder engine checks if the habit is not logged after reminder_time.

---

## 8) Automation and App Launcher

### Purpose
Open apps, files, folders, and websites via voice or typed commands.

### Core files
- src/managers/app_launcher.py
- src/assistant.py (intent routing)

### How it works
1. Intent detection routes to open_app/open_file/open_folder/open_url.
2. App launcher resolves common apps and executes OS commands.

---

## 9) Local Database (SQLite)

### Purpose
Store all structured data locally on the machine for offline operation.

### Core file
- src/database/database.py

### Tables
- tasks
- subtasks
- finances
- habits
- habit_logs
- user_activity
- reminders (created by the GUI when needed)

### Key design points
- WAL mode for better write performance.
- Indexes on common queries.
- Migration support for schema updates.

---

## 10) Text To Speech (TTS)

### Purpose
Speak responses and reminders aloud.

### Core file
- src/voice/text_to_speech.py

### How it works
1. A shared TTS instance is used to avoid multiple engines.
2. The assistant passes response messages to TTS if enabled.
3. Reminder and status messages can be spoken immediately.

---

## Data Flow Summary

1. Voice input -> Whisper transcription -> command detection -> NLP parse
2. NLP intent -> Assistant -> relevant manager
3. Manager writes/reads local DB
4. GUI updates tables + charts
5. TTS speaks responses and reminders

---

## Suggested Future Enhancements

- Add configurable budgets per category (not fixed mock values).
- Add habit streak calculations to the UI.
- Add scheduled reminder checks without full refresh.
- Add user settings for voice sensitivity and reminder times.
