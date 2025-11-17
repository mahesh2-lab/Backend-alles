import os
from dotenv import load_dotenv
from collections import deque
from datetime import datetime, timedelta

load_dotenv()

class KeyManager:
    def __init__(self):
        keys = os.getenv("LLM_KEYS", "").split(",")
        self.keys = deque(keys)
        self.failed_keys = {}  # key -> next_retry_time

    def get_active_key(self):
        # Rotate until a valid key is found
        for _ in range(len(self.keys)):
            key = self.keys[0]
            if not self.is_key_failed(key):
                return key
            self.keys.rotate(-1)
        raise RuntimeError("🚨 No active API keys available.")

    def mark_key_as_failed(self, key, cooldown_minutes=5):
        self.failed_keys[key] = datetime.now() + timedelta(minutes=cooldown_minutes)
        print(f"⚠️ Key {key[:8]}... failed. Will retry after {cooldown_minutes} min.")
        self.keys.rotate(-1)

    def is_key_failed(self, key):
        if key not in self.failed_keys:
            return False
        if datetime.now() > self.failed_keys[key]:
            del self.failed_keys[key]  # retry after cooldown
            return False
        return True
