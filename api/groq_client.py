"""
Groq client with multi-key round-robin support
"""

import json
import time
import requests
from typing import Generator
from api.key_manager import key_manager
from config import (
    GROQ_ENDPOINT, GROQ_MODEL, GROQ_TIMEOUT,
    AI_TEMPERATURE, AI_MAX_TOKENS, AI_TOP_P, AI_SYSTEM_PROMPT,
    MAX_KEY_RETRIES
)


def stream_chat(messages: list[dict]) -> Generator[str, None, None]:
    """Stream from Groq with automatic key rotation on rate limits"""
    
    request_id = int(time.time() * 1000) % 10000
    
    full_messages = [{"role": "system", "content": AI_SYSTEM_PROMPT}] + messages
    
    payload = {
        'model': GROQ_MODEL,
        'messages': full_messages,
        'temperature': AI_TEMPERATURE,
        'max_tokens': AI_MAX_TOKENS,
        'top_p': AI_TOP_P,
        'stream': True,
    }
    
    # Try multiple keys if rate limited
    for attempt in range(MAX_KEY_RETRIES):
        # Get next available key
        api_key = key_manager.get_next_key()
        
        if not api_key:
            raise Exception("⏱️ All API keys are rate-limited. Please wait.")
        
        stats = key_manager.get_stats()
        current_key_num = stats['current_key_index']
        
        print(f"🚀 Groq API [{request_id}] attempt #{attempt+1} using key #{current_key_num}")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        
        try:
            response = requests.post(
                GROQ_ENDPOINT,
                headers=headers,
                json=payload,
                stream=True,
                timeout=GROQ_TIMEOUT
            )
            
            # Check for rate limit BEFORE processing
            if response.status_code == 429:
                print(f"⚠️ Rate limit hit on key #{current_key_num}")
                key_manager.mark_rate_limited(api_key)
                
                # Try next key
                if attempt < MAX_KEY_RETRIES - 1:
                    print(f"🔄 Retrying with next key...")
                    continue
                else:
                    raise Exception("⏱️ Rate limit exceeded on all keys")
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            # Success - stream the response
            chunk_count = 0
            
            for line in response.iter_lines():
                if not line:
                    continue
                    
                line = line.decode('utf-8')
                
                if line.startswith(':'):
                    continue
                
                if line.startswith('data: '):
                    data_str = line[6:]
                    
                    if data_str.strip() == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        
                        if 'choices' in data and data['choices']:
                            choice = data['choices'][0]
                            delta = choice.get('delta', {})
                            content = delta.get('content', '')
                            
                            if content:
                                chunk_count += 1
                                yield content
                            
                            if choice.get('finish_reason') == 'stop':
                                break
                    
                    except json.JSONDecodeError:
                        continue
            
            print(f"✅ Success with key #{current_key_num} ({chunk_count} chunks)")
            return  # Success - exit function
                    
        except requests.exceptions.Timeout:
            print(f"❌ Timeout on key #{current_key_num}")
            key_manager.mark_error(api_key)
            raise Exception("⏱️ Request timeout")
        
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            print(f"❌ HTTP {status} on key #{current_key_num}")
            
            # Mark rate limit
            if status == 429:
                key_manager.mark_rate_limited(api_key)
                if attempt < MAX_KEY_RETRIES - 1:
                    continue
            else:
                key_manager.mark_error(api_key)
            
            error_messages = {
                400: "❌ Invalid request",
                401: "🔑 Invalid API key",
                429: "⏱️ Rate limit exceeded",
                500: "🔧 Server error",
                503: "⚠️ Service unavailable",
            }
            
            raise Exception(error_messages.get(status, f"HTTP {status}"))
        
        except Exception as e:
            print(f"❌ Error on key #{current_key_num}: {e}")
            key_manager.mark_error(api_key)
            raise Exception(f"⚠️ Error: {str(e)[:100]}")
    
    # If we get here, all retries failed
    raise Exception("❌ Failed after trying all available keys")