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
CARDS = []
LIVE_TEXT = ""
LOCK = threading.Lock()

# sentence tracking
STABLE_SENTENCES = []      # sentences confirmed stable
LAST_SENTENCES = []        # last seen sentence list
LAST_CHANGE_TIME = 0       # when LAST_SENTENCES last changed
FINALIZED_COUNT = 0        # how many sentences already turned into cards

STABLE_WAIT = 1.5          # seconds a sentence must stay unchanged


def get_tail(text):
    m = list(re.finditer(r'[.!?]', text))
    return text[m[-1].end():].strip() if m else text.strip()


# ─── ROUTES ───
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/stream')
def stream():
    with LOCK:
        # live = any stable sentences not yet carded + incomplete tail
        pending = STABLE_SENTENCES[FINALIZED_COUNT:]
        parts = list(pending)
        if LIVE_TEXT:
            tail = get_tail(LIVE_TEXT)
            if tail:
                parts.append(tail)
        return jsonify({
            'current': ' '.join(parts).strip(),
            'cards': list(CARDS),
            'count': len(CARDS)
        })


# ─── CAPTURE THREAD ───
def capture():
    global LIVE_TEXT

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

        except Exception as e:
            print(f"⚠️ Reconnecting... {str(e)[:30]}")
            try:
                win = desktop.window(title="Live Captions")
            except:
                pass
            time.sleep(0.3)

        time.sleep(0.05)


# ─── SENTENCE DETECTOR THREAD ───
def sentence_detector():
    global LAST_SENTENCES, LAST_CHANGE_TIME, FINALIZED_COUNT

    while True:
        with LOCK:
            if LIVE_TEXT:
                # extract complete sentences from current text
                found = re.findall(r'[^.!?]+[.!?]', LIVE_TEXT)
                current = [s.strip() for s in found if len(s.strip()) >= 5]

                # did the sentence list change?
                if current != LAST_SENTENCES:
                    LAST_SENTENCES = current
                    LAST_CHANGE_TIME = time.time()
                else:
                    # stable long enough? lock in ALL current complete sentences
                    if current and time.time() - LAST_CHANGE_TIME >= STABLE_WAIT:
                        # add any new stable sentences
                        for s in current:
                            if s not in STABLE_SENTENCES:
                                STABLE_SENTENCES.append(s)

                        # make cards from pairs
                        while len(STABLE_SENTENCES) - FINALIZED_COUNT >= 2:
                            s1 = STABLE_SENTENCES[FINALIZED_COUNT]
                            s2 = STABLE_SENTENCES[FINALIZED_COUNT + 1]
                            card = (s1 + ' ' + s2).strip()
                            CARDS.append(card)
                            FINALIZED_COUNT += 2
                            print(f"📝 Card: {card[:80]}")

        time.sleep(0.3)


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
    threading.Thread(target=sentence_detector, daemon=True).start()
    ip = get_ip()
    print(f"\n  🚀 http://{ip}:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)