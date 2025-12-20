import time
import json
import os
import sys
from pathlib import Path

# Add project root to path to import user scripts
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from backend.core.file_ipc import FileIPC

# Import user scripts
try:
    from backend.processors.youtube_scraper import YouTubeScraper
    from backend.processors.audio_splitter import AudioSplitter
    from backend.processors.audio_transcriber import AudioTranscriber
    from backend.processors.semantic_splitter import SemanticSplitter
except ImportError as e:
    print(f"Error importing user scripts: {e}")
    # Define dummy classes or handle missing imports later
    SemanticSplitter = None

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
ipc = FileIPC(str(STORAGE_DIR))

# Ensure directories exist
(STORAGE_DIR / "datasets_csv").mkdir(parents=True, exist_ok=True)
(STORAGE_DIR / "audios").mkdir(parents=True, exist_ok=True)
(STORAGE_DIR / "audios" / "splitted_audios").mkdir(parents=True, exist_ok=True)
(STORAGE_DIR / "datasets_csv" / "audio_datasets").mkdir(parents=True, exist_ok=True)
(STORAGE_DIR / "datasets_csv" / "audio_text_datasets").mkdir(parents=True, exist_ok=True)


def process_task(task_file):
    with open(task_file, "r") as f:
        task = json.load(f)
    
    task_id = task["task_id"]
    task_type = task["type"]
    payload = task["payload"]
    
    print(f"Processing task: {task_id} ({task_type})")
    
    result = None
    try:
        if task_type == "scrape_youtube":
            # Payload: playlist_url (was channel_url)
            # User might send "channel_url" or "playlist_url"
            url = payload.get("playlist_url") or payload.get("channel_url")
            
            # Voice name is optional now, derive from URL or use default
            # Determine URL type and generate appropriate naming
            if "/watch?v=" in url:
                # Single video URL
                # Extract video ID from URL
                if "v=" in url:
                    video_id = url.split("v=")[-1].split("&")[0]
                    name_prefix = f"video_{video_id}"
                else:
                    name_prefix = "single_video"
            elif "list=" in url:
                # Playlist URL
                identifier = url.split("list=")[-1].split("&")[0]
                name_prefix = f"playlist_{identifier}"
            elif "@" in url:
                # Channel URL
                identifier = url.split("@")[-1].split("/")[0]
                name_prefix = identifier
            else:
                name_prefix = "scraped_data"
                
            voice_name = payload.get("voice_name") or name_prefix
            
            output_dir = str(STORAGE_DIR / "datasets_csv")
            csv_name = f"{name_prefix}_metadata.csv"
            output_audio_dir = str(STORAGE_DIR / "audios")
            
            print(f"Scraping {url}...")
            
            def scraper_progress(message, percent):
                 ipc.update_progress(task_id, message, percent)
                 
            scraper = YouTubeScraper(
                channel_name=name_prefix,
                channel_url=url,
                voice=voice_name,
                output_dir=output_dir,
                csv_name=csv_name,
                output_audio_dir=output_audio_dir,
                progress_callback=scraper_progress
            )
            scraper.collect_data()
            
            result = {
                "status": "success", 
                "csv_path": os.path.join(output_dir, csv_name),
                "csv_filename": csv_name
            }

        elif task_type == "split_audio":
            # Payload: csv_filename OR audio_folder
            csv_filename = payload.get("csv_filename")
            audio_folder = payload.get("audio_folder")
            
            def progress_callback(message, percent):
                ipc.update_progress(task_id, message, percent)
            
            if csv_filename:
                csv_path = str(STORAGE_DIR / "datasets_csv" / csv_filename)
                
                # Use defaults or derive from payload
                audio_name = "audio" # Could be parameterized
                channel_name = csv_filename.replace("_metadata.csv", "")
                output_csv_name = f"{channel_name}_splitted.csv"
                
                # extracting params from payload if they exist
                silence_len = payload.get("silence_len", 300)
                max_audio_len = payload.get("max_audio_len", 25000)
                
                print(f"Splitting audio from CSV {csv_filename} with silence_len={silence_len}, max_len={max_audio_len}...")
                
                splitter = AudioSplitter(
                    csv_path=csv_path,
                    audio_name=audio_name,
                    channel_name=channel_name,
                    output_csv_name=output_csv_name,
                    output_splitted_audio_dir=str(STORAGE_DIR / "audios" / "splitted_audios"),
                    output_audio_dir=str(STORAGE_DIR / "audios"),
                    output_csv_dir=str(STORAGE_DIR / "datasets_csv" / "audio_datasets"),
                    progress_callback=progress_callback,
                    silence_len=int(silence_len),
                    max_audio_len=int(max_audio_len)
                )
            elif audio_folder:
                # Handle direct folder input
                target_folder = Path(audio_folder)
                if not target_folder.is_absolute():
                    # If not absolute, assume relative to STORAGE_DIR
                    target_folder = STORAGE_DIR / audio_folder
                
                print(f"Splitting audio from folder {target_folder}...")
                
                # extracting params from payload if they exist
                silence_len = payload.get("silence_len", 300)
                max_audio_len = payload.get("max_audio_len", 25000)
                
                if not target_folder.exists():
                     raise FileNotFoundError(f"Audio folder not found: {target_folder}")

                splitter = AudioSplitter(
                    input_audio_folder=str(target_folder),
                    output_splitted_audio_dir=str(STORAGE_DIR / "audios" / "splitted_audios"),
                    output_csv_dir=str(STORAGE_DIR / "datasets_csv" / "audio_datasets"),
                    progress_callback=progress_callback,
                    silence_len=int(silence_len),
                    max_audio_len=int(max_audio_len)
                )
            else:
                raise ValueError("Either csv_filename or audio_folder must be provided")



            splitter_method = payload.get("splitting_method", "vad") # vad or semantic

            if splitter_method == "semantic":
                print(f"Using Semantic Splitter (Faster-Whisper)...")
                if not audio_folder:
                     # If user provided CSV, we still need folder. 
                     # Current semantic splitter only supports folder input for simplicity or needs adaptation.
                     # Let's support folder path derivation from CSV if needed, but UI sends folder.
                     # Assuming UI sends audio_folder for semantic mode as per plan.
                     pass

                # If we are in CSV mode but want semantic, we might need to derive folder.
                # simpler: Semantic Mode strictly requires audio_folder for now.
                
                target_folder_semantic = None
                if audio_folder:
                    target_folder_semantic = str(target_folder)
                elif csv_filename:
                     # Attempt to derive
                     if hasattr(splitter, 'output_audio_dir'):
                          target_folder_semantic = splitter.output_audio_dir
                
                if not target_folder_semantic:
                     raise ValueError("Semantic Splitting requires an audio folder input.")

                if SemanticSplitter is None:
                    raise ImportError("SemanticSplitter is not available. Please install 'faster-whisper' and 'torchaudio'.")

                semantic_splitter = SemanticSplitter(
                    input_audio_folder=target_folder_semantic,
                    output_splitted_audio_dir=str(STORAGE_DIR / "audios" / "splitted_audios"),
                    output_csv_dir=str(STORAGE_DIR / "datasets_csv" / "audio_datasets"),
                    progress_callback=progress_callback
                )
                res = semantic_splitter.split_audio()
                
                result = {
                    "status": "success",
                    "output_csv": res["csv_filename"],
                    "audio_dir": res["audio_dir"]
                }
            else:
                # VAD Mode (Existing)
                splitter.process_videos()
                
                result = {
                    "status": "success",
                    "output_csv": splitter.output_csv_name if hasattr(splitter, 'output_csv_name') else "output.csv",
                    "audio_dir": str(STORAGE_DIR / "audios" / "splitted_audios")
                }

        elif task_type == "transcribe_audio":
            # Payload: output_csv_name, method ('local' or 'elevenlabs'), api_key (if elevenlabs)
            
            # Determine target folder
            audio_folder = payload.get("audio_folder")
            if audio_folder:
                target_folder = Path(audio_folder)
                if not target_folder.is_absolute():
                     target_folder = STORAGE_DIR / audio_folder
                target_folder = str(target_folder)
            else:
                target_folder = str(STORAGE_DIR / "audios" / "splitted_audios")

            output_csv_name = payload.get("output_csv_name", "transcription.csv")
            method = payload.get("method", "local")
            
            print(f"Transcribing audio in {target_folder} using {method} method...")
            
            # Define progress callback
            def progress_callback(message, percent):
                ipc.update_progress(task_id, message, percent)
            
            if method == "elevenlabs":
                # Use ElevenLabs API
                api_key = payload.get("api_key")
                if not api_key:
                    raise ValueError("API key is required for ElevenLabs transcription")
                
                from backend.tools.elevenlabs_transcriber import ElevenLabsTranscriber
                transcriber = ElevenLabsTranscriber(
                    api_key=api_key,
                    csv_filename=output_csv_name,
                    output_csv_dir=str(STORAGE_DIR / "datasets_csv" / "audio_text_datasets")
                )
                transcriber.transcribe_audio_folder(target_folder, progress_callback=progress_callback)
            else:
                # Use local STT model
                transcriber = AudioTranscriber(
                    csv_filename=output_csv_name,
                    output_csv_dir=str(STORAGE_DIR / "datasets_csv" / "audio_text_datasets")
                )
                transcriber.transcribe_audio_folder(target_folder, progress_callback=progress_callback)
            
            result = {
                "status": "success",
                "output_csv": output_csv_name,
                "method": method
            }

        # Write Result
        result_file = ipc.results_dir / f"{task_id}_result.json"
        with open(result_file, "w") as f:
            json.dump(result, f)
            
        print(f"Task {task_id} completed.")
        
        # Remove job file
        os.remove(task_file)

    except Exception as e:
        print(f"Error processing task {task_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Write error result
        result_file = ipc.results_dir / f"{task_id}_result.json"
        with open(result_file, "w") as f:
            json.dump({"status": "error", "message": str(e)}, f)
        os.remove(task_file)

def main():
    # Clear any existing jobs on startup
    print("Cleaning up previous jobs...")
    for job_file in ipc.jobs_dir.glob("*.json"):
        try:
            os.remove(job_file)
            print(f"Removed stale job: {job_file.name}")
        except Exception as e:
            print(f"Failed to remove stale job {job_file.name}: {e}")

    print("TTS Worker started. Waiting for jobs...")
    while True:
        # List all json files in jobs dir
        job_files = list(ipc.jobs_dir.glob("*.json"))
        if job_files:
            # Pick the first one
            process_task(job_files[0])
        else:
            time.sleep(1)

if __name__ == "__main__":
    main()
