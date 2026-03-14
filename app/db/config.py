"""Database path from environment. Default: ./data/renfe_tracker.db"""
import os

def get_sqlite_path() -> str:
    if path := os.environ.get("SQLITE_PATH"):
        return path
    data_dir = os.environ.get("DATA_DIR", "data")
    return os.path.join(data_dir, "renfe_tracker.db")

def ensure_data_dir(path: str) -> None:
    """Create parent directory for the DB file if it does not exist."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
