from pywinauto import Desktop
from flask import Flask, render_template, jsonify
import threading
import socket
import logging
import time
import re
import hashlib
import warnings
from queue import Queue, Empty
from collections import deque

warnings.filterwarnings("ignore")

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# ─── STORAGE ───
CARDS = []
SENTENCE_BUFFER = []
LIVE_PARTIAL = ""
LAST_CHANGE = 0
LOCK = threading.Lock()

# ─── QUEUE ───
RAW_QUEUE = Queue(maxsize=200)

# ─── DEDUP (fast only) ───
SEEN_HASHES = set()
RECENT_NORMS = deque(maxlen=15)

SILENCE_SEC = 5


def normalize(text):
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text


def fast_hash(sentence):
    return hashlib.md5(normalize(sentence).encode()).hexdigest()[:12]


def is_duplicate(sentence):
    h = fast_hash(sentence)
    if h in SEEN_HASHES:
        return True

    norm = normalize(sentence)
    for existing_norm in RECENT_NORMS:
        if norm in existing_norm or existing_norm in norm:
            if len(norm) <= len(existing_norm):
                return True
    return False


def register(sentence):
    SEEN_HASHES.add(fast_hash(sentence))
    RECENT_NORMS.append(normalize(sentence))


def try_flush():
    while len(SENTENCE_BUFFER) >= 2:
        s1 = SENTENCE_BUFFER.pop(0)
        s2 = SENTENCE_BUFFER.pop(0)
        card = s1 + ' ' + s2
        CARDS.append(card)
        print(f"📝 Card: {card[:80]}")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/stream')
def stream():
    with LOCK:
        parts = list(SENTENCE_BUFFER)
        if LIVE_PARTIAL:
            parts.append(LIVE_PARTIAL)
        current = ' '.join(parts) if parts else ''
        return jsonify({
            'current': current,
            'cards': list(CARDS)
        })


# ─── THREAD 1: CAPTURE (ultra light) ───
def capture():
    print("🔍 Looking for Live Captions...")
    desktop = Desktop(backend="uia")

    win = None
    while win is None:
        try:
            win = desktop.window(title="Live Captions")
            print("✅ Found!")
        except:
            print("⏳ Press Win+Ctrl+L to start Live Captions")
            time.sleep(1)

    print("🎤 Streaming...\n")
    prev = ""

    while True:
        try:
            elements = win.descendants(control_type="Text")
            parts = []
            for el in elements:
                t = el.window_text()
                if t and t.strip() and t.strip() != "Live Captions":
                    parts.append(t.strip())

            if not parts:
                time.sleep(0.05)
                continue

            raw = " ".join(parts).strip()

            if raw != prev:
                prev = raw
                if not RAW_QUEUE.full():
                    RAW_QUEUE.put_nowait(raw)

        except Exception as e:
            print(f"⚠️ Reconnecting... {str(e)[:30]}")
            try:
                win = desktop.window(title="Live Captions")
            except:
                pass
            time.sleep(0.3)

        time.sleep(0.05)


# ─── THREAD 2: PROCESSOR (fast) ───
def processor():
    global LIVE_PARTIAL, LAST_CHANGE

    while True:
        try:
            raw = RAW_QUEUE.get(timeout=0.1)
        except Empty:
            continue

        sentences = re.split(r'(?<=[.!?])\s+', raw)

        with LOCK:
            LAST_CHANGE = time.time()
            LIVE_PARTIAL = ""

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                if not re.search(r'[.!?]$', sentence):
                    LIVE_PARTIAL = sentence
                    continue

                if len(sentence) < 20:
                    continue

                if is_duplicate(sentence):
                    continue

                register(sentence)
                SENTENCE_BUFFER.append(sentence)
                print(f"  ✓ {sentence[:60]}...")

            try_flush()


# ─── THREAD 3: SILENCE FLUSH ───
def silence_detector():
    while True:
        with LOCK:
            if SENTENCE_BUFFER and time.time() - LAST_CHANGE >= SILENCE_SEC:
                card = ' '.join(SENTENCE_BUFFER)
                CARDS.append(card)
                print(f"📝 Final: {card[:80]}")
                SENTENCE_BUFFER.clear()
        time.sleep(0.5)


def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


if __name__ == '__main__':
    threading.Thread(target=capture, daemon=True).start()
    threading.Thread(target=processor, daemon=True).start()
    threading.Thread(target=silence_detector, daemon=True).start()
    ip = get_ip()
    print(f"\n  🚀 http://{ip}:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)