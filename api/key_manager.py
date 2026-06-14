"""
API Key Manager - Round Robin with Rate Limit Handling
"""

import threading
import time
from typing import Optional
from config import (
    GROQ_API_KEYS,
    KEY_ROTATION_STRATEGY,
    MAX_KEY_RETRIES,
    RATE_LIMIT_COOLDOWN
)


class KeyManager:
    """Manages multiple API keys with round-robin rotation"""
    
    def __init__(self):
        self.keys = GROQ_API_KEYS.copy()
        self.current_index = 0
        self.lock = threading.Lock()
        
        # Track rate-limited keys: {key: cooldown_until_timestamp}
        self.rate_limited_keys = {}
        
        # Stats
        self.key_usage_count = {key: 0 for key in self.keys}
        self.key_error_count = {key: 0 for key in self.keys}
        
        print(f"🔑 KeyManager initialized with {len(self.keys)} key(s)")
        print(f"   Strategy: {KEY_ROTATION_STRATEGY}")
    
    def get_next_key(self) -> Optional[str]:
        """Get next available API key"""
        with self.lock:
            # Clean up expired cooldowns
            current_time = time.time()
            expired_keys = [k for k, exp_time in self.rate_limited_keys.items() 
                          if current_time >= exp_time]
            for key in expired_keys:
                del self.rate_limited_keys[key]
                print(f"✅ Key #{self._get_key_index(key)+1} cooldown expired")
            
            # Find available key
            attempts = 0
            while attempts < len(self.keys):
                key = self.keys[self.current_index]
                
                # Check if key is rate-limited
                if key not in self.rate_limited_keys:
                    # Key is available
                    self.key_usage_count[key] += 1
                    
                    # Rotate index for next call (if round_robin strategy)
                    if KEY_ROTATION_STRATEGY == 'round_robin':
                        self.current_index = (self.current_index + 1) % len(self.keys)
                    
                    key_num = self._get_key_index(key) + 1
                    return key
                
                # Try next key
                self.current_index = (self.current_index + 1) % len(self.keys)
                attempts += 1
            
            # All keys are rate-limited
            print("❌ All API keys are rate-limited!")
            return None
    
    def mark_rate_limited(self, key: str):
        """Mark a key as rate-limited"""
        with self.lock:
            cooldown_until = time.time() + RATE_LIMIT_COOLDOWN
            self.rate_limited_keys[key] = cooldown_until
            self.key_error_count[key] += 1
            
            key_num = self._get_key_index(key) + 1
            print(f"⏱️  Key #{key_num} rate-limited (cooldown: {RATE_LIMIT_COOLDOWN}s)")
            
            # If on_error strategy, rotate to next key
            if KEY_ROTATION_STRATEGY == 'on_error':
                self.current_index = (self.current_index + 1) % len(self.keys)
    
    def mark_error(self, key: str):
        """Mark a key as having an error (non-rate-limit)"""
        with self.lock:
            self.key_error_count[key] += 1
    
    def _get_key_index(self, key: str) -> int:
        """Get index of a key"""
        try:
            return self.keys.index(key)
        except ValueError:
            return -1
    
    def get_stats(self) -> dict:
        """Get usage statistics"""
        with self.lock:
            available_keys = [k for k in self.keys if k not in self.rate_limited_keys]
            
            return {
                'total_keys': len(self.keys),
                'available_keys': len(available_keys),
                'rate_limited_keys': len(self.rate_limited_keys),
                'current_key_index': self.current_index + 1,
                'strategy': KEY_ROTATION_STRATEGY,
                'key_stats': [
                    {
                        'key_number': i + 1,
                        'key_preview': key[:8] + '...' + key[-4:] if len(key) > 12 else key,
                        'usage_count': self.key_usage_count[key],
                        'error_count': self.key_error_count[key],
                        'rate_limited': key in self.rate_limited_keys,
                        'cooldown_remaining': max(0, int(self.rate_limited_keys.get(key, 0) - time.time()))
                    }
                    for i, key in enumerate(self.keys)
                ]
            }


# Global instance
key_manager = KeyManager()