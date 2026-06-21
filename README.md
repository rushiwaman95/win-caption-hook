## Intro

Real-time voice-to-AI interview assistant that captures Windows Live Captions and streams responses from Groq AI.

Perfect for DevOps/SRE interview practice - speak your questions naturally and get expert-level answers instantly.



## Features

- **Zero Fuzzy Matching** - Restarts Live Captions on every Send/Skip for clean buffers
- **Smart Orchestrator** - Detects 5-second silence to mark questions as "ready"
- **Streaming AI Responses** - Real-time token streaming from Groq AI
- **Multi-Key Rotation** - Round-robin API key switching (up to 4 keys supported)
- **Invisible Caption Window** - Aggressively hidden (1ms polling for 3 seconds)
- **Fast Restarts** - 200ms kill → restart cycle per question
- **Real-time Stats** - SSE stream for live text, state, and silence detection
- **Clean UI** - Markdown rendering with code highlighting

## 📋 Requirements

- **OS:** Windows 11 (Live Captions built-in)
- **Python:** 3.9+
- **API Key:** [Groq Cloud](https://console.groq.com/) (free tier: 30 req/min per key)

## 🚀 Installation

### 1. Clone Repository


```bash
git clone <your-repo-url>
cd win-cap-v2
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**`requirements.txt`:**
```
Flask==3.0.0
pywinauto==0.6.8
requests==2.31.0
python-dotenv==1.0.0
```

### 3. Configure API Keys

Create `.env` file:

```env
# Single key
GROQ_API_KEY=gsk_your_key_here

# OR multiple keys (recommended for rate limits)
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3,gsk_key4

# Optional
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TIMEOUT=30
```

### 4. Enable Live Captions

```
Press: Win + Ctrl + L
```

Or go to: `Settings → Accessibility → Captions → Live captions`

---

## ▶️ Usage

### Start Server

```bash
python app.py
```

```
✅ Loaded 4 API key(s)
🔍 Starting caption capture with orchestrator...
⏳ Waiting for Live Captions... (Press Win+Ctrl+L)
✅ Capture active

 * Running on http://0.0.0.0:5000
```

### Open Browser

```
http://localhost:5000
```

### Workflow

1. **Speak** your question out loud
2. **Wait 5 seconds** → Green "Ready to Send" appears
3. **Click "Send"** or press `Enter`
4. Live Captions **restarts** (fresh buffer)
5. AI **streams** response
6. Repeat for next question

---

## 🎛️ Configuration

**`config.py`** - Main settings:

```python
# ═══ AI MODEL ═══════════════════════════════════════════
GROQ_MODEL = 'llama-3.1-8b-instant'
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 512

# ═══ CAPTION POLLING ════════════════════════════════════
CAPTION_POLL_INTERVAL = 0.05  # 50ms (don't go lower)

# ═══ ORCHESTRATOR ═══════════════════════════════════════
SILENCE_THRESHOLD = 5.0       # Seconds to mark as "ready"
MIN_QUESTION_LENGTH = 10      # Min chars to send

# ═══ KEY ROTATION ═══════════════════════════════════════
KEY_ROTATION_STRATEGY = 'round_robin'  # or 'on_error'
MAX_KEY_RETRIES = 4
RATE_LIMIT_COOLDOWN = 60

# ═══ SERVER ═════════════════════════════════════════════
HOST = '0.0.0.0'
PORT = 5000
DEBUG = False
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI |
| `/events` | GET | SSE stream (captions + state) |
| `/api/chat` | POST | Send question to AI (SSE response) |
| `/api/skip` | POST | Skip current text, restart captions |
| `/api/chat/clear` | POST | Clear history + restart captions |
| `/api/stats` | GET | Orchestrator stats (JSON) |
| `/api/keys/stats` | GET | API key rotation stats |
| `/health` | GET | Health check |

### Example: Send Question

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain Docker networking"}'
```

### Example: Get Stats

```bash
curl http://localhost:5000/api/stats
```

**Response:**
```json
{
  "state": "listening",
  "live_text": "How do you troubleshoot high CPU usage on Linux",
  "raw_text": "How do you troubleshoot high CPU usage on Linux",
  "checkpoint": "",
  "checkpoint_length": 0,
  "silence_detected": true,
  "silence_elapsed": 5.2,
  "question_count": 3,
  "capture_running": true
}
```

---

## 📁 Project Structure

```
win-cap-v2/
├── app.py                    # Flask entry point
├── config.py                 # All configuration
├── requirements.txt
├── .env                      # API keys (gitignored)
│
├── core/
│   ├── state.py             # Shared state management
│   ├── capture.py           # Live Captions scraper
│   └── caption_control.py   # Kill/Start/Restart/Hide 
templates
├── api/
│   ├── routes.py            # Flask routes
│   ├── groq_client.py       # Groq API streaming client
│   └── key_manager.py       # Multi-key rotation
│
└── templates/
    └── index.html           # Frontend UI
```

---

## Caption Restart Mechanism

### Why Restart?

Windows Live Captions has a **rolling buffer** that truncates old text. Instead of complex fuzzy matching, we **restart the window** on every Send/Skip for a fresh buffer.

### Implementation

**`core/caption_control.py`:**

```python
def restart_captions():
    """Kill → wait 200ms → start fresh"""
    kill_captions()      # taskkill /F /IM LiveCaptions.exe
    time.sleep(0.2)      # Wait for Windows to cleanup
    start_captions()     # C:\Windows\System32\LiveCaptions.exe
    
    # Background thread: check every 1ms for 3 seconds
    _aggressive_hide()   # Move to (-3000, -3000) off-screen
```

### When It Triggers

| Event | Trigger |
|-------|---------|
| **Send** (Enter key) | ✅ Restart after checkpoint update |
| **Skip** | ✅ Restart after checkpoint update |
| **Clear History** | ✅ Restart + reset all state |
| Normal capture | ❌ No restart |

### Timing

- **Kill:** ~10-50ms
- **Wait:** 200ms (safety buffer)
- **Start:** ~50-100ms
- **Hide:** 1-3 seconds (background, non-blocking)

**Total user-facing delay:** ~250-350ms

---

## Key Features Explained

### 1. Multi-Key Rotation

**Problem:** Groq free tier = 30 requests/min per key

**Solution:** Round-robin across 4 keys = 120 requests/min

```env
# .env
GROQ_API_KEYS=key1,key2,key3,key4
```

**`api/key_manager.py`** automatically cycles:
```
Request 1 → key1
Request 2 → key2
Request 3 → key3
Request 4 → key4
Request 5 → key1 (loop)
```

### 2. Aggressive Window Hiding

**Problem:** Live Captions always shows popup

**Solution:** Background thread checks **every 1ms for 3 seconds**

```python
def _aggressive_hide():
    end_time = time.time() + 3
    while time.time() < end_time:
        _move_offscreen()  # Find window, move to -3000,-3000
        time.sleep(0.001)  # 1ms polling
```

**Result:** Window visible for <10ms (human can't see it)

### 3. Orchestrator States

```python
class OrchestratorState(Enum):
    LISTENING      # Capturing captions
    READY          # 5-sec silence detected
    AI_STREAMING   # AI is responding
```

**State flow:**
```
LISTENING → (5 sec silence) → READY → (Send) → AI_STREAMING → (done) → LISTENING
```

Frontend shows:
- 🔵 **Listening** - normal capture
- 🟢 **Ready to Send** - silence detected, can send
- 🟡 **AI Responding** - streaming in progress

---

## Troubleshooting

### Live Captions Not Found

```
⏳ Waiting for Live Captions... (Press Win+Ctrl+L)
```

**Fix:**
1. Press `Win + Ctrl + L` to open Live Captions
2. Or: `Settings → Accessibility → Captions → Toggle ON`

---

### Window Keeps Appearing

**If `_aggressive_hide()` doesn't work:**

1. Check if `pywin32` installed:
   ```bash
   pip install --force-reinstall pywin32
   ```

2. Try minimize instead (edit `caption_control.py`):
   ```python
   win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
   ```

---

### Rate Limit Errors

```
❌ AI error: Rate limit exceeded
```

**Fix:**
1. Add more API keys in `.env`:
   ```env
   GROQ_API_KEYS=key1,key2,key3,key4
   ```

2. Check rotation stats:
   ```bash
   curl http://localhost:5000/api/keys/stats
   ```

---

### Captions Not Updating

**Check stats:**
```bash
curl http://localhost:5000/api/stats
```

**If `capture_running: false`:**
```python
# In Python console or add to routes.py
import core.state as state
state.resume_capture()
```

---

### Import Error: `win32gui`

```
ModuleNotFoundError: No module named 'win32gui'
```

**Fix:**
```bash
pip install pywin32
python Scripts/pywin32_postinstall.py -install
```

---

## Testing

### Test Caption Restart

```python
# test_restart.py
from core.caption_control import restart_captions
import time

print("Testing restart...")
restart_captions()
print("✅ Done - check if window appeared and disappeared")
time.sleep(5)
```

### Test API Key Rotation

```bash
# Make 10 requests rapidly
for i in {1..10}; do
  curl -X POST http://localhost:5000/api/chat \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Test $i\"}" &
done

# Check which keys were used
curl http://localhost:5000/api/keys/stats
```

---

## 🔐 Security Notes

- **Never commit `.env`** to Git (add to `.gitignore`)
- **Rotate API keys** monthly
- **Use HTTPS** in production (not HTTP)
- **Rate limit** `/api/chat` endpoint (not implemented yet)

---

## 📝 System Prompt

The AI is configured for DevOps/SRE interviews in `config.py`:

```python
AI_SYSTEM_PROMPT = """You are answering DevOps/SRE interview questions...
- Give direct answer first (1-2 sentences)
- Use STAR format for behavioral questions
- Mention trade-offs for senior-level answers
- Use **bold** for key terms, `code` for commands
"""
```

**Customize it** for your use case (change in `config.py`).

---

## 🎓 Use Cases

- **Interview Practice** - Real-time DevOps/SRE Q&A
- **Meeting Assistant** - Capture spoken questions, get instant answers
- **Accessibility Tool** - Voice-to-AI for hands-free research
- **Learning Aid** - Ask questions verbally while coding

---

## 🚀 Performance

### Benchmarks (on i5-8250U, 8GB RAM)

| Metric | Value |
|--------|-------|
| Caption capture latency | ~50-100ms |
| Silence detection accuracy | 99% (5-sec threshold) |
| Window hide time | <10ms (visible) |
| Restart cycle time | 250-350ms |
| AI first token | ~200-500ms |
| AI full response | 2-5 seconds |
| Memory usage | ~150MB (Flask + pywinauto) |

---

## 🛠️ Development

### Run in Debug Mode

```bash
# In config.py
DEBUG = True

# Or environment variable
FLASK_DEBUG=1 python app.py
```

### Add New Route

```python
# api/routes.py
@bp.route('/api/custom', methods=['POST'])
def custom_endpoint():
    data = request.get_json()
    # Your logic here
    return jsonify({'result': 'success'})
```

### Modify AI Prompt

```python
# config.py
AI_SYSTEM_PROMPT = """Your custom system prompt here"""
```

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/amazing`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing`
5. Open Pull Request


## 🙏 Credits
- **Me** - [Linkdin](https://www.linkedin.com/in/rushiwaman95/) 
- **Groq** - Lightning-fast LLM inference
- **Windows Live Captions** - Built-in speech-to-text
- **pywinauto** - Windows UI automation
- **Flask** - Web framework

---

## Quick Start (TL;DR)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Add API key to .env
echo "GROQ_API_KEY=gsk_your_key" > .env

# 3. Enable Live Captions
# Press Win+Ctrl+L

# 4. Run
python app.py

# 5. Open browser
# http://localhost:5000
```

**That's it!** Speak your questions and watch the magic happen.

---

**Made with ❤️❤️ for interview prep**
