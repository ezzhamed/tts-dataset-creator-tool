import os
from pydub import AudioSegment
import shutil
from pathlib import Path

class VideoProcessor:
    def __init__(self, storage_dir):
        self.storage_dir = Path(storage_dir)
        self.temp_dir = self.storage_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def extract_audio(self, video_path):
        # Simple audio extraction using pydub (which uses ffmpeg)
        # Note: pydub opens audio files. For video, we might need to use ffmpeg directly or pydub's from_file if it supports it (it usually does via ffmpeg)
        try:
            audio = AudioSegment.from_file(video_path)
            output_path = self.temp_dir / f"{Path(video_path).stem}.wav"
            audio.export(output_path, format="wav")
            return str(output_path)
        except Exception as e:
            print(f"Error extracting audio: {e}")
            raise

    def combine_audio_video(self, video_path, audio_path, output_path):
        # This usually requires ffmpeg command line
        # ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4
        cmd = f'ffmpeg -y -i "{video_path}" -i "{audio_path}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{output_path}"'
        return os.system(cmd)

class AudioProcessor:
    def __init__(self):
        pass

    def process_audio(self, audio_path):
        # Mock processing: just reverse the audio for demonstration
        # or change speed, or use the Transcriber if we can load it
        audio = AudioSegment.from_file(audio_path)
        
        # Example: Make it quieter
        processed_audio = audio - 10
        
        output_path = str(audio_path).replace(".wav", "_processed.wav")
        processed_audio.export(output_path, format="wav")
        return output_path
