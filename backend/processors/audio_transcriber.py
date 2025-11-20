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





    def transcribe_audio(self, audio_path):
        transcription = self.transcription_pipeline(audio_path, generate_kwargs={"tgt_lang": self.target_lang})
        return transcription


    def transcribe_audio_folder(self, folder_path, progress_callback=None):
        transcriptions = {}
        sorted_filenames = sorted(os.listdir(folder_path))
        
        # Filter only .wav files
        wav_files = [f for f in sorted_filenames if f.endswith(".wav")]
        total_files = len(wav_files)
        
        print(f"Starting transcription of {total_files} audio files...")
        start = time.time()
        
        for i, filename in enumerate(wav_files, 1):
            audio_path = os.path.join(folder_path, filename)
            transcription = self.transcribe_audio(audio_path)
            transcriptions[filename] = transcription['text']
            
            message = f"Finished processing {filename}, {i} out of {total_files}"
            print(message)
            
            if progress_callback:
                percent = int((i / total_files) * 100)
                progress_callback(message, percent)
        
        end = time.time()
        print(f"Transcription completed! Time taken: {end - start:.2f} seconds")
        
        keys, values = zip(*transcriptions.items())

        df = pd.DataFrame({
            'filename': keys,
            'text': values
        })

        df.to_csv(os.path.join(self.output_csv_dir, self.csv_filename), encoding='utf-8-sig', index=False)
        print(f"CSV saved to: {os.path.join(self.output_csv_dir, self.csv_filename)}")