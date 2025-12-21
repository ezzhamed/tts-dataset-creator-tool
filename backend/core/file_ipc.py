import json
import os
import time
import uuid
import asyncio
from pathlib import Path

class FileIPC:
    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.jobs_dir = self.storage_dir / "jobs"
        self.results_dir = self.storage_dir / "results"
        self.progress_dir = self.storage_dir / "progress"
        
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.progress_dir.mkdir(parents=True, exist_ok=True)

    def create_task(self, task_type: str, payload: dict) -> str:
        task_id = str(uuid.uuid4())
        task_data = {
            "task_id": task_id,
            "type": task_type,
            "payload": payload,
            "created_at": time.time(),
            "status": "pending"
        }
        
        file_path = self.jobs_dir / f"{task_id}.json"
        with open(file_path, "w") as f:
            json.dump(task_data, f, indent=2)
            
        return task_id

    def update_progress(self, task_id: str, message: str, percent: int = None):
        """Updates the progress file for a task with robust retry logic"""
        progress_data = {
            "task_id": task_id,
            "message": message,
            "percent": percent,
            "updated_at": time.time()
        }
        file_path = self.progress_dir / f"{task_id}.json"
        temp_path = file_path.with_suffix(".tmp")
        
        max_retries = 5
        retry_delay = 0.2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Try writing to temp file first
                with open(temp_path, "w") as f:
                    json.dump(progress_data, f)
                
                # Try to replace with retry
                try:
                    os.replace(temp_path, file_path)
                    return  # Success
                except PermissionError:
                    # If replace fails, try direct write
                    try:
                        with open(file_path, "w") as f:
                            json.dump(progress_data, f)
                        return  # Success
                    except PermissionError:
                        pass  # Will retry
                        
            except PermissionError:
                pass  # Will retry
            except Exception as e:
                print(f"Error in update_progress: {e}")
                return
            
            # Wait before retry
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        
        # If all retries failed, just skip this progress update (non-critical)
        # The transcription will continue without updating progress

    def get_progress(self, task_id: str):
        """Reads the progress file for a task"""
        file_path = self.progress_dir / f"{task_id}.json"
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None
        return None

    async def watch_task(self, task_id: str, timeout: int = 300):
        """
        Watches for a result file for the given task_id.
        Returns the result data if found, or raises TimeoutError.
        """
        result_file = self.results_dir / f"{task_id}_result.json"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if result_file.exists():
                # Give a brief moment for write to complete
                await asyncio.sleep(0.1)
                try:
                    with open(result_file, "r") as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    # File might be currently being written
                    pass
            
            await asyncio.sleep(0.5)
            
        raise TimeoutError(f"Timeout waiting for task {task_id}")

    def get_task_status(self, task_id: str):
        # Check if result exists
        result_file = self.results_dir / f"{task_id}_result.json"
        if result_file.exists():
            return "completed"
        
        # Check if job file exists
        job_file = self.jobs_dir / f"{task_id}.json"
        if job_file.exists():
            return "pending" # Or 'processing' if we had a way to mark it
            
        return "unknown"
