import subprocess
import win32gui
import win32con
import time
import threading

def kill_captions():
    subprocess.run(['taskkill', '/F', '/IM', 'LiveCaptions.exe'], 
                   capture_output=True, 
                   creationflags=subprocess.CREATE_NO_WINDOW)
    print("❌ Killed Live Captions")

def move_caption_offscreen():
    """Find Live Captions window and move it off-screen"""
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Live Captions" in title or "Live captions" in title or "Captions" in title:
                # Move window far off-screen (left side)
                win32gui.SetWindowPos(hwnd, None, -3000, -3000, 0, 0, 
                                     win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)
                print(f"📍 Moved off-screen: {title}")
                return False  # Stop searching after found
        return True
    
    win32gui.EnumWindows(callback, None)

def aggressive_hide():
    """Aggressively check for window every 1ms for 3 seconds"""
    end_time = time.time() + 3  # Run for 3 seconds
    count = 0
    
    while time.time() < end_time:
        move_caption_offscreen()
        count += 1
        time.sleep(0.001)  # 1ms delay
    
    print(f"✅ Checked {count} times in 3 seconds")

def start_captions():
    subprocess.Popen([r'C:\Windows\System32\LiveCaptions.exe'],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL,
                     creationflags=subprocess.CREATE_NO_WINDOW)
    print("✅ Starting Live Captions...")
    
    # Start aggressive hiding in background thread
    hide_thread = threading.Thread(target=aggressive_hide, daemon=True)
    hide_thread.start()

def minimize_caption():
    """Minimize Live Captions window"""
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Live Captions" in title or "Live captions" in title or "Captions" in title:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                print(f"➖ Minimized: {title}")
        return True
    
    win32gui.EnumWindows(callback, None)

def make_tiny():
    """Make Live Captions window 1x1 pixel in corner"""
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Live Captions" in title or "Live captions" in title or "Captions" in title:
                # Make tiny and move to top-left corner
                win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, 0, 0, 1, 1, 0)
                print(f"🔬 Made tiny: {title}")
        return True
    
    win32gui.EnumWindows(callback, None)

print("Commands:")
print("  s = start (auto hides every 1ms)")
print("  k = kill")
print("  o = move off-screen")
print("  m = minimize")
print("  t = make tiny (1x1)")
print("  q = quit")

while True:
    cmd = input(">> ").strip().lower()
    if cmd == 's':
        start_captions()
    elif cmd == 'k':
        kill_captions()
    elif cmd == 'o':
        move_caption_offscreen()
    elif cmd == 'm':
        minimize_caption()
    elif cmd == 't':
        make_tiny()
    elif cmd == 'q':
        break
    else:
        print("Unknown command")