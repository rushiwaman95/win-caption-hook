"""
Configuration for Live Captions + AI Chat
Orchestrator + Checkpoint System + Multi-Key Round Robin
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# 🤖 AI MODEL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Support multiple API keys (comma-separated in .env)
# Example in .env file:
# GROQ_API_KEYS=key1,key2,key3,key4
_api_keys_str = os.getenv('GROQ_API_KEYS', os.getenv('GROQ_API_KEY', ''))
GROQ_API_KEYS = [key.strip() for key in _api_keys_str.split(',') if key.strip()]

if not GROQ_API_KEYS:
    print("⚠️  WARNING: No API keys found in .env file!")
    print("   Add: GROQ_API_KEYS=key1,key2,key3,key4")
    GROQ_API_KEYS = ['your-groq-api-key-here']

print(f"✅ Loaded {len(GROQ_API_KEYS)} API key(s)")

GROQ_ENDPOINT = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
GROQ_TIMEOUT = int(os.getenv('GROQ_TIMEOUT', 30))

# ═══════════════════════════════════════════════════════════════════════════
# 🔄 API KEY ROTATION SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

# Rotation strategy: 'round_robin' or 'on_error'
# - round_robin: Rotate key on every request
# - on_error: Only rotate when rate limit hit
KEY_ROTATION_STRATEGY = os.getenv('KEY_ROTATION_STRATEGY', 'round_robin')

# Max retries per request (tries different keys)
MAX_KEY_RETRIES = len(GROQ_API_KEYS)

# Cooldown time for rate-limited keys (seconds)
RATE_LIMIT_COOLDOWN = 60  # Don't use rate-limited key for 60 seconds

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 AI BEHAVIOR
# ═══════════════════════════════════════════════════════════════════════════

AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 512
AI_TOP_P = 0.9

AI_SYSTEM_PROMPT = """You are answering DevOps/SRE interview questions the way a strong candidate would — clear, structured, and technically precise.

**How to answer:**
- Give a direct answer first (1-2 sentences), then expand with reasoning, an example, or a walkthrough
- For "how would you..." or troubleshooting questions, explain your thought process step by step
- For behavioral questions, use the STAR format (Situation, Task, Action, Result)
- Where relevant, mention trade-offs or alternatives — this is what distinguishes a senior-level answer from a junior one
- Keep answers focused; don't pad with unnecessary background

**Technical accuracy:**
- Use correct, current terminology for CI/CD, Docker/Kubernetes, AWS/GCP/Azure, Terraform/Ansible, Linux, networking, and monitoring/observability
- If a question could apply to multiple tools/providers, briefly state the assumption you're making (e.g. "Assuming AWS...")

**Style:**
- Use **bold** for key terms, `inline code` for commands/tools/flags, and code blocks for scripts or configs if needed
- For complex topics, optionally add a short note on what a follow-up question might dig into"""

# ═══════════════════════════════════════════════════════════════════════════
# 🎤 CAPTION SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

CAPTION_POLL_INTERVAL = 0.05  # 50ms

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 ORCHESTRATOR SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

SILENCE_THRESHOLD = 5.0  # Seconds of silence to mark question as "ready"
SIMILARITY_THRESHOLD = 0.7  # 70% match for fuzzy overlap detection
MIN_QUESTION_LENGTH = 10  # Minimum chars to consider valid

# ═══════════════════════════════════════════════════════════════════════════
# 💬 CHAT SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

ENABLE_CHAT_HISTORY = False
MAX_CHAT_HISTORY = 0

# ═══════════════════════════════════════════════════════════════════════════
# 🌐 SERVER SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

HOST = '0.0.0.0'
PORT = 5000
DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 UI SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

APP_TITLE = 'Live Captions + AI Chat'
ENABLE_MARKDOWN = True
ENABLE_CODE_HIGHLIGHTING = True