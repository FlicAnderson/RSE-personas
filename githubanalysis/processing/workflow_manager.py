"""Create todo file from github urls for processing."""

from pathlib import Path
import json
from typing import Any


class WorkflowManager:
    filepath: Path

    def __init__(self) -> None:
        repo_root = Path(__file__).parent.parent
        self.filepath = repo_root / "workflow_management_info.json"
        if not self.filepath.exists():
            with open(self.filepath, mode="w") as filehandle:
                json.dump({}, filehandle)

    def set(self, key: str, value: Any):
        with open(self.filepath, mode="r") as filehandle:
            file_contents = json.load(filehandle)

        assert isinstance(
            file_contents, dict
        ), "This really ought to be a dict, we just created it."

        file_contents[key] = value

        with open(self.filepath, mode="w") as filehandle:
            json.dump(file_contents, filehandle)

    def get(self, key: str, default: Any = None):
        with open(self.filepath, mode="r") as filehandle:
            file_contents = json.load(filehandle)

        assert isinstance(
            file_contents, dict
        ), "This really ought to be a dict, we just created it."

        return file_contents.get(key, default)
