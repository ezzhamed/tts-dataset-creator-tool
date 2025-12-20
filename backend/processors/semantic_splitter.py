import os
import pandas as pd
from pydub import AudioSegment
from faster_whisper import WhisperModel
import torch
import warnings

# Filter warnings
warnings.filterwarnings("ignore")

class SemanticSplitter:
    
    def __init__(self,
                 input_audio_folder=None,
                 output_splitted_audio_dir='./audios/splitted_audios',
                 output_csv_dir='./datasets_csv/audio_datasets',
                 model_size="medium",
                 device="cuda" if torch.cuda.is_available() else "cpu",
                 progress_callback=None
                ):
        self.input_audio_folder = input_audio_folder
        self.output_splitted_audio_dir = output_splitted_audio_dir
        self.output_csv_dir = output_csv_dir
        self.progress_callback = progress_callback
        self.device = device
        self.compute_type = "float16" if device == "cuda" else "int8"
        
        print(f"Loading Faster-Whisper model ({model_size}) on {device}...")
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=self.compute_type)
            print("Faster-Whisper model loaded successfully.")
        except Exception as e:
            print(f"Error loading Faster-Whisper: {e}")
            raise e

    def split_audio(self):
        if not self.input_audio_folder or not os.path.exists(self.input_audio_folder):
            raise ValueError(f"Input folder not found: {self.input_audio_folder}")

        # Ensure output directories exist
        os.makedirs(self.output_splitted_audio_dir, exist_ok=True)
        os.makedirs(self.output_csv_dir, exist_ok=True)

        # Get audio files
        extensions = ('.wav', '.mp3', '.flac', '.m4a', '.ogg')
        audio_files = [f for f in os.listdir(self.input_audio_folder) if f.lower().endswith(extensions)]
        total_files = len(audio_files)
        
        if total_files == 0:
            raise ValueError(f"No audio files found in {self.input_audio_folder}")

        print(f"Found {total_files} audio files for semantic spitting.")
        
        all_segments_data = []

        for idx, filename in enumerate(audio_files):
            file_path = os.path.join(self.input_audio_folder, filename)
            base_name = os.path.splitext(filename)[0]
            
            if self.progress_callback:
                percent = int((idx / total_files) * 100)
                self.progress_callback(f"Processing {filename}...", percent)
            
            try:
                # Load Audio for cutting
                audio = AudioSegment.from_file(file_path)
                
                # Transcribe
                segments, info = self.model.transcribe(file_path, beam_size=5, word_timestamps=True)
                
                # Iterate over segments (sentences)
                segment_idx = 0
                for segment in segments:
                    start_ms = int(segment.start * 1000)
                    end_ms = int(segment.end * 1000)
                    text = segment.text.strip()
                    
                    # Basic constraints
                    duration_ms = end_ms - start_ms
                    if duration_ms < 1000: # Skip very short segments < 1s
                        continue
                        
                    # Extract audio clip
                    clip = audio[start_ms:end_ms]
                    
                    # Export
                    new_filename = f"{base_name}_seg_{segment_idx:04d}.wav"
                    output_path = os.path.join(self.output_splitted_audio_dir, new_filename)
                    
                    clip.export(output_path, format="wav")
                    
                    all_segments_data.append({
                        'original_file': filename,
                        'audio_filename': new_filename,
                        'text': text,
                        'duration_sec': duration_ms / 1000.0,
                        'speaker': 'unknown' 
                    })
                    
                    segment_idx += 1
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue

        if self.progress_callback:
            self.progress_callback("Finalizing...", 100)

        # Save Metadata
        output_csv_name = f"semantic_split_{os.path.basename(self.input_audio_folder)}.csv"
        df = pd.DataFrame(all_segments_data)
        csv_path = os.path.join(self.output_csv_dir, output_csv_name)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        return {
            "csv_path": csv_path,
            "csv_filename": output_csv_name,
            "audio_dir": self.output_splitted_audio_dir
        }
