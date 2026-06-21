"""
Live Captions Window Controller
Kill, Start, Restart with aggressive hide
"""

import subprocess
import time
import threading
import win32gui
import win32con


def kill_captions():
    """Kill Live Captions process"""
    subprocess.run(['taskkill', '/F', '/IM', 'LiveCaptions.exe'],
                   capture_output=True,
                   creationflags=subprocess.CREATE_NO_WINDOW)


def start_captions():
    """Start Live Captions and aggressively hide"""
    subprocess.Popen([r'C:\Windows\System32\LiveCaptions.exe'],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL,
                     creationflags=subprocess.CREATE_NO_WINDOW)

    # Hide in background thread
    hide_thread = threading.Thread(target=_aggressive_hide, daemon=True)
    hide_thread.start()


def restart_captions():
    """Kill → wait 200ms → start fresh"""
    kill_captions()
    time.sleep(0.2)
    start_captions()


def _move_offscreen():
    """Move Live Captions window off-screen"""
    found = False

    def callback(hwnd, _):
        nonlocal found
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Live Captions" in title or "Live captions" in title or "Captions" in title:
                win32gui.SetWindowPos(hwnd, None, -3000, -3000, 0, 0,
                                     win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)
                found = True
        return True

    win32gui.EnumWindows(callback, None)
    return found


def _aggressive_hide():
    """Check every 1ms for 3 seconds to hide window"""
    end_time = time.time() + 3

    while time.time() < end_time:
        _move_offscreen()
        time.sleep(0.001)