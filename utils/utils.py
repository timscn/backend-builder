from pathlib import Path
from datetime import datetime
from typing import List

# Centralized Constants
VALID_FEATURES: List[str] = ["map", "chat", "settings", "profile"]
VALID_ACTIONS: List[str] = ["start", "end"]

def resolve_path(path_str: str, base_file: str) -> Path:
    """
    Resolves a path relative to the repository root.
    Args:
        path_str: The relative or absolute path to resolve.
        base_file: The __file__ path of the calling script to determine repo root.
    """
    script_dir = Path(base_file).parent
    # Assuming structure is repo_root/partX_folder/script.py
    repo_root = script_dir.parent
    full_path = repo_root / path_str if not Path(path_str).is_absolute() else Path(path_str)
    return full_path

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO format timestamp string to datetime object, handling 'Z'."""
    return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))