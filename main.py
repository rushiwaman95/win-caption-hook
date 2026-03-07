from pywinauto import Desktop
from flask import Flask, render_template, jsonify, request, Response
import threading
import json
import socket
import logging
import time
import re
import warnings
import os

# Suppress warnings from google.generativeai about deprecation
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
warnings.filterwarnings("ignore", category=UserWarning, module="google.generativeai")

import google.generativeai as genai
from itertools import cycle 

# Disable Flask logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# --- 🧠 AI CONFIGURATION ---

key_pool = None
WORKING_MODEL_NAME = "gemini-3-flash-preview"

# Shorter prompt = faster first token
SYSTEM_PROMPT = """You are an AWS DevOps expert helping with interview prep.
Rules: Be concise. Use HTML: <ul><li> for lists, <b> for key terms. Max 5 points."""

def setup_keys():
    global key_pool
    print("\n" + "="*50)
    print("      🔑 GEMINI API KEY SETUP      ")
    print("="*50 + "\n")
    
    while True:
        try:
            count = int(input("How many Gemini API keys do you have? "))
            if count > 0:
                break
            print("Please enter a number greater than 0.")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
    api_keys = []
    for i in range(count):
        while True:
            key = input(f"Enter API Key #{i+1}: ").strip()
            if key:
                api_keys.append(key)
                break
            print("Key cannot be empty.")
            
    key_pool = cycle(api_keys)
    print("\n✅ Keys configured successfully!\n")


# 🚀 NEW: Streaming AI Response
@app.route('/ask_ai_stream', methods=['POST'])
def ask_ai_stream():
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return Response("data: {\"error\": \"No text\"}\n\n", mimetype='text/event-stream')
    
    def generate():
        global key_pool, WORKING_MODEL_NAME
        
        if key_pool is None:
            yield f"data: {json.dumps({'error': 'API keys not configured'})}\n\n"
            return
        
        current_key = next(key_pool)
        print(f"🔑 Using Key: ...{current_key[-6:]}")
        
        try:
            genai.configure(api_key=current_key)
            model = genai.GenerativeModel(WORKING_MODEL_NAME)
            
            prompt = f"{SYSTEM_PROMPT}\n\nQuestion: {text}"
            
            # 🚀 STREAMING: stream=True
            response = model.generate_content(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'chunk': chunk.text})}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            print(f"❌ Error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    })


# Fallback non-streaming endpoint
def get_ai_response(user_text):
    global WORKING_MODEL_NAME, key_pool
    
    if key_pool is None:
        return "Error: API keys not configured."
    
    current_key = next(key_pool)
    print(f"🔑 Using Key: ...{current_key[-6:]}") 
    
    try:
        genai.configure(api_key=current_key)
        prompt = f"{SYSTEM_PROMPT}\n\nQuestion: {user_text}"
        model = genai.GenerativeModel(WORKING_MODEL_NAME)
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return f"<span style='color:red'>Error: {str(e)}</span>"


# -----------------------------------------

# Storage
TRANSCRIPT_SENTENCES = []
SEEN_FINGERPRINTS = set()
LAST_WINDOW_TEXT = ""


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/get_caption')
def get_caption():
    return jsonify({'sentences': TRANSCRIPT_SENTENCES})


@app.route('/ask_ai', methods=['POST'])
def ask_ai_route():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'answer': 'No text selected.'})
    
    answer = get_ai_response(text)
    return jsonify({'answer': answer})


def normalize(text):
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text


def get_fingerprint(sentence):
    return normalize(sentence)[:50]


def is_duplicate(sentence):
    fp = get_fingerprint(sentence)
    
    if fp in SEEN_FINGERPRINTS:
        return True
    
    norm = normalize(sentence)
    for existing in TRANSCRIPT_SENTENCES[-20:]:
        existing_norm = normalize(existing)
        if norm in existing_norm or existing_norm in norm:
            if len(norm) <= len(existing_norm):
                return True
    
    return False


def capture_captions():
    global LAST_WINDOW_TEXT
    
    print("--- Searching for 'Live captions' window ---")
    desktop = Desktop(backend="uia")
    
    caption_window = None
    
    while caption_window is None:
        try:
            caption_window = desktop.window(title="Live Captions")
            print("✓ Found 'Live Captions' window!")
        except:
            print("⏳ Waiting... (Press Win+Ctrl+L)")
            time.sleep(2)
    
    print("--- Transcript Started ---")
    
    while True:
        try:
            text_elements = caption_window.descendants(control_type="Text")
            parts = []
            
            for t in text_elements:
                txt = t.window_text()
                if txt and txt != "Live Captions":
                    parts.append(txt)
            
            if not parts:
                time.sleep(2)
                continue
            
            current_text = " ".join(parts).strip()
            
            if current_text == LAST_WINDOW_TEXT:
                time.sleep(2)
                continue
            
            LAST_WINDOW_TEXT = current_text
            
            sentences = re.split(r'(?<=[.!?])\s+', current_text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                
                if len(sentence) < 30:
                    continue
                
                if not re.search(r'[.!?]$', sentence):
                    continue
                
                if is_duplicate(sentence):
                    continue
                
                fp = get_fingerprint(sentence)
                SEEN_FINGERPRINTS.add(fp)
                TRANSCRIPT_SENTENCES.append(sentence)
                print(f"✓ {sentence[:60]}...")
                
        except:
            print("Reconnecting...(Press Win+Ctrl+L)")
            try:
                caption_window = desktop.window(title="Live Captions")
            except:
                pass
            
        time.sleep(2)


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
    setup_keys()
    threading.Thread(target=capture_captions, daemon=True).start()
    print(f"Open: http://{get_ip()}:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)