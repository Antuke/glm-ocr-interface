# glm-ocr-interface

A lightweight web application built with FastAPI that leverages the [GLM-OCR](https://huggingface.co/zai-org/GLM-OCR) model to perform Optical Character Recognition (OCR), specifically optimized for extracting and reconstructing tables from images.

## Features

- **Image Upload:** Upload images directly through a web interface.
- **Table Extraction:** Uses the powerful `zai-org/GLM-OCR` model to recognize and format tables found within images.
- **Save Results:** Store extraction results locally as JSON files.
- **History Viewer:** Browse previously saved extraction tasks.
- **REST API:** Endpoints available for programmatic access (`/ocr`, `/save`, `/history`).

## Prerequisites

- **Python 3.8+**
- **GPU (Recommended):** The application defaults to using `cuda` (NVIDIA GPU) for inference. Running on CPU may be significantly slower or require code modification.
- **Hugging Face Access:** The model will be downloaded automatically from Hugging Face on the first run.

## Installation

1.  **Clone the repository** (if applicable) or navigate to the project directory:
    ```bash
    cd /path/to/glm
    ```

2.  **Install Dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

    *Note: If you have specific CUDA requirements for PyTorch, install it manually according to [pytorch.org](https://pytorch.org/) before running the requirements file.*

## Usage

1.  **Start the Server:**
    Run the application using Uvicorn:
    ```bash
    uvicorn main:app --reload
    ```

2.  **Access the Interface:**
    Open your web browser and navigate to:
    ```
    http://127.0.0.1:8000
    ```

3.  **Upload & Process:**
    - Click to select or drag & drop an image containing a table.
    - The system will process the image (this may take a moment depending on your GPU).
    - View the rendered HTML result.
    - Save the result for later reference.

## Project Structure

- `main.py`: The FastAPI application server and API endpoints.
- `glm.py`: Wrapper class for the GLM-OCR model inference logic.
- `templates/index.html`: The frontend user interface.
- `static/`: Static assets (JS/CSS).
- `uploads/`: Directory where uploaded images are temporarily stored.
- `data/`: Directory where saved OCR results are stored as JSON.
- `requirements.txt`: Python dependencies.

## API Endpoints

- `GET /`: Renders the main UI.
- `POST /ocr`: Accepts an image file (`multipart/form-data`), returns the extracted HTML content.
- `POST /save`: Accepts JSON data (`{content: "...", name: "..."}`) to save the result.
- `GET /history`: Returns a list of previously saved results.

## Troubleshooting

- **Out of Memory (OOM):** If you encounter CUDA out-of-memory errors, ensure no other heavy processes are using the GPU. You may need a GPU with more VRAM for large images or this specific model.
- **Model Loading:** The first startup will take time as the model weights are downloaded. Ensure you have a stable internet connection.
