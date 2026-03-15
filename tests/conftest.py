"""
Pytest fixtures for Renfe Tracker. Uses a temporary DB so tests don't touch real data.
"""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Use a temp dir for DB before app is imported (so get_sqlite_path() sees it).
_test_data = tempfile.mkdtemp(prefix="renfe_tracker_test_")
os.environ["DATA_DIR"] = _test_data

from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient; app runs startup so DB is created."""
    with TestClient(app) as c:
        yield c
