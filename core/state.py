"""
Shared application state - Orchestrator + Checkpoint System
"""

import threading
import time
from enum import Enum
from typing import List, Dict

# ═══════════════════════════════════════════════════════════════════════════
# State Variables
# ═══════════════════════════════════════════════════════════════════════════

LOCK = threading.RLock()

# Caption state
LIVE_TEXT: str = ""  # Current display text (after stripping checkpoint)
RAW_TEXT: str = ""   # Full Windows caption text

# Checkpoint system
CHECKPOINT_BUFFER: str = ""  # Last confirmed text (sent or skipped)

# Orchestrator state
class OrchestratorState(Enum):
    LISTENING = "listening"      # Actively capturing
    READY = "ready"              # 5 sec silence detected
    AI_STREAMING = "ai_streaming"  # AI is responding

ORCHESTRATOR_STATE: OrchestratorState = OrchestratorState.LISTENING

# Silence detection
LAST_TEXT_UPDATE: float = 0.0  # Timestamp of last text change
SILENCE_DETECTED: bool = False

# Threading control
CAPTURE_EVENT = threading.Event()
CAPTURE_EVENT.set()

# Chat history
CHAT_HISTORY: List[Dict[str, str]] = []
QUESTION_COUNT: int = 0

# ═══════════════════════════════════════════════════════════════════════════
# Checkpoint Management
# ═══════════════════════════════════════════════════════════════════════════

def update_checkpoint(text: str = ""):
    """Update checkpoint buffer (called on Send or Skip)"""
    global CHECKPOINT_BUFFER, LIVE_TEXT, RAW_TEXT, QUESTION_COUNT
    with LOCK:
        # Use raw text if available, otherwise use provided text
        CHECKPOINT_BUFFER = RAW_TEXT if RAW_TEXT else text
        LIVE_TEXT = ""
        RAW_TEXT = ""
        if text:  # Only increment if actually sending/skipping
            QUESTION_COUNT += 1


def get_checkpoint() -> str:
    """Get current checkpoint"""
    with LOCK:
        return CHECKPOINT_BUFFER


# ═══════════════════════════════════════════════════════════════════════════
# Orchestrator State Management
# ═══════════════════════════════════════════════════════════════════════════

def set_state(state: OrchestratorState):
    """Set orchestrator state"""
    global ORCHESTRATOR_STATE
    with LOCK:
        ORCHESTRATOR_STATE = state


def get_state() -> OrchestratorState:
    """Get orchestrator state"""
    with LOCK:
        return ORCHESTRATOR_STATE


def update_silence_status(has_new_text: bool):
    """Update silence detection status"""
    global LAST_TEXT_UPDATE, SILENCE_DETECTED
    with LOCK:
        if has_new_text:
            LAST_TEXT_UPDATE = time.time()
            SILENCE_DETECTED = False
        else:
            elapsed = time.time() - LAST_TEXT_UPDATE
            from config import SILENCE_THRESHOLD
            if elapsed >= SILENCE_THRESHOLD and not SILENCE_DETECTED:
                SILENCE_DETECTED = True
                if ORCHESTRATOR_STATE == OrchestratorState.LISTENING:
                    set_state(OrchestratorState.READY)


def is_silence_detected() -> bool:
    """Check if silence threshold reached"""
    with LOCK:
        return SILENCE_DETECTED


def reset_silence():
    """Reset silence detection"""
    global LAST_TEXT_UPDATE, SILENCE_DETECTED
    with LOCK:
        LAST_TEXT_UPDATE = time.time()
        SILENCE_DETECTED = False


# ═══════════════════════════════════════════════════════════════════════════
# Capture Control
# ═══════════════════════════════════════════════════════════════════════════

def pause_capture():
    """Pause caption capture"""
    CAPTURE_EVENT.clear()


def resume_capture():
    """Resume caption capture"""
    CAPTURE_EVENT.set()
    reset_silence()


# ═══════════════════════════════════════════════════════════════════════════
# Chat History
# ═══════════════════════════════════════════════════════════════════════════

def add_chat_message(role: str, content: str):
    """Add message to chat history"""
    global CHAT_HISTORY
    with LOCK:
        CHAT_HISTORY.append({
            "role": role,
            "content": content
        })


def get_chat_history() -> List[Dict[str, str]]:
    """Get chat history"""
    with LOCK:
        return list(CHAT_HISTORY)


def reset_chat_history():
    """Clear chat history"""
    global CHAT_HISTORY
    with LOCK:
        CHAT_HISTORY.clear()


# ═══════════════════════════════════════════════════════════════════════════
# Full Reset
# ═══════════════════════════════════════════════════════════════════════════

def reset_all():
    """Reset everything"""
    global LIVE_TEXT, RAW_TEXT, CHECKPOINT_BUFFER, CHAT_HISTORY, QUESTION_COUNT
    global SILENCE_DETECTED, ORCHESTRATOR_STATE
    with LOCK:
        LIVE_TEXT = ""
        RAW_TEXT = ""
        CHECKPOINT_BUFFER = ""
        CHAT_HISTORY.clear()
        QUESTION_COUNT = 0
        SILENCE_DETECTED = False
        ORCHESTRATOR_STATE = OrchestratorState.LISTENING
        reset_silence()


# ═══════════════════════════════════════════════════════════════════════════
# Stats
# ═══════════════════════════════════════════════════════════════════════════

def get_stats() -> Dict:
    """Get current stats"""
    with LOCK:
        elapsed = time.time() - LAST_TEXT_UPDATE if LAST_TEXT_UPDATE > 0 else 0
        return {
            'state': ORCHESTRATOR_STATE.value,
            'live_text': LIVE_TEXT[:100],
            'raw_text': RAW_TEXT[:100],
            'checkpoint': CHECKPOINT_BUFFER[-100:] if CHECKPOINT_BUFFER else "",
            'checkpoint_length': len(CHECKPOINT_BUFFER),
            'silence_detected': SILENCE_DETECTED,
            'silence_elapsed': round(elapsed, 1),
            'question_count': QUESTION_COUNT,
            'capture_running': CAPTURE_EVENT.is_set(),
        }