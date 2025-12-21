import os
import requests
from pathlib import Path


class ElevenLabsTranscriber:
    """
    Handles audio transcription using ElevenLabs API.
    Saves CSV progressively to preserve results on interruption or credit exhaustion.
    """
    
    def __init__(self, api_key, csv_filename="transcription.csv", output_csv_dir="./datasets_csv"):
        self.api_key = api_key
        self.csv_filename = csv_filename
        self.output_csv_dir = Path(output_csv_dir)
        self.output_csv_dir.mkdir(parents=True, exist_ok=True)
        self.api_url = "https://api.elevenlabs.io/v1/speech-to-text"
        self.results = []  # Store results for progressive saving
    
    def _save_csv(self, results=None):
        """Save the current transcription results to CSV file with retry logic."""
        if results is None:
            results = self.results
        
        if not results:
            return
        
        output_path = self.output_csv_dir / self.csv_filename
        
        # Try to save with retry logic for locked files
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                self._save_to_csv_internal(results, output_path)
                print(f"CSV saved to: {output_path}")
                return
            except PermissionError as e:
                if attempt < max_retries - 1:
                    print(f"File is locked, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    import time
                    time.sleep(retry_delay)
                else:
                    # Save to backup file with timestamp
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_filename = self.csv_filename.replace('.csv', f'_backup_{timestamp}.csv')
                    backup_path = self.output_csv_dir / backup_filename
                    try:
                        self._save_to_csv_internal(results, backup_path)
                        print(f"⚠️ Original file is locked. Saved backup to: {backup_path}")
                    except Exception as backup_error:
                        print(f"❌ Failed to save backup: {backup_error}")
    
    def transcribe_audio_folder(self, folder_path, progress_callback=None):
        """
        Transcribe all audio files in the given folder using ElevenLabs API.
        Saves CSV progressively after each file to preserve partial results.
        
        Args:
            folder_path: Path to folder containing audio files
            progress_callback: Optional callback function(message, percent)
        """
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # Get all audio files
        audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
        audio_files = []
        for ext in audio_extensions:
            audio_files.extend(folder.glob(f'*{ext}'))
        
        # Sort files for consistent ordering
        audio_files = sorted(audio_files, key=lambda x: x.name)
        
        if not audio_files:
            raise ValueError(f"No audio files found in {folder_path}")
        
        total_files = len(audio_files)
        self.results = []  # Reset results for this session
        
        if progress_callback:
            progress_callback(f"Found {total_files} audio files to transcribe", 0)
        
        try:
            # Process each audio file
            for idx, audio_file in enumerate(audio_files):
                try:
                    if progress_callback:
                        progress_callback(f"Transcribing {audio_file.name}...", int((idx / total_files) * 100))
                    
                    # Call ElevenLabs API
                    text = self._transcribe_file(audio_file)
                    
                    self.results.append({
                        'audio_file': audio_file.name,
                        'text': text
                    })
                    
                    # Save CSV after each successful transcription to preserve progress
                    self._save_csv()
                    
                except CreditExhaustedException as e:
                    # Credits exhausted - save progress and notify user
                    print(f"ElevenLabs credits exhausted. Saving partial results ({len(self.results)} files transcribed)...")
                    self._save_csv()
                    if progress_callback:
                        progress_callback(f"Credits exhausted! Saved {len(self.results)} transcriptions.", 
                                         int((len(self.results) / total_files) * 100))
                    raise
                    
                except Exception as e:
                    print(f"Error transcribing {audio_file.name}: {e}")
                    self.results.append({
                        'audio_file': audio_file.name,
                        'text': f"[ERROR: {str(e)}]"
                    })
                    # Save CSV even with error entries to preserve progress
                    self._save_csv()
            
            # Final save and completion message
            output_path = self.output_csv_dir / self.csv_filename
            
            if progress_callback:
                progress_callback(f"Transcription complete! Saved to {output_path}", 100)
            
            return str(output_path)
            
        except KeyboardInterrupt:
            # Handle user interruption (Ctrl+C)
            print(f"Transcription interrupted by user. Saving partial results ({len(self.results)} files transcribed)...")
            self._save_csv()
            raise
        
        except CreditExhaustedException:
            # Re-raise after saving (already handled above)
            raise
        
        except Exception as e:
            # Save progress before re-raising any other exception
            print(f"Error during transcription: {e}. Saving partial results ({len(self.results)} files transcribed)...")
            self._save_csv()
            raise
    
    def _transcribe_file(self, audio_file_path):
        """
        Transcribe a single audio file using ElevenLabs API.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Transcribed text
            
        Raises:
            CreditExhaustedException: When ElevenLabs credits are exhausted
            Exception: For other API errors
        """
        headers = {
            "xi-api-key": self.api_key
        }
        
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'file': (audio_file_path.name, audio_file, 'audio/mpeg')
            }
            
            # model_id is required by ElevenLabs Speech-to-Text API
            data = {
                'model_id': 'scribe_v1'
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('text', '')
        elif response.status_code in [402, 429]:
            # 402 = Payment Required (credits exhausted)
            # 429 = Too Many Requests (rate limit or quota exceeded)
            raise CreditExhaustedException(f"ElevenLabs credits exhausted or rate limited: {response.status_code} - {response.text}")
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
    
    def _save_to_csv_internal(self, results, output_path):
        """
        Save transcription results to CSV file.
        
        Args:
            results: List of dicts with 'audio_file' and 'text' keys
            output_path: Path to save the CSV file
        """
        import csv
        
        # Use utf-8-sig encoding (UTF-8 with BOM) for proper Arabic text display in Excel
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['audio_file', 'text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result)


class CreditExhaustedException(Exception):
    """Exception raised when ElevenLabs API credits are exhausted."""
    pass
