# TTS Dataset Creator

A powerful tool for building Arabic audio datasets for Text-to-Speech (TTS) training. This application automates the process of collecting, processing, and transcribing audio data from YouTube.

## Features

- **YouTube Scraper**: Download audio from YouTube videos, playlists, and channels
- **Audio Splitter**: Automatically split audio into chunks, normalize volume, and add silence padding
- **Audio Transcriber**: Transcribe audio using either:
  - Local STT model (Seamless M4T)
  - ElevenLabs API (cloud-based)

## Tech Stack

### Backend
- FastAPI
- WebSockets for real-time progress updates
- File-based IPC for task management
- SSL/HTTPS support

### Frontend
- React
- Vite
- Tailwind CSS
- Pure black theme design

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ezzhamed/tts-dataset-creator-tool.git
cd tts-dataset-creator-tool
```

2. Install backend dependencies:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

**Note:** You also need to have `ffmpeg` installed on your system.
- Ubuntu: `sudo apt install ffmpeg`
- Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
- Mac: `brew install ffmpeg`

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Generate SSL certificates (for development):
```bash
# In project root
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

## Usage

1. Start the backend server:
```bash
.venv\Scripts\uvicorn backend.app:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem --reload
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173` (or the port shown in the terminal)

## Workflow

1. **Step 1 - Scraper**: Enter a YouTube URL (video, playlist, or channel) to download and extract audio
2. **Step 2 - Splitter**: Select the scraped CSV file to split audio into chunks
3. **Step 3 - Transcriber**: Choose your transcription method and generate the final dataset

## Author

**Ezzeldeen Hamed**
- GitHub: [@ezzhamed](https://github.com/ezzhamed)

## License

This project is open source and available under the MIT License.
