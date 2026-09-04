import os
import json
from datetime import datetime

class StateManager:

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._state = self._load()

    def _load(self) -> dict:

        if not os.path.exists(self.file_path):
            default_state = {"lastModifiedDate": "Never", "actualHash": "N/A"}
            self._state = default_state
            self._save()
            return default_state
        
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            default_state = {"lastModifiedDate": "Never", "actualHash": "N/A"}
            self._state = default_state
            self._save()
            return default_state

    def get_state(self) -> dict:
        return self._state

    def update_state(self, actual_hash: str):

        self._state["lastModifiedDate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._state["actualHash"] = actual_hash
        self._save()

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)