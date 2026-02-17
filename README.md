# M.I.L.O. (Managing Information & Lifestyle Optimizer)

A fully offline, privacy-centric virtual assistant built with Python and PyQt5.

## Features
- **Offline Voice Interaction**: Uses Vosk for Speech-to-Text (STT) and pyttsx3 for Text-to-Speech (TTS)
- **Natural Language Understanding**: Offline NLP parser for understanding user commands
- **Task Management**: Create, schedule, complete, and delete tasks locally
- **Finance Tracking**: Track expenses, income, and view balance without cloud syncing
- **Habit Tracking**: Monitor habits and analyze completion patterns
- **Dashboard**: Visual overview of tasks, finances, and habits
- **Privacy First**: All data stays on your machine - no internet connection required

## Project Structure

```
project/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main entry point
│   ├── database.py             # Database operations (SQLite)
│   ├── voice_recognition.py    # Offline voice recognition (Vosk)
│   ├── text_to_speech.py       # Offline text-to-speech (pyttsx3)
│   ├── nlp_parser.py           # Command parser and intent recognition
│   ├── assistant.py            # Main assistant coordinator
│   ├── task_manager.py         # Task management module
│   ├── finance_manager.py      # Financial tracking module
│   ├── habit_manager.py        # Habit tracking and analytics
│   └── gui/
│       ├── __init__.py
│       └── main_window.py      # PyQt5 GUI application
├── data/                       # Database and data files (created automatically)
├── models/                     # Vosk model directory (user downloads)
│   └── model/                  # Vosk model files
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Setup

1.  **Install Python 3.10+**
    - Download from [python.org](https://www.python.org/downloads/)

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: On Windows, `pyaudio` might need to be installed using:*
    ```bash
    pip install pipwin
    pipwin install pyaudio
    ```
    *On Linux, you may need to install PortAudio:*
    ```bash
    sudo apt-get install portaudio19-dev python3-pyaudio
    ```

3.  **Download Vosk Model**:
    - Download a model from [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)
    - Recommended: `vosk-model-small-en-us-0.15` (smaller, faster) or `vosk-model-en-us-0.22` (more accurate)
    - Extract the downloaded zip file
    - Create a `models` folder in the project root
    - Move the extracted model folder into `models/` and rename it to `model`
    - Final path should be: `models/model/vosk-model-...`

4.  **Run the Application**:
    ```bash
    python src/main.py
    ```

## Usage

### Voice Commands
- Click "🎤 Start Listening" to activate voice recognition
- Speak commands naturally, such as:
  - "Create a task to buy groceries"
  - "Add expense 50 dollars for food"
  - "Check my balance"
  - "List my tasks"

### Text Commands
- Type commands in the input field and press Enter or click Send
- Examples:
  - "create task finish report priority high"
  - "add expense 25 shopping"
  - "show tasks"
  - "complete task 1"

### GUI Features
- **Dashboard**: Overview of tasks, finances, and habits
- **Tasks Tab**: Manage tasks (add, complete, delete)
- **Finances Tab**: Track income and expenses
- **Habits Tab**: Monitor habit completion

## Commands

### Task Commands
- `create task [title]` - Create a new task
- `list tasks` - Show all pending tasks
- `complete task [number]` - Mark task as complete
- `delete task [number]` - Delete a task

### Finance Commands
- `add expense [amount] [category]` - Add an expense
- `add income [amount]` - Add income
- `check balance` - Show current balance and summary

### Habit Commands
- `add habit [name]` - Create a new habit
- `log habit` - Log habit completion for today

### General Commands
- `help` - Show available commands
- `hello` - Greeting
- `goodbye` - Exit

## Application Areas

- **Secure Financial Management**: Track expenses and generate reports locally
- **Advanced Productivity Tracking**: Organize schedules and optimize efficiency
- **Personalized Academic Research**: Index local papers and summarize documents
- **Digital Health Monitoring**: Analyze activity patterns and suggest breaks
- **Confidential Data Organization**: Automate file management securely
- **Self-Sustaining Digital Support**: Consistent automation without internet

## Technical Details

- **Language**: Python 3.10+
- **GUI Framework**: PyQt5
- **Speech Recognition**: Vosk (offline)
- **Text-to-Speech**: pyttsx3 (offline)
- **Database**: SQLite3 (local)
- **Architecture**: Modular design with separate managers for each feature

## Privacy & Security

- All data is stored locally in SQLite database
- No internet connection required
- No data is sent to external servers
- Voice processing happens entirely offline
- Complete data sovereignty

## Team

**TEAM NO: 7**
- Vengadeshaperumal T (2236110009)
- Srieevardhan S M (2236110010)
- Kumaresan K (2236110013)
- Deepakkumar S (2236110015)

**Annamalai University**  
**Faculty of Engineering and Technology**  
**Department of Computer Science and Engineering**

**Project Guide**: Dr. L. R. Sudha (Associate Professor)

## License

This project is developed as part of Final Year Project Review-1 at Annamalai University.

## Troubleshooting

1. **Voice recognition not working**: 
   - Ensure Vosk model is downloaded and placed in `models/model/`
   - Check microphone permissions
   - Try a different Vosk model

2. **PyAudio installation issues**:
   - Windows: Use `pipwin install pyaudio`
   - Linux: Install `portaudio19-dev` first
   - macOS: Install via Homebrew: `brew install portaudio`

3. **Database errors**:
   - Ensure `data/` directory exists or is writable
   - Delete `data/milo.db` to reset database

## Future Enhancements

- Wake word detection
- Calendar integration
- Email integration
- File search capabilities
- Advanced analytics and reporting
