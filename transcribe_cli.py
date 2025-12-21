"""
Standalone Audio Transcriber Script
Run directly from CMD: python transcribe_cli.py

Usage:
    python transcribe_cli.py --method elevenlabs --api-key YOUR_API_KEY
    python transcribe_cli.py --method local
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    parser = argparse.ArgumentParser(description='Audio Transcriber CLI')
    parser.add_argument('--method', type=str, choices=['local', 'elevenlabs'], default='elevenlabs',
                        help='Transcription method: local (Seamless M4T) or elevenlabs (API)')
    parser.add_argument('--api-key', type=str, default=None,
                        help='ElevenLabs API key (required for elevenlabs method)')
    parser.add_argument('--input-folder', type=str, default=None,
                        help='Input folder containing audio files (default: storage/audios/splitted_audios)')
    parser.add_argument('--output-csv', type=str, default='transcription.csv',
                        help='Output CSV filename (default: transcription.csv)')
    
    args = parser.parse_args()
    
    # Setup paths
    STORAGE_DIR = PROJECT_ROOT / "storage"
    OUTPUT_CSV_DIR = STORAGE_DIR / "datasets_csv" / "audio_text_datasets"
    OUTPUT_CSV_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.input_folder:
        input_folder = Path(args.input_folder)
        if not input_folder.is_absolute():
            input_folder = STORAGE_DIR / args.input_folder
    else:
        input_folder = STORAGE_DIR / "audios" / "splitted_audios"
    
    if not input_folder.exists():
        print(f"❌ Error: Input folder not found: {input_folder}")
        sys.exit(1)
    
    print("=" * 60)
    print("🎙️  Audio Transcriber CLI")
    print("=" * 60)
    print(f"📁 Input folder: {input_folder}")
    print(f"📄 Output CSV: {OUTPUT_CSV_DIR / args.output_csv}")
    print(f"🔧 Method: {args.method}")
    print("=" * 60)
    
    def progress_callback(message, percent):
        print(f"[{percent:3d}%] {message}")
    
    try:
        if args.method == 'elevenlabs':
            if not args.api_key:
                print("❌ Error: API key is required for ElevenLabs method")
                print("Usage: python transcribe_cli.py --method elevenlabs --api-key YOUR_API_KEY")
                sys.exit(1)
            
            from backend.tools.elevenlabs_transcriber import ElevenLabsTranscriber
            
            transcriber = ElevenLabsTranscriber(
                api_key=args.api_key,
                csv_filename=args.output_csv,
                output_csv_dir=str(OUTPUT_CSV_DIR)
            )
            
            print("\n🚀 Starting ElevenLabs transcription...\n")
            transcriber.transcribe_audio_folder(str(input_folder), progress_callback=progress_callback)
            
        else:  # local
            from backend.processors.audio_transcriber import AudioTranscriber
            
            print("\n🚀 Starting local transcription (Seamless M4T)...\n")
            print("⚠️  Note: First run will download the model (~2GB)\n")
            
            transcriber = AudioTranscriber(
                csv_filename=args.output_csv,
                output_csv_dir=str(OUTPUT_CSV_DIR)
            )
            
            transcriber.transcribe_audio_folder(str(input_folder), progress_callback=progress_callback)
        
        print("\n" + "=" * 60)
        print("✅ Transcription completed successfully!")
        print(f"📄 CSV saved to: {OUTPUT_CSV_DIR / args.output_csv}")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Transcription interrupted by user.")
        print("📄 Partial results have been saved.")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("📄 Partial results (if any) have been saved.")
        sys.exit(1)

if __name__ == "__main__":
    main()
