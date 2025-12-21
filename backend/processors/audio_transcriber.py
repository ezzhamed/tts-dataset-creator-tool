import os
import pandas as pd
from transformers import pipeline, SeamlessM4TTokenizer
import torch
import time
import warnings

# Suppress tokenizer conversion warnings
warnings.filterwarnings("ignore", message=".*Converting from SentencePiece.*")

# Check if MPS is available and set device accordingly
if torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")  # Fallback to CPU if MPS is not available

class AudioTranscriber:
    
    
    def __init__(self, csv_filename, model_name="facebook/seamless-m4t-v2-large", target_lang="arb", output_csv_dir='./datasets_csv/audio_text_datasets'):
        # Use the specific tokenizer for SeamlessM4T to avoid conversion errors
        tokenizer = SeamlessM4TTokenizer.from_pretrained(model_name)
        
        self.transcription_pipeline = pipeline(
            "automatic-speech-recognition", 
            model=model_name,
            tokenizer=tokenizer,
            device=0
        )
        self.csv_filename = csv_filename
        self.target_lang = target_lang
        self.output_csv_dir = output_csv_dir
        
        # Ensure output directory exists
        os.makedirs(self.output_csv_dir, exist_ok=True)

    def transcribe_audio(self, audio_path):
        transcription = self.transcription_pipeline(audio_path, generate_kwargs={"tgt_lang": self.target_lang})
        return transcription

    def _save_csv(self, transcriptions):
        """Save the current transcriptions to CSV file with retry logic."""
        if not transcriptions:
            return
        
        keys, values = zip(*transcriptions.items())
        df = pd.DataFrame({
            'filename': keys,
            'text': values
        })
        
        csv_path = os.path.join(self.output_csv_dir, self.csv_filename)
        
        # Try to save with retry logic for locked files
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Use utf-8-sig encoding (UTF-8 with BOM) for proper Arabic text display in Excel
                df.to_csv(csv_path, encoding='utf-8-sig', index=False)
                print(f"CSV saved to: {csv_path}")
                return
            except PermissionError as e:
                if attempt < max_retries - 1:
                    print(f"File is locked, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    # Save to backup file with timestamp
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_filename = self.csv_filename.replace('.csv', f'_backup_{timestamp}.csv')
                    backup_path = os.path.join(self.output_csv_dir, backup_filename)
                    try:
                        df.to_csv(backup_path, encoding='utf-8-sig', index=False)
                        print(f"⚠️ Original file is locked. Saved backup to: {backup_path}")
                    except Exception as backup_error:
                        print(f"❌ Failed to save backup: {backup_error}")

    def transcribe_audio_folder(self, folder_path, progress_callback=None):
        transcriptions = {}
        sorted_filenames = sorted(os.listdir(folder_path))
        
        # Filter audio files with supported extensions
        extensions = ('.wav', '.mp3', '.flac', '.m4a', '.ogg')
        audio_files = [f for f in sorted_filenames if f.lower().endswith(extensions)]
        total_files = len(audio_files)
        
        print(f"Starting transcription of {total_files} audio files...")
        start = time.time()
        
        try:
            for i, filename in enumerate(audio_files, 1):
                audio_path = os.path.join(folder_path, filename)
                transcription = self.transcribe_audio(audio_path)
                transcriptions[filename] = transcription['text']
                
                message = f"Finished processing {filename}, {i} out of {total_files}"
                print(message)
                
                if progress_callback:
                    percent = int((i / total_files) * 100)
                    progress_callback(message, percent)
                
                # Save CSV after each file to preserve progress
                self._save_csv(transcriptions)
            
            end = time.time()
            print(f"Transcription completed! Time taken: {end - start:.2f} seconds")
            
        except Exception as e:
            # Save progress before re-raising the exception
            print(f"Error during transcription: {e}. Saving partial results...")
            self._save_csv(transcriptions)
            raise
        
        except KeyboardInterrupt:
            # Handle user interruption (Ctrl+C)
            print("Transcription interrupted by user. Saving partial results...")
            self._save_csv(transcriptions)
            raise