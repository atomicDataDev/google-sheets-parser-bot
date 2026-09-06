"""
State persistence module.

Manages the bot's persistent state (last known spreadsheet modification
timestamp) stored as a JSON file on disk.
"""
import json
import os


class StateManager:
    """
    Handles loading, updating, and saving bot state to a JSON file.

    :param file_path: Path to the JSON file used for state persistence.
    :type file_path: str
    """

    _DEFAULT_STATE: dict = {"modifiedTime": "Never"}

    def __init__(self, file_path: str) -> None:
        """
        Initialize the StateManager and load existing state from disk.

        :param file_path: Path to the JSON state file.
        :type file_path: str
        """
        self.file_path = file_path
        self._state = self._load()

    def _load(self) -> dict:
        """
        Load state from the JSON file.

        Creates the file with a default state if it does not exist.
        Falls back to the default state on any read or parse error.

        :return: The loaded state dictionary.
        :rtype: dict
        """
        if not os.path.exists(self.file_path):
            self._state = dict(self._DEFAULT_STATE)
            self._save()
            return self._state

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return dict(self._DEFAULT_STATE)

    def get_state(self) -> dict:
        """
        Return the current in-memory state.

        :return: A dictionary containing the current state.
        :rtype: dict
        """
        return self._state

    def update_state(self, modified_time: str) -> None:
        """
        Update the ``modifiedTime`` field and persist the state to disk.

        :param modified_time: ISO 8601 timestamp string from the Google Drive API.
        :type modified_time: str
        """
        self._state["modifiedTime"] = modified_time
        self._save()

    def _save(self) -> None:
        """
        Persist the current in-memory state to the JSON file.
        """
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)
