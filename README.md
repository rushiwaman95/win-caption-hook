
# Win Caption Hook

A Windows application that captures live system captions and integrates with web-based AI assistants (ChatGPT, Gemini, etc.) through a Flask-powered web dashboard and Chrome extension.

## 🚀 Features

- **Real-time Transcription Capture**: Hooks into Windows Live Captions to capture audio transcription in real-time.
- **Web Dashboard**: Flask-based responsive UI for managing and analyzing captured captions.
- **Chrome Extension**: ChatGPT DevOps Panel integration for quick access to AI assistance.
- **Network Accessible**: Access the dashboard from any device on your local network.
- **Light-weight**: Minimal resource usage with efficient caption parsing.

---

## 📋 System Requirements

- **OS**: Windows 10/11 with Live Captions support
- **Python**: Python 3.8+ (for running from source)
- **Browser**: Chrome/Edge for the web dashboard and extension
- **Audio**: A working microphone or system audio routing for Live Captions

---

## 🛠️ Installation & Setup

### Option 1: Running from Source (Recommended for Development)

1. **Install Python**: Ensure Python 3.8+ is installed.

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python main.py
   ```

4. **Access the Dashboard**:
   The console will display the local URL, typically:
   ```
   http://localhost:5000
   ```
   - **From your PC**: Open `http://localhost:5000` in Chrome/Edge
   - **From other devices**: Use the network IP shown in console (e.g., `http://192.168.x.x:5000`)

### Option 2: Using the Compiled EXE

1. Locate the EXE in the `dist` folder
2. Double-click `main.exe` to run
3. Follow on-screen instructions if any prerequisites are missing

---

## 🔧 Chrome Extension Setup

The `Extension/` folder contains a ChatGPT DevOps Panel Chrome extension.

### Installation Steps:
1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Navigate to the `Extension/` folder in this project and select it
5. The extension will appear in your Chrome toolbar

### Features:
- Access ChatGPT in a Chrome side panel
- Integrates with captured captions for quick context
- DevOps-focused prompt assistance

---

## 🚦 How to Use

### 1. Enable Windows Live Captions
- Press **`Win + Ctrl + L`** to open Live Captions
- Ensure the Live Captions bar is visible (at top or bottom of screen)
- Download any required language packs if prompted
- Play audio (video, music, calls, etc.) to start transcription

### 2. Monitor Captions in Dashboard
- Open `http://localhost:5000` in your browser
- Captions will appear as cards in real-time as audio is captured
- Each completed sentence becomes a card

### 3. Use Chrome Extension (Optional)
- Click the extension icon in Chrome toolbar
- Access ChatGPT in the side panel for quick AI assistance
- Use captured captions as context for your prompts

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Waiting for Live Captions..."** or no text appearing | Press `Win + Ctrl + L` to ensure Live Captions window is open and active. Try playing audio to test. |
| **Dashboard not loading** | Verify Flask is running (check console for errors). Try `http://localhost:5000` or the network IP shown in console. |
| **Extension not appearing** | Ensure Developer mode is enabled in `chrome://extensions/`. Reload the extension if needed. |
| **Module not found errors** | Run `pip install -r requirements.txt` to install all dependencies. |
| **Python DLL errors** | Ensure Python 3.8+ is installed and accessible from PATH. |

---

## 📁 Project Structure

```
win-caption-hook/
├── main.py                 # Flask web server & caption capture logic
├── WindowsLiveChecker.py   # Utility to detect Live Captions window
├── requirements.txt        # Python dependencies
├── main.spec              # PyInstaller configuration for EXE build
├── Extension/             # Chrome extension files
│   ├── manifest.json      # Extension configuration
│   ├── sidepanel.html     # Extension UI
│   ├── sidepanel.js       # Extension logic
│   ├── background.js      # Background service worker
│   ├── content.js         # Content script
│   └── images/            # Extension icons
├── templates/             # Flask HTML templates
│   └── index.html         # Dashboard UI
└── LICENSE
```

---

## 🔨 Development Info

- **Backend**: Python with Flask
- **GUI Automation**: PyWinAuto (reads Windows Live Captions accessibility tree)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Extension**: Chrome Manifest V3

### Build EXE from Source
```bash
pyinstaller main.spec
```
The compiled EXE will be in the `dist/` folder.

### Dependencies
- `pywinauto`: Windows UI automation
- `flask`: Web framework
- `google-generativeai`: Optional, for Gemini API integration

---

## 📝 License

See [LICENSE](LICENSE) file for details.
The output will be in the `dist` folder.
