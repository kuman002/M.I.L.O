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

### 2. Run the Application

**Option 1: Using Python directly**
```bash
python src/main.py
```

**Option 2: Using the batch launcher (Windows)**
```bash
launch_milo.bat
```

**Option 3: Using scripts (all platforms)**
```bash
# Windows PowerShell
.\scripts\run.ps1

# Windows Command Prompt
.\scripts\run.bat
```

## First Run

1. The application will create a `data/` directory automatically
2. A SQLite database (`milo.db`) will be created for storing your data
3. **Voice recognition model** (faster-whisper) will download automatically on first use (~150MB)
4. If voice recognition doesn't work, check that:
   - Internet connection is available for initial model download
   - Microphone permissions are granted
   - Microphone is connected and working

## Verification

To verify everything is working:

1. **Test GUI**: Launch the application - you should see the MILO interface
2. **Test Text Input**: Type "help" in the input field and press Enter
3. **Test Voice**: Click "🎤 Start Listening" and say "hello" (model downloads automatically on first use)

## Common Issues

### Issue: "No module named 'PyQt5'"
**Solution**: Install dependencies: `pip install -r requirements.txt`

### Issue: "faster-whisper not installed"
**Solution**: Install faster-whisper: `pip install faster-whisper`

### Issue: "PyAudio not found"
**Solution**: Follow PyAudio installation instructions above

### Issue: Voice recognition not working
**Solution**: 
- Verify microphone permissions
- Ensure internet connection for initial model download
- Check that `assets/milo_brain/` folder exists after first run

### Issue: Database errors
**Solution**: 
- Ensure `data/` directory exists and is writable
- Delete `data/milo.db` to reset database

## System Requirements

- **OS**: Windows 10+, Linux, or macOS
- **RAM**: 4GB minimum (8GB recommended for voice features)
- **Storage**: 500MB for application + voice model (~150MB)
- **Python**: 3.10 or higher
- **Microphone**: Required for voice features (optional for text-only use)
- **Internet**: Required once for initial voice model download

## Support

For issues or questions, refer to the project documentation or contact the development team.
