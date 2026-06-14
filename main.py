"""
Main entry - DEBUG MODE
"""

import threading
import socket
import logging
from flask import Flask

from core.capture import capture
from api.routes import bp
from config import HOST, PORT, DEBUG, SECRET_KEY, APP_TITLE

# Keep werkzeug quiet
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.register_blueprint(bp)

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    print("\n" + "="*70)
    print(f"  {APP_TITLE} - DEBUG MODE")
    print("="*70)
    
    print("\n🔧 Starting capture thread...")
    threading.Thread(target=capture, daemon=True).start()
    
    ip = get_local_ip()
    
    print("\n" + "="*70)
    print("SERVER RUNNING")
    print("="*70)
    print(f"  🌐 Local:   http://127.0.0.1:{PORT}")
    print(f"  🌐 Network: http://{ip}:{PORT}")
    print("\n  📡 Debug endpoints:")
    print(f"     http://127.0.0.1:{PORT}/debug/caption")
    print("\n  💡 Steps:")
    print("     1. Press Win+Ctrl+L (Live Captions)")
    print("     2. Start speaking")
    print("     3. Watch terminal for logs")
    print("="*70 + "\n")
    
    app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True, use_reloader=False)