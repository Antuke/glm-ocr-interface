from fastapi import FastAPI
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.concurrency import run_in_threadpool
import shutil
import os
import uuid
from datetime import datetime
from glm import GLMOCR
from contextlib import asynccontextmanager


# Global model instance
ocr_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ocr_model
    try:
        ocr_model = GLMOCR()
        print("GLM-OCR Model loaded successfully.")
    except Exception as e:
        print(f"Failed to load model: {e}")
    yield 
    print('=== Closing ===')


app = FastAPI(lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Templates
templates = Jinja2Templates(directory="templates")

# Directories
UPLOAD_DIR = "uploads"
DATA_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)






@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/ocr")
async def process_image(file: UploadFile = File(...), type: str = Form("table"), session_id: str = Form(None)):
    if not ocr_model:
        raise HTTPException(status_code=503, detail="Model not loaded. Check server logs.")
    
    # Determine session ID
    if not session_id or session_id == "null":
        final_session_id = str(uuid.uuid4())
    else:
        final_session_id = session_id

    # Create session directory
    session_dir = os.path.join(UPLOAD_DIR, final_session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Save uploaded file
    file_id = str(uuid.uuid4())
    extension = file.filename.split(".")[-1]
    # Use absolute path for robustness in WSL
    file_path = os.path.abspath(os.path.join(session_dir, f"{file_id}.{extension}"))
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print(f"Processing image (Stream): {file_path} with mode: {type}")
        
        async def response_generator():
            # Run the blocking iterator in a threadpool to keep the event loop free
            def sync_gen():
                for chunk in ocr_model.process_image_stream(file_path, type=type):
                    yield chunk

            # Helper to safely get next item without raising StopIteration across async boundary
            def safe_next(iterator):
                try:
                    return next(iterator)
                except StopIteration:
                    return None

            import asyncio
            gen = sync_gen()
            
            while True:
                try:
                    # Get next chunk in a threadpool
                    chunk = await run_in_threadpool(safe_next, gen)
                    
                    if chunk is None:
                        break
                        
                    if chunk == "<!-- Process Aborted -->":
                        yield chunk
                        break
                    yield chunk
                except Exception as e:
                    print(f"Streaming error: {e}")
                    yield f"<!-- Error: {str(e)} -->"
                    break

        return StreamingResponse(
            response_generator(), 
            media_type="text/plain",  
            headers={
                "X-File-ID": file_id,
                "X-Session-ID": final_session_id,
                "X-Filename": file.filename,
                "X-OCR-Type": type
            }
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Return the actual error message to the client
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/cancel")
async def cancel_processing():
    if ocr_model:
        ocr_model.abort_event.set()
        return {"status": "cancelled"}
    return {"status": "no model"}

@app.get("/gpu")
async def get_gpu_status():
    import torch
    status = {
        "available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
        "info": []
    }
    
    if status["available"]:
        for i in range(status["device_count"]):
            props = torch.cuda.get_device_properties(i)
            # Memory in MB
            total_mem = props.total_memory / 1024**2
            reserved_mem = torch.cuda.memory_reserved(i) / 1024**2
            allocated_mem = torch.cuda.memory_allocated(i) / 1024**2
            free_mem = total_mem - reserved_mem # Approximation of free memory in terms of reservation
            
            status["info"].append({
                "name": props.name,
                "total_memory": f"{total_mem:.0f} MB",
                "reserved_memory": f"{reserved_mem:.0f} MB",
                "allocated_memory": f"{allocated_mem:.0f} MB",
                "utilization": f"{(reserved_mem/total_mem)*100:.1f}%"
            })
    return status

@app.post("/save")
async def save_table(data: dict):
    # Data expected: { "content": "html/json...", "name": "optional name", "id": "optional id" }
    
    save_id = data.get("id")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # If ID provided, look for existing file
    existing_file = None
    if save_id:
        # Security check: ensure ID is just a UUID/filename and not a path traversal
        safe_id = os.path.basename(save_id)
        possible_path = os.path.join(DATA_DIR, f"table_{safe_id}.json")
        if os.path.exists(possible_path):
            existing_file = possible_path
            filename = f"table_{safe_id}.json"
        else:
            # If ID provided but not found, treat as new or keep ID? 
            # Let's keep the ID to maintain session continuity if frontend thinks it exists.
            filename = f"table_{safe_id}.json"
    else:
        save_id = str(uuid.uuid4())
        filename = f"table_{save_id}.json"
        
    filepath = os.path.join(DATA_DIR, filename)
    
    save_data = {
        "id": save_id,
        "timestamp": timestamp,
        "name": data.get("name", "Untitled"),
        "content": data.get("content")
    }
    
    import json
    with open(filepath, "w") as f:
        json.dump(save_data, f, indent=2)
        
    return {"status": "success", "id": save_id}

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    safe_id = os.path.basename(session_id)
    filename = f"table_{safe_id}.json"
    filepath = os.path.join(DATA_DIR, filename)
    
    # Delete JSON data
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Delete uploads directory for this session
    session_upload_dir = os.path.join(UPLOAD_DIR, safe_id)
    if os.path.exists(session_upload_dir):
        try:
            shutil.rmtree(session_upload_dir)
        except Exception as e:
            print(f"Error deleting session directory {session_upload_dir}: {e}")
            # We continue even if this fails, but ideally we should log it
            pass
            
    return {"status": "success", "message": "Session deleted"}

@app.get("/history")
async def get_history():
    files = []
    if os.path.exists(DATA_DIR):
        import json
        for f in os.listdir(DATA_DIR):
            if f.endswith(".json"):
                with open(os.path.join(DATA_DIR, f), "r") as json_file:
                    try:
                        data = json.load(json_file)
                        files.append(data)
                    except:
                        pass
    # Sort by timestamp desc
    files.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return files

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4444)