# glm-ocr-interface

A comprehensive web interface built with FastAPI that leverages the [GLM-OCR](https://huggingface.co/zai-org/GLM-OCR) model to perform advanced Optical Character Recognition (OCR). It is optimized for both extracting structured tables and transcribing text from images.

## ✨ Features

- **Dual Extraction Modes:**
  - **Table Recognition:** Optimized for extracting and reconstructing complex tables into HTML/CSV.
  - **Text Extraction:** Uses a text-focused prompt to transcribe documents into editable text.
- **Image Editor:** Built-in tool to **crop** and **rotate** images before processing to improve accuracy.
- **Batch Processing:** Upload multiple images at once; they are queued and processed sequentially.
- **Process Control:** Ability to **stop/cancel** the inference process at any time, immediately freeing up GPU resources.
- **System Monitoring:** Real-time **GPU Status** dashboard to check VRAM usage and availability.
- **Dark Mode:** Fully supported dark theme that persists across sessions.
- **Export Options:**
  - Export tables to **CSV**.
  - Export text to **TXT**.
  - Save sessions internally (JSON) to resume work later.
- **No Internet Required:** All frontend dependencies (Bootstrap, Cropper.js, Icons) are bundled locally for complete offline operation.

## 🛠️ Prerequisites

- **Python 3.8+**
- **NVIDIA GPU (Highly Recommended):** The application relies on `torch.cuda` for efficient inference. 
- **CUDA Toolkit:** Ensure you have the appropriate CUDA toolkit installed for your GPU.

## 🚀 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Antuke/glm-ocr-interface
    cd glm-ocr-interface
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes `fastapi`, `uvicorn`, `torch`, `transformers`, `accelerate`, and `nvidia-ml-py`.*

## 🖥️ Usage

1.  **Start the Server:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```
    *Note: The first time you run the application, it will automatically download the GLM-OCR model (~2.5GBs) from Hugging Face. *

2.  **Access the Interface:**
    Open your web browser and navigate to:
    ```
    http://localhost:8000
    ```


3.  **Workflow:**
    - Click **New Session** and choose your mode (Table or Text).
    - **Drag & Drop** images or click to upload.
    - Use the **Image Editor** to crop the region of interest.
    - Click **Process & Upload**.
    - Once finished, edit the results directly in the browser or export them.

## 📂 Project Structure

- `main.py`: FastAPI backend handling API endpoints and concurrency.
- `glm.py`: Model wrapper handling GLM-OCR inference and cancellation logic.
- `templates/index.html`: Main frontend interface (Bootstrap + Jinja2).
- `static/`:
  - `script.js`: Frontend logic (Queue, Editor, API calls, UI state).
- `uploads/`: Temporary storage for processed images.
- `data/`: JSON storage for saved sessions.

## 🔌 API Endpoints

- `GET /`: Serves the web interface.
- `POST /ocr`: Processing endpoint. Accepts `file` and `type` (table/text).
- `POST /cancel`: Signals the backend to abort the current inference task.
- `GET /gpu`: Returns current GPU memory usage and status.
- `POST /save` & `GET /history`: Session management endpoints.

## ⚠️ Troubleshooting

- **No CUDA GPU available:** The "GPU Status" modal will verify if PyTorch can see your GPU. If not, check your PyTorch installation command matches your CUDA version.
- **OOM (Out of Memory):** Large images or high batch sizes might fill VRAM. Use the **Stop Processing** button if the system hangs, or try cropping smaller regions.
