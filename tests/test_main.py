import os
import json
import pytest
import shutil

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
    
    # Check headers
    assert response.headers["X-Filename"] == filename
    assert "X-Session-ID" in response.headers
    
    # Verify session directory creation
    session_id = response.headers["X-Session-ID"]
    session_dir = os.path.join("uploads", session_id)
    assert os.path.exists(session_dir)
    assert os.path.isdir(session_dir)
    
    # Verify file is inside
    files_in_session = os.listdir(session_dir)
    assert len(files_in_session) == 1
    
    # Clean up
    shutil.rmtree(session_dir)


def test_save_and_history_and_delete(client):
    # 1. Simulate Upload to get a Session ID and create a folder/file
    filename = "hand_written_table.jpg"
    file_path = os.path.join("test_images", filename)
    
    # Skip if test image missing (though it should be there)
    if not os.path.exists(file_path):
        pytest.skip(f"Test image {filename} not found")

    with open(file_path, "rb") as f:
        response = client.post(
            "/ocr",
            files={"file": (filename, f, "image/jpeg")},
            data={"type": "table"}
        )
    
    assert response.status_code == 200
    session_id = response.headers["X-Session-ID"]
    
    # Verify upload dir exists
    upload_dir = os.path.join("uploads", session_id)
    assert os.path.exists(upload_dir)
    
    # 2. Save the session
    data = {
        "name": "Test Session with Image",
        "content": "<div>Test Content</div>",
        "id": session_id
    }
    
    response = client.post("/save", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    assert res_json["id"] == session_id
    
    # Verify JSON file exists
    json_path = os.path.join("data", f"table_{session_id}.json")
    assert os.path.exists(json_path)
    
    # 3. Get history
    response = client.get("/history")
    assert response.status_code == 200
    history = response.json()
    found = False
    for item in history:
        if item["id"] == session_id:
            assert item["name"] == "Test Session with Image"
            found = True
            break
    assert found
    
    # 4. Delete session
    response = client.delete(f"/session/{session_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # 5. Verify Cleanup
    # JSON should be gone
    assert not os.path.exists(json_path)
    # Upload directory should be gone
    assert not os.path.exists(upload_dir)
    
    # 6. Verify gone from history
    response = client.get("/history")
    history = response.json()
    found = False
    for item in history:
        if item["id"] == session_id:
            found = True
            break
    assert not found

def test_gpu_status(client):
    response = client.get("/gpu")
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
    assert "info" in data

def test_cancel_endpoint(client):
    response = client.post("/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"