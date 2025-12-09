import os
import sys
import wave
import struct
import math
from pathlib import Path
import time

# Add backend to path
sys.path.append(os.getcwd())

from backend.processors.audio_splitter import AudioSplitter

def create_dummy_wav(filename, duration_sec=3):
    sample_rate = 44100
    num_samples = duration_sec * sample_rate
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(2) # 2 bytes
        wav_file.setframerate(sample_rate)
        
        # Generate silence/noise
        data = []
        for i in range(num_samples):
            # Generate a sine wave
            value = int(32767.0 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
            data.append(struct.pack('<h', value))
            
        wav_file.writeframes(b''.join(data))

def test_folder_splitting():
    print("Starting Directory Splitting Test...")
    
    # Setup directories
    test_dir = Path("test_audio_input")
    test_dir.mkdir(exist_ok=True)
    
    output_audio_dir = Path("test_audio_output")
    output_audio_dir.mkdir(exist_ok=True)
    
    output_csv_dir = Path("test_csv_output")
    output_csv_dir.mkdir(exist_ok=True)
    
    # Create dummy audio
    dummy_file = test_dir / "test_clip.wav"
    create_dummy_wav(str(dummy_file))
    print(f"Created dummy audio file: {dummy_file}")
    
    try:
        # Instantiate Splitter with folder
        splitter = AudioSplitter(
            input_audio_folder=str(test_dir),
            output_splitted_audio_dir=str(output_audio_dir),
            output_csv_dir=str(output_csv_dir)
        )
        
        print("Running process_videos()...")
        splitter.process_videos()
        
        # Verify output
        expected_csv = output_csv_dir / "test_audio_input_splitted.csv"
        if expected_csv.exists():
            print(f"SUCCESS: Output CSV found at {expected_csv}")
            with open(expected_csv, 'r') as f:
                print("CSV Content:")
                print(f.read())
        else:
            print(f"FAILURE: Output CSV not found at {expected_csv}")
            
        # Check if split files exist (might be empty if dummy audio is too simple/short/silence logic filters it)
        # Note: My dummy wav is a sine wave (non-silent), so it should be detected as one chunk or split if long enough.
        # Length is 3s. min_audio_len default is 2s. So it should likely preserve it.
        split_files = list(output_audio_dir.glob("*.wav"))
        print(f"Found {len(split_files)} split audio files.")
        if len(split_files) > 0:
            print("SUCCESS: Split audio files generated.")
        else:
            print("WARNING: No split files. This might be due to silence detection settings on the sine wave.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    # import shutil
    # shutil.rmtree(test_dir)
    # shutil.rmtree(output_audio_dir)
    # shutil.rmtree(output_csv_dir)

if __name__ == "__main__":
    test_folder_splitting()
