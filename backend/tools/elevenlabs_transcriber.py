import os
import requests
from pathlib import Path


class ElevenLabsTranscriber:
    """
    Handles audio transcription using ElevenLabs API.
    """
    
    def __init__(self, api_key, csv_filename="transcription.csv", output_csv_dir="./datasets_csv"):
        self.api_key = api_key
        self.csv_filename = csv_filename
        self.output_csv_dir = Path(output_csv_dir)
        self.output_csv_dir.mkdir(parents=True, exist_ok=True)
        self.api_url = "https://api.elevenlabs.io/v1/speech-to-text"
    
    def transcribe_audio_folder(self, folder_path, progress_callback=None):
        """
        Transcribe all audio files in the given folder using ElevenLabs API.
        
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
        
        if not audio_files:
            raise ValueError(f"No audio files found in {folder_path}")
        
        total_files = len(audio_files)
        results = []
        
        if progress_callback:
            progress_callback(f"Found {total_files} audio files to transcribe", 0)
        
        # Process each audio file
        for idx, audio_file in enumerate(audio_files):
            try:
                if progress_callback:
                    progress_callback(f"Transcribing {audio_file.name}...", int((idx / total_files) * 100))
                
                # Call ElevenLabs API
                text = self._transcribe_file(audio_file)
                
                results.append({
                    'audio_file': audio_file.name,
                    'text': text
                })
                
            except Exception as e:
                print(f"Error transcribing {audio_file.name}: {e}")
                results.append({
                    'audio_file': audio_file.name,
                    'text': f"[ERROR: {str(e)}]"
                })
        
        # Save to CSV
        output_path = self.output_csv_dir / self.csv_filename
        self._save_to_csv(results, output_path)
        
        if progress_callback:
            progress_callback(f"Transcription complete! Saved to {output_path}", 100)
        
        return str(output_path)
    
    def _transcribe_file(self, audio_file_path):
        """
        Transcribe a single audio file using ElevenLabs API.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Transcribed text
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
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
    
    def _save_to_csv(self, results, output_path):
        """
        Save transcription results to CSV file.
        
        Args:
            results: List of dicts with 'audio_file' and 'text' keys
            output_path: Path to save the CSV file
        """
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['audio_file', 'text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result)
