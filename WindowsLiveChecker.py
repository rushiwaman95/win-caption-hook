import uiautomation as auto

# Find Live Captions window (ctrl+win+L)
window = auto.WindowControl(Name="Live Captions")

if window.Exists():
    print("Found Live Captions window!")
else:
    print("Not found. Is Live Captions ON?")