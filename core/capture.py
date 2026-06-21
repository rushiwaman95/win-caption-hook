"""
Windows Live Captions capture - Orchestrator
Live Captions restarts on each Send/Skip - no fuzzy matching needed
"""

import time
import re
from pywinauto import Desktop
import core.state as state
from config import CAPTION_POLL_INTERVAL


def find_window(desktop):
    """Try to find Live Captions window"""
    for title in ["Live Captions", "Live captions", "Captions"]:
        try:
            win = desktop.window(title=title)
            return win
        except:
            continue
    return None


def capture():
    """Main capture loop with orchestrator"""

    print("🔍 Starting caption capture with orchestrator...")

    desktop = Desktop(backend="uia")
    win = None
    retry_count = 0

    # Initial window search
    while win is None:
        win = find_window(desktop)
        if win is None:
            retry_count += 1
            if retry_count % 5 == 0:
                print(f"⏳ Waiting for Live Captions... (Press Win+Ctrl+L)")
            time.sleep(1)

    print("✅ Capture active\n")

    prev_text = ""
    state.reset_silence()  # Initialize timer

    while True:
        try:
            # ── PAUSE CHECK ────────────────────────────────
            state.CAPTURE_EVENT.wait()
            # ───────────────────────────────────────────────

            # Scrape Windows caption
            text_elements = win.descendants(control_type="Text")
            edit_elements = win.descendants(control_type="Edit")
            all_elements = text_elements + edit_elements

            parts = []
            for el in all_elements:
                try:
                    text = el.window_text().strip()
                    if text and text != "Live Captions" and len(text) > 0:
                        parts.append(text)
                except:
                    continue

            if not parts:
                # No text - update silence timer
                state.update_silence_status(has_new_text=False)
                time.sleep(CAPTION_POLL_INTERVAL)
                continue

            raw = " ".join(parts)
            raw = re.sub(r'\s+', ' ', raw).strip()

            if len(raw) < 2:
                state.update_silence_status(has_new_text=False)
                time.sleep(CAPTION_POLL_INTERVAL)
                continue

            # ── ORCHESTRATOR LOGIC ─────────────────────────
            with state.LOCK:
                # Always update RAW_TEXT
                state.RAW_TEXT = raw
                
                # Only process if text actually changed
                if raw != prev_text:
                    prev_text = raw
                    
                    # Direct display - no checkpoint stripping
                    # Live Captions restarts fresh on each Send/Skip
                    state.LIVE_TEXT = raw
                    
                    # Reset silence timer (new text arrived)
                    state.update_silence_status(has_new_text=True)
                else:
                    # No new text - check silence
                    state.update_silence_status(has_new_text=False)
            # ───────────────────────────────────────────────

        except Exception as e:
            # print(f"⚠️ Capture error: {e}")
            win = None
            while win is None:
                state.CAPTURE_EVENT.wait()
                win = find_window(desktop)
                if win is None:
                    time.sleep(1)

        time.sleep(CAPTION_POLL_INTERVAL)