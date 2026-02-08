
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os
import shutil
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock the GLMOCR class before importing main
# We need to mock it at the module level where it is used
# But main.py imports it.
# Easiest way is to patch it in the test or use a fixture that patches it.

@pytest.fixture(scope="session")
def mock_glm_ocr():
    with patch("glm.GLMOCR") as mock:
        # Setup the mock instance
        instance = mock.return_value
        # Mock process_image_stream to return a generator
        def stream_side_effect(image_path, type="table"):
            yield "<!-- Start -->"
            yield "Detected Content"
            yield "<!-- End -->"
        
        instance.process_image_stream.side_effect = stream_side_effect
        instance.abort_event = MagicMock()
        instance.abort_event.is_set.return_value = False
        yield mock

@pytest.fixture(scope="module")
def client(mock_glm_ocr):
    # We need to import app AFTER the mock is active or patch it where it's imported
    # logic in main.py:
    # app = FastAPI(lifespan=lifespan)
    # global ocr_model
    # ocr_model = GLMOCR() in lifespan
    
    from main import app, lifespan
    
    # We need to manually trigger the lifespan or rely on TestClient to do it (TestClient does call lifespan context)
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def clean_directories():
    # Setup: Ensure dirs exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    yield
    # Teardown: Clean up specific test artifacts if needed
    # For now, we might want to leave them or clean them. 
    # Let's clean up files created during tests to keep it tidy.
    # But be careful not to delete real user data if running locally.
    # Since we are in a dev environment, maybe just cleaning known test files.
