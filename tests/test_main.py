
import os
import json
import pytest

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

@pytest.mark.parametrize("filename, type_param", [
    ("hand_written_table.jpg", "table"),
    ("test_text.PNG", "text")
])
def test_ocr_endpoint(client, filename, type_param):
    file_path = os.path.join("test_images", filename)
    if not os.path.exists(file_path):
        pytest.skip(f"Test image {filename} not found")
        
    with open(file_path, "rb") as f:
        # Determine mime type roughly
        mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
        
        response = client.post(
            "/ocr",
            files={"file": (filename, f, mime)},
            data={"type": type_param}
        )
        
    assert response.status_code == 200
    # The response is a stream, TestClient handles it by reading content
    content = response.content.decode()
    
    # Check that we got some content back
    assert len(content) > 0
    # Ensure no error messages were returned in the stream
    assert "<!-- Error:" not in content
    assert "Processing failed" not in content
    # Also check headers if possible, or just the mocked stream content
    assert response.headers["X-Filename"] == filename


def test_save_and_history_and_delete(client):
    # 1. Save a session
    data = {
        "name": "Test Session",
        "content": "<div>Test Content</div>",
        "id": "test-uuid-1234"
    }
    
    response = client.post("/save", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    assert res_json["id"] == "test-uuid-1234"
    
    # Verify file exists
    expected_path = os.path.join("data", "table_test-uuid-1234.json")
    assert os.path.exists(expected_path)
    
    # 2. Get history
    response = client.get("/history")
    assert response.status_code == 200
    history = response.json()
    # Check if our saved session is in history
    found = False
    for item in history:
        if item["id"] == "test-uuid-1234":
            assert item["name"] == "Test Session"
            found = True
            break
    assert found
    
    # 3. Delete session
    response = client.delete("/session/test-uuid-1234")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify file gone
    assert not os.path.exists(expected_path)
    
    # 4. Verify gone from history
    response = client.get("/history")
    history = response.json()
    found = False
    for item in history:
        if item["id"] == "test-uuid-1234":
            found = True
            break
    assert not found

def test_gpu_status(client):
    # This just mocks the torch calls inside the endpoint or we assume it runs (might return available=False)
    # Since we didn't mock torch in main.py, it will try to run real torch commands.
    # Depending on environment, this might be fine.
    response = client.get("/gpu")
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
    assert "info" in data

def test_cancel_endpoint(client):
    response = client.post("/cancel")
    assert response.status_code == 200
    # Depending on mock state, it might return cancelled or no model.
    # Our mock fixture setup ensures model is loaded via lifespan.
    assert response.json()["status"] == "cancelled"
