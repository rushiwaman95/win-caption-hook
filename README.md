
# 🎙️ Live Transcript & AI Assistant

A powerful, live captioning AI assistant that listens to your system audio (via Windows Live Captions) and provides intelligent, human-like answers using **Google Gemini**.

## 🚀 Features

- **Real-time Transcription**: Hooks into Windows 11 "Live Captions" to read audio in real-time.
- **AI-Powered Context**: Select any card or transcription segment to ask Google Gemini for context or answers.
- **Smart API Key Rotation**: Handles multiple API keys to avoid hitting usage limits.
- **Web Dashboard**: Modern, dark-themed responsive UI accessible from your phone or local network.

---

## 📋 System Requirements

- **OS**: Windows 11 (22H2 or later) or Windows 10 (with Live Captions support).
- **Audio**: A working microphone or system audio routing.
- **Internet**: Required for Google Gemini API.

---

## 🛠️ Installation & Setup

### Option 1: Running the Executable (Recommended)
This is the easiest way to run the application if you don't want to mess with code.

1. **Locate the EXE**: Go to the `dist` folder in this directory.
2. **Run**: Double-click `main.exe`.
3. **Follow On-Screen Instructions**: The app will verify prerequisites.

### Option 2: Running from Source
If you are a developer or want to modify the code:

1. **Install Python**: Ensure Python 3.10+ is installed.
2. **Install Dependencies**:
   Open a terminal in this folder and run:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Script**:
   ```bash
   python main.py
   ```

---

## 🚦 How to Use

### 1. Enable Live Captions
The app relies on the **Windows Live Captions** feature.
- Press **`Win + Ctrl + L`** on your keyboard.
- Ensure the Live Captions bar appears (usually at the top or bottom of your screen).
- If it asks to download a language pack, please do so.

### 2. Configure API Keys (First Run)
On the first launch, the application (console window) will ask for your Google Gemini API Keys.
- You can get free keys from [Google AI Studio](https://aistudio.google.com/).
- We recommend adding **at least 2-3 keys** if you plan to use it heavily, but 1 works fine.
- Answer the prompts in the console window to save your keys.

### 3. Open the Dashboard
Once running, the console will display a local URL, for example:
```
http://192.168.1.5:5000
```
- **From your PC**: Open `http://localhost:5000` in Chrome/Edge.
- **From your Phone**: Ensure your phone is on the **same Wi-Fi**, then open the IP address shown in the console.

### 4. Interacting with the AI
- **Automatic Transcription**: As audio plays on your PC, cards will appear in the dashboard.
- **Ask AI**:
    - **Single Card**: Click the **Star Icon (✧˖)** on any specific card to get context about that sentence.
    - **Multiple Cards**: Click multiple cards to select them, then click the floating **"Ask AI"** button at the bottom right to analyze all selected text together.

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Waiting for Live Captions..."** | Press `Win + Ctrl + L` to ensure the Live Captions window is open and visible. The app needs it to be running. |
| **No Text Appearing** | Ensure audio is playing and Live Captions is actually transcribing words. Try playing a YouTube video to test. |
| **AI Not Responding** | Check your internet connection. Your API keys might be expired or quota exceeded. Restart the app to re-enter keys if needed. |
| **"DLL load failed" (Source)** | You might be missing C++ redistributables or have an incompatible Python version. Try the EXE version instead. |

---

## 🔨 Development Info

- **Backend**: Python (Flask)
- **GUI Automation**: PyWinAuto (reads the accessibility tree of Windows Live Captions)
- **Frontend**: HTML5, CSS3, Vanilla JS
- **AI Model**: Google Gemini 1.5 Flash (via `google-generativeai`)

### Build EXE
To compile the project yourself:
```bash
pyinstaller main.spec
```
The output will be in the `dist` folder.
