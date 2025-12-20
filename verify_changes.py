import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from backend.processors.audio_transcriber import AudioTranscriber

def test_audio_transcriber_filtering():
    print("Testing AudioTranscriber file filtering...")
    
    # Mock os.listdir to return various files
    with patch('os.listdir') as mock_listdir:
        mock_listdir.return_value = [
            'audio1.wav', 'audio2.mp3', 'image.png', 'audio3.FLAC', 'audio4.m4a', 'script.py'
        ]
        
        # Instantiate with dummy values
        # We mock pipeline to avoid loading heavy models
        with patch('backend.processors.audio_transcriber.pipeline') as mock_pipeline, \
             patch('backend.processors.audio_transcriber.SeamlessM4TTokenizer') as mock_tokenizer:
            
            transcriber = AudioTranscriber("test.csv")
            
            # Mock transcribe method to avoid actual processing
            transcriber.transcribe_audio = MagicMock(return_value={'text': 'dummy'})
            
            # Mock os.path.join and pandas
            with patch('os.path.join', side_effect=lambda p, f: f"{p}/{f}"), \
                 patch('pandas.DataFrame') as mock_df, \
                 patch('time.time', return_value=0):
                 
                 transcriber.transcribe_audio_folder("dummy_folder")
                 
                 # Check how many times transcribe_audio was called
                 # Should be 4 (.wav, .mp3, .FLAC, .m4a)
                 call_count = transcriber.transcribe_audio.call_count
                 print(f"transcribe_audio called {call_count} times.")
                 
                 expected_calls = 4
                 if call_count == expected_calls:
                     print("SUCCESS: Filtering logic worked correctly.")
                 else:
                     print(f"FAILURE: Expected {expected_calls} calls, got {call_count}.")

def test_worker_payload_logic():
    print("\nTesting Worker payload logic simulation...")
    # Simulate the logic added to worker.py
    
    payload = {"audio_folder": "custom/path/audios"}
    STORAGE_DIR = "storage"
    
    # Logic from worker.py
    audio_folder = payload.get("audio_folder")
    if audio_folder:
        # Simple check without Path object for simulation, or use Path if imported
        from pathlib import Path
        target_folder = Path(audio_folder)
        if not target_folder.is_absolute():
                target_folder = Path(STORAGE_DIR) / audio_folder
        target_folder = str(target_folder)
    else:
        target_folder = str(Path(STORAGE_DIR) / "audios" / "splitted_audios")

    print(f"Resolved target_folder: {target_folder}")
    
    expected = os.path.join("storage", "custom", "path", "audios")
    if str(target_folder) == str(expected):
        print("SUCCESS: Payload logic resolved correct path.")
    else:
        print(f"FAILURE: Expected {expected}, got {target_folder}")

if __name__ == "__main__":
    try:
        test_audio_transcriber_filtering()
        test_worker_payload_logic()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
