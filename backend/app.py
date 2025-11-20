import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
from pathlib import Path
from backend.core.file_ipc import FileIPC

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://localhost:5173", "http://localhost:5174", "https://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize IPC
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
ipc = FileIPC(str(STORAGE_DIR))

# Mount Storage
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

# --- Endpoints ---

@app.get("/files/csvs")
async def list_csvs():
    """List available CSVs in storage/datasets_csv"""
    csv_dir = STORAGE_DIR / "datasets_csv"
    if not csv_dir.exists():
        return []
    return [f.name for f in csv_dir.glob("*.csv")]

@app.post("/tasks/scrape")
async def start_scrape(payload: dict):
    """Start a scraping task"""
    # payload: { "channel_url": str, "voice_name": str }
    task_id = ipc.create_task("scrape_youtube", payload)
    return {"task_id": task_id}

@app.post("/tasks/split")
async def start_split(payload: dict):
    """Start a splitting task"""
    # payload: { "csv_filename": str }
    task_id = ipc.create_task("split_audio", payload)
    return {"task_id": task_id}

@app.post("/tasks/transcribe")
async def start_transcribe(payload: dict):
    """Start a transcription task"""
    # payload: { "output_csv_name": str }
    task_id = ipc.create_task("transcribe_audio", payload)
    return {"task_id": task_id}

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            try:
                result_file = ipc.results_dir / f"{task_id}_result.json"
                
                if result_file.exists():
                    with open(result_file, "r") as f:
                        result = json.load(f)
                    await websocket.send_json({"status": "completed", "result": result})
                    break
                else:
                    # Check if job still exists
                    job_file = ipc.jobs_dir / f"{task_id}.json"
                    if not job_file.exists() and not result_file.exists():
                         # Job gone but no result? Maybe picked up but not finished?
                         # Or maybe failed and deleted?
                         # For now, assume processing if not found in result
                         pass

                    # Check for progress
                    progress = ipc.get_progress(task_id)
                    print(f"Checking progress for {task_id} in {ipc.progress_dir}: {progress}")
                    if progress:
                        await websocket.send_json({"status": "processing", "detail": progress})
                    else:
                        await websocket.send_json({"status": "processing"})
                
                import asyncio
                await asyncio.sleep(1)
            except Exception as e:
                await websocket.send_json({"status": "error", "message": str(e)})
                break
                
    except WebSocketDisconnect:
        print(f"Client disconnected for task {task_id}")

if __name__ == "__main__":
    # SSL Configuration
    # Certificates are in the project root
    ssl_keyfile = BASE_DIR / "key.pem"
    ssl_certfile = BASE_DIR / "cert.pem"
    
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile=str(ssl_keyfile),
        ssl_certfile=str(ssl_certfile),
        reload=True
    )
