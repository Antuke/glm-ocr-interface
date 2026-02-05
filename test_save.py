import requests
import json

BASE_URL = "http://localhost:4444"

def test_save_flow():
    # 1. First Save (New Session)
    print("Step 1: Creating new session...")
    resp = requests.post(f"{BASE_URL}/save", json={
        "name": "Test Session",
        "content": "<div>Table 1</div>",
        "id": None
    })
    
    if resp.status_code != 200:
        print("Failed to save:", resp.text)
        return
        
    data1 = resp.json()
    session_id = data1.get("id")
    print(f"Created Session ID: {session_id}")
    
    if not session_id:
        print("Error: No ID returned")
        return

    # 2. Second Save (Update Session)
    print("Step 2: Updating session...")
    resp = requests.post(f"{BASE_URL}/save", json={
        "name": "Test Session",
        "content": "<div>Table 1</div>",
        "id": session_id
    })
    
    data2 = resp.json()
    session_id_2 = data2.get("id")
    print(f"Updated Session ID: {session_id_2}")
    
    if session_id != session_id_2:
        print("FAILURE: Session ID changed! New session spawned.")
    else:
        print("SUCCESS: Session ID preserved.")

    # Check history
    resp = requests.get(f"{BASE_URL}/history")
    history = resp.json()
    print(f"History count: {len(history)}")
    for h in history:
        print(f" - {h['name']} ({h['id']})")

if __name__ == "__main__":
    try:
        test_save_flow()
    except Exception as e:
        print(f"Error: {e}")
