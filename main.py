from pywinauto import Desktop
from flask import Flask, render_template, jsonify, request
import threading
import socket
import logging
import time
import re
import warnings
import os

# Suppress warnings from google.generativeai about deprecation
# We are doing this to maintain stability while the new library is adopted
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
warnings.filterwarnings("ignore", category=UserWarning, module="google.generativeai")

import google.generativeai as genai
from itertools import cycle 

# Disable Flask logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# --- 🧠 AI CONFIGURATION ---

# Global variable to hold the iterator
key_pool = None

# 3. Working Model
WORKING_MODEL_NAME = "gemini-3-flash-preview" 

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

def get_ai_response(user_text):
    global WORKING_MODEL_NAME, key_pool
    
    if key_pool is None:
        return "Error: API keys not configured."
    
    # Get next key
    current_key = next(key_pool)
    print(f"🔑 Using Key: ...{current_key[-6:]}") 
    
    try:
        genai.configure(api_key=current_key)
        
        # --- UPDATED PROMPT FOR HUMAN-LIKE, FORMATTED ANSWERS ---
        prompt = f"""
        You are a smart, professional AWS DevOps engineer who is helpong a friend to crack the technical interview.

        CONTEXT FROM USER:
        "{user_text}"
        
        YOUR TASK:
        1. Answer the implied question.
        2. TONE: Professional, short, and direct. Do NOT say "As an AI" or "Based on the text". Just give the answer.
        3. FORMAT: You MUST return the answer using HTML tags. Use <ul> for the list and <li> for points. Use <b> for key terms.
        4. LENGTH: Keep it under 5 bullet points.
        5. If the user asks for a code snippet, provide it in a code block.
        6. Answer all questions in a professional and informative manner but keep it short, simple and concise.
        """

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
    
    # Call our load balanced function
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
    app.run(host='0.0.0.0', port=5000, debug=False)