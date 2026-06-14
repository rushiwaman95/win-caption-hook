"""
Windows Live Captions capture - Orchestrator + Fuzzy Matching
"""

import time
import re
from difflib import SequenceMatcher
from pywinauto import Desktop
import core.state as state
from config import CAPTION_POLL_INTERVAL, SIMILARITY_THRESHOLD


def find_window(desktop):
    """Try to find Live Captions window"""
    for title in ["Live Captions", "Live captions", "Captions"]:
        try:
            win = desktop.window(title=title)
            print(f"✅ Live Captions found: '{title}'")
            return win
        except:
            continue
    return None


def fuzzy_strip_checkpoint(raw: str, checkpoint: str) -> str:
    """
    Strip checkpoint from raw using fuzzy matching.
    Handles Windows truncation.
    
    Returns: New text only
    """
    if not checkpoint:
        return raw
    
    if not raw:
        return ""
    
    raw_lower = raw.lower().strip()
    checkpoint_lower = checkpoint.lower().strip()
    
    # Case 1: Exact prefix match (fastest)
    if raw_lower.startswith(checkpoint_lower):
        return raw[len(checkpoint):].strip()
    
    # Case 2: Raw is subset of checkpoint (Windows behind)
    if checkpoint_lower.find(raw_lower) != -1:
        return ""
    
    # Case 3: Fuzzy overlap (Windows truncated)
    raw_words = raw.split()
    checkpoint_words = checkpoint.split()
    
    if not raw_words or not checkpoint_words:
        return raw
    
    best_overlap_idx = 0
    best_similarity = 0.0
    
    # Find best overlap between checkpoint end and raw start
    for i in range(1, min(len(checkpoint_words), len(raw_words)) + 1):
        checkpoint_suffix = ' '.join(checkpoint_words[-i:])
        raw_prefix = ' '.join(raw_words[:i])
        
        ratio = SequenceMatcher(None, checkpoint_suffix.lower(), raw_prefix.lower()).ratio()
        
        if ratio > best_similarity:
            best_similarity = ratio
            best_overlap_idx = i
    
    # If good overlap found (>70%)
    if best_similarity >= SIMILARITY_THRESHOLD:
        new_words = raw_words[best_overlap_idx:]
        new_text = ' '.join(new_words)
        
        print(f"🔄 Fuzzy overlap: {best_similarity:.0%} similar, {best_overlap_idx} words")
        
        # Update checkpoint to current raw (sync after truncation)
        with state.LOCK:
            state.CHECKPOINT_BUFFER = raw
        
        return new_text
    
    # Case 4: No overlap - major change (user cleared or new session)
    print(f"⚠️ No overlap ({best_similarity:.0%}) - resetting checkpoint")
    with state.LOCK:
        state.CHECKPOINT_BUFFER = ""
    
    return raw


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
                    
                    # Strip checkpoint from raw
                    checkpoint = state.CHECKPOINT_BUFFER
                    new_text = fuzzy_strip_checkpoint(raw, checkpoint)
                    
                    # Update display
                    state.LIVE_TEXT = new_text
                    
                    # Reset silence timer (new text arrived)
                    state.update_silence_status(has_new_text=True)
                else:
                    # No new text - check silence
                    state.update_silence_status(has_new_text=False)
            # ───────────────────────────────────────────────

        except Exception as e:
            print(f"⚠️ Capture error: {e}")
            win = None
            while win is None:
                state.CAPTURE_EVENT.wait()
                win = find_window(desktop)
                if win is None:
                    time.sleep(1)

        time.sleep(CAPTION_POLL_INTERVAL)