# MILO Installation Guide

## Prerequisites

1. **Python 3.10 or higher**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

## Step-by-Step Installation

### 1. Install Python Dependencies

Open terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

**Troubleshooting PyAudio Installation:**

- **Windows:**
  ```bash
  pip install pipwin
  pipwin install pyaudio
  ```

- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt-get update
  sudo apt-get install portaudio19-dev python3-pyaudio
  ```

- **macOS:**
  ```bash
  brew install portaudio
  pip install pyaudio
  ```

### 2. Download Vosk Speech Recognition Model

1. Visit: https://alphacephei.com/vosk/models
2. Download a model (recommended: `vosk-model-small-en-us-0.15` for faster processing)
3. Extract the downloaded ZIP file
4. Create a folder named `models` in the project root (if it doesn't exist)
5. Move the extracted model folder into `models/` and rename it to `model`

**Final structure should be:**
```
project/
  └── models/
      └── model/
          ├── am/
          ├── graph/
          ├── ivector/
          └── ... (other model files)
```

**Model Options:**
- `vosk-model-small-en-us-0.15` - Small, fast, ~40MB
- `vosk-model-en-us-0.22` - Larger, more accurate, ~1.8GB
- `vosk-model-en-us-0.22-lgraph` - Even larger, most accurate, ~1.9GB

### 3. Run the Application

**Option 1: Using Python directly**
```bash
python src/main.py
```

**Option 2: Using the batch file (Windows)**
```bash
run.bat
```

**Option 3: Using the shell script (Linux/macOS)**
```bash
chmod +x run.sh
./run.sh
```

## First Run

1. The application will create a `data/` directory automatically
2. A SQLite database (`milo.db`) will be created for storing your data
3. If voice recognition doesn't work, check that:
   - Vosk model is correctly placed in `models/model/`
   - Microphone permissions are granted
   - Microphone is connected and working

## Verification

To verify everything is working:

1. **Test GUI**: Launch the application - you should see the MILO interface
2. **Test Text Input**: Type "help" in the input field and press Enter
3. **Test Voice**: Click "🎤 Start Listening" and say "hello" (requires Vosk model)

## Common Issues

### Issue: "No module named 'PyQt5'"
**Solution**: Install dependencies: `pip install -r requirements.txt`

### Issue: "Vosk model not found"
**Solution**: Download and place Vosk model in `models/model/` directory

### Issue: "PyAudio not found"
**Solution**: Follow PyAudio installation instructions above

### Issue: Voice recognition not working
**Solution**: 
- Verify microphone permissions
- Check Vosk model installation
- Try a different Vosk model

### Issue: Database errors
**Solution**: 
- Ensure `data/` directory exists and is writable
- Delete `data/milo.db` to reset database

## System Requirements

- **OS**: Windows 10+, Linux, or macOS
- **RAM**: 2GB minimum (4GB recommended)
- **Storage**: 500MB for application + model size
- **Python**: 3.10 or higher
- **Microphone**: Required for voice features (optional for text-only use)

## Support

For issues or questions, refer to the project documentation or contact the development team.
