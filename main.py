from pywinauto import Desktop
from flask import Flask, render_template, jsonify
import threading
import socket
import logging
import time
import re
import warnings

warnings.filterwarnings("ignore")

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# ─── STORAGE ───
CARDS = []               # finalized card texts
LIVE_TEXT = ""            # current streaming text
LAST_CHANGE = 0          # timestamp of last LIVE_TEXT change
SAVED_ALL = ""           # all card text joined (for overlap detection)
LAST_FINALIZED = ""      # prevent re-firing on same text
LOCK = threading.Lock()

SILENCE_SEC = 5


def normalize(s):
    return re.sub(r'\s+', ' ', s.strip())


def find_new_portion(current, saved):
    """
    Find where the tail of `saved` overlaps the head of `current`,
    return only the NEW tail of `current`.

    saved : "Hello how are you"
    curr  : "how are you I am fine"
    overlap: "how are you"  (3 words)
    return : "I am fine"
    """
    curr = normalize(current)
    if not curr:
        return ""
    if not saved:
        return curr

    saved_words = saved.lower().split()[-200:]   # only check recent history
    curr_words  = curr.split()
    curr_lower  = [w.lower() for w in curr_words]

    max_check = min(len(saved_words), len(curr_lower))

    for length in range(max_check, 0, -1):
        if saved_words[-length:] == curr_lower[:length]:
            return ' '.join(curr_words[length:]).strip()

    return curr   # no overlap found → everything is new


# ─── ROUTES ───
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/stream')
def stream():
    with LOCK:
        display_live = find_new_portion(LIVE_TEXT, SAVED_ALL) if LIVE_TEXT else ""
        return jsonify({
            'current': display_live,
            'cards': list(CARDS)
        })


# ─── CAPTURE THREAD ───
def capture():
    global LIVE_TEXT, LAST_CHANGE

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
    prev_text = ""

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

            if raw == prev_text:
                time.sleep(0.05)
                continue

            prev_text = raw

            with LOCK:
                LIVE_TEXT = raw
                LAST_CHANGE = time.time()

        except Exception as e:
            print(f"⚠️ Reconnecting... {str(e)[:30]}")
            try:
                win = desktop.window(title="Live Captions")
            except:
                pass
            time.sleep(0.3)

        time.sleep(0.05)


# ─── SILENCE DETECTOR THREAD ───
def silence_detector():
    global LAST_FINALIZED, SAVED_ALL, LIVE_TEXT

    while True:
        with LOCK:
            if LIVE_TEXT and LIVE_TEXT != LAST_FINALIZED:
                if time.time() - LAST_CHANGE >= SILENCE_SEC:
                    new_part = find_new_portion(LIVE_TEXT, SAVED_ALL)

                    if new_part and len(new_part) >= 3:
                        CARDS.append(new_part)
                        SAVED_ALL = (SAVED_ALL + ' ' + new_part).strip() \
                                    if SAVED_ALL else new_part
                        print(f"📝 Card: {new_part[:80]}")

                    LAST_FINALIZED = LIVE_TEXT
                    LIVE_TEXT = ""          # clear → live card disappears
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
    threading.Thread(target=silence_detector, daemon=True).start()
    ip = get_ip()
    print(f"\n  🚀 http://{ip}:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)