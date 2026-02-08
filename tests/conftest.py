import pytest
from fastapi.testclient import TestClient
import os
import shutil
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture(scope="module")
def client():
    # We import app here to ensure sys.path is set
    from main import app
    
    # TestClient context manager triggers the lifespan events (startup/shutdown)
    # This will load the REAL GLMOCR model.
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def clean_directories():
    # Setup: Ensure dirs exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    yield
    # Teardown: Clean up specific test artifacts if needed