import os
from config import DB_FILE

class GUIDTracker:
    def __init__(self):
        self.seen_guids = self._load()

    def _load(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def is_new(self, guid):
        return guid not in self.seen_guids

    def add(self, guid):
        self.seen_guids.add(guid)
        parent = os.path.dirname(DB_FILE)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(DB_FILE, "a") as f:
            f.write(f"{guid}\n")
