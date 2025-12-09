import os
import pandas as pd
from pydub import AudioSegment
from tqdm import tqdm
import torch
import numpy as np
import warnings

# Filter warnings from torch/silero
warnings.filterwarnings("ignore")

class AudioSplitter:
    
    def __init__(self,
                 csv_path=None, 
                 input_audio_folder=None,
                 audio_name="audio",
                 channel_name="unknown_channel",
                 output_csv_name=None,
                 silence_len=None, # Deprecated/Not used in VAD directly but kept for compat
                 silence_thresh=None, # Deprecated/Not used in VAD directly
                 min_audio_len=2000, # 2 seconds
                 max_audio_len=25000, # 25 seconds
                 output_splitted_audio_dir='./audios/splitted_audios',
                 output_audio_dir='./audios',
                 output_csv_dir='./datasets_csv/audio_datasets',
                 conditional_function=None,
                 progress_callback=None
                ):
        self.audio_name = audio_name
        self.channel_name = channel_name
        self.output_csv_name = output_csv_name
        self.min_audio_len = min_audio_len
        self.max_audio_len = max_audio_len
        self.output_splitted_audio_dir = output_splitted_audio_dir
        self.output_audio_dir = output_audio_dir
        self.output_csv_dir = output_csv_dir
        self.conditional_function = conditional_function
        self.progress_callback = progress_callback
        
        # Load VAD model once
        try:
            print("Loading Silero VAD model...")
            self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                             model='silero_vad',
                                             force_reload=False,
                                             trust_repo=True,
                                             verbose=False)
            self.get_speech_timestamps = utils[0]
            print("Silero VAD model loaded successfully.")
        except Exception as e:
            print(f"Error loading Silero VAD: {e}")
            self.model = None

        if csv_path:
            self.df = pd.read_csv(csv_path, encoding='utf-8-sig')
            print(f"DEBUG: Loaded CSV with {len(self.df)} rows.")
        elif input_audio_folder:
            self.output_audio_dir = input_audio_folder
            # Support multiple formats
            extensions = ('.wav', '.mp3', '.flac', '.m4a')
            files = [f for f in os.listdir(input_audio_folder) if f.lower().endswith(extensions)]
            print(f"DEBUG: Found {len(files)} audio files in {input_audio_folder}")
            
            if not files:
                raise ValueError(f"No audio files found in {input_audio_folder}. Please check the path.")

            if channel_name == "unknown_channel" or not channel_name:
                 self.channel_name = os.path.basename(input_audio_folder)

            if not self.output_csv_name:
                self.output_csv_name = f"{self.channel_name}_splitted.csv"

            data = []
            for f in files:
                name_no_ext = os.path.splitext(f)[0]
                data.append({
                    'channel_name': self.channel_name,
                    'video_title': name_no_ext,
                    'audio_filename': name_no_ext,
                    'voice': 'unknown'
                })
            self.df = pd.DataFrame(data)
        else:
             raise ValueError("Either csv_path or input_audio_folder must be provided")


    def _conditional_function_caller(self, func):
        return func()

    
    def _match_target_amplitude(self, aChunk, target_dBFS):
        change_in_dBFS = target_dBFS - aChunk.dBFS
        return aChunk.apply_gain(change_in_dBFS)


    def split_audio(self, filename):
        # Allow format auto-detection or fallback
        file_path_wav = os.path.join(self.output_audio_dir, filename+'.wav')
        file_path_mp3 = os.path.join(self.output_audio_dir, filename+'.mp3')
        
        file_path = None
        if os.path.exists(file_path_wav):
            file_path = file_path_wav
        elif os.path.exists(file_path_mp3):
            file_path = file_path_mp3
        else:
            # Try finding without extension if user passed full name or other extension
            possible_files = [f for f in os.listdir(self.output_audio_dir) if f.startswith(filename)]
            if possible_files:
                file_path = os.path.join(self.output_audio_dir, possible_files[0])
        
        if not file_path:
            print(f"DEBUG: Could not find audio file for {filename}")
            return [], []

        print(f"DEBUG: Processing file: {file_path}")
        try:
            audio = AudioSegment.from_file(file_path)
        except Exception as e:
             print(f"DEBUG: Failed to load audio file {file_path}: {e}")
             return [], []
        
        chunks = []
        
        # Method 1: Use Silero VAD (Preferred)
        if self.model:
            try:
                # Prepare audio for VAD (16k, mono, float32)
                audio_16k = audio.set_frame_rate(16000).set_channels(1)
                samples = np.array(audio_16k.get_array_of_samples())
                
                # Handle empty audio
                if len(samples) == 0:
                    return [], []

                # Convert to float32 and normalize
                if audio_16k.sample_width == 2: # 16-bit
                    samples_float = samples.astype(np.float32) / 32768.0
                elif audio_16k.sample_width == 4: # 32-bit
                     samples_float = samples.astype(np.float32) / 2147483648.0
                else:
                    # Fallback for 24-bit etc if needed, but pydub handles most
                     samples_float = samples.astype(np.float32) / float(1 << (8 * audio_16k.sample_width - 1))

                tensor = torch.from_numpy(samples_float)
                
                # Get speech timestamps (in samples at 16k)
                # threshold=0.5 is standard. min_silence_duration_ms=100 helps find small gaps.
                # UPDATED: threshold 0.4 -> 0.5 (Stricter), min_silence 300 -> 100 (Find more pauses)
                timestamps = self.get_speech_timestamps(tensor, self.model, sampling_rate=16000, threshold=0.5, min_silence_duration_ms=100)
                print(f"DEBUG: VAD found {len(timestamps)} speech attributes.")
                
                # Extract chunks using timestamps
                # Map 16k timestamps back to original audio ms
                
                raw_chunks_ms = []
                for ts in timestamps:
                    start_ms = int(ts['start'] / 16000 * 1000)
                    end_ms = int(ts['end'] / 16000 * 1000)
                    raw_chunks_ms.append((start_ms, end_ms))
                
                # Merge logic
                merged_chunks_ms = []
                if raw_chunks_ms:
                    current_start, current_end = raw_chunks_ms[0]
                    
                    for i in range(1, len(raw_chunks_ms)):
                        next_start, next_end = raw_chunks_ms[i]
                        gap = next_start - current_end
                        current_dur = current_end - current_start
                        
                        should_merge = False
                        
                        # Logic Revised:
                        # 1. If current chunk is too small (< min_len), we TRY to merge to reach min_len.
                        # 2. If chunk is already good size (> min_len), we ONLY merge if gap is insignificant (< 200ms).
                        # 3. If gap is distinct (> 200ms), we treat it as a sentence boundary and split, 
                        #    UNLESS current chunk is tiny.
                        
                        merged_dur = next_end - current_start
                        
                        # Hard constraint: Never exceed max_audio_len
                        if merged_dur > self.max_audio_len:
                            should_merge = False
                        else:
                            if current_dur < self.min_audio_len:
                                # Current is garbage/short, must merge to save it
                                should_merge = True
                            elif gap < 200: 
                                # Tiny gap (intra-word or fast speech), keep together
                                should_merge = True
                            else:
                                # Gap is > 200ms AND current is > min_len.
                                # This is likely a valid pause between sentences. Do NOT merge.
                                should_merge = False
                        
                        if should_merge:
                            current_end = next_end
                        else:
                            # Commit current
                            merged_chunks_ms.append((current_start, current_end))
                            current_start = next_start
                            current_end = next_end
                    
                    # Append last
                    merged_chunks_ms.append((current_start, current_end))
                
                # Extract actual audio objects
                for start, end in merged_chunks_ms:
                    # Double check constraints
                    dur = end - start
                    if dur >= self.min_audio_len: # Strict min check
                        # If > max_len (rare), we might want to split it, but VAD usually pauses.
                        # If strict max needed:
                        if dur > self.max_audio_len:
                            # Split simply by max len
                            sub_start = start
                            while sub_start < end:
                                sub_end = min(sub_start + self.max_audio_len, end)
                                if sub_end - sub_start >= self.min_audio_len:
                                    chunks.append(audio[sub_start:sub_end])
                                sub_start = sub_end
                        else:
                            chunks.append(audio[start:end])
                            
            except Exception as e:
                print(f"VAD processing failed: {e}. Falling back to pydub.")
                chunks = [] # Trigger fallback
        
        # Fallback: Pydub Silence (if VAD failed or no model)
        if not chunks:
            from pydub.silence import detect_nonsilent
            nonsilent_ranges = detect_nonsilent(audio, min_silence_len=500, silence_thresh=-40)
            for start_i, end_i in nonsilent_ranges:
                chunk = audio[start_i:end_i]
                if len(chunk) >= self.min_audio_len:
                     # Basic max len splitting for fallback
                    if len(chunk) > self.max_audio_len:
                         for i in range(0, len(chunk), self.max_audio_len):
                             sub = chunk[i:i+self.max_audio_len]
                             if len(sub) >= self.min_audio_len:
                                 chunks.append(sub)
                    else:
                        chunks.append(chunk)

        # Final Export
        original_audio_name_lst = []
        splitted_audio_name_lst = []
        
        chunk_idx = 0
        for chunk in chunks:
            # Padding
            silence_chunk = AudioSegment.silent(duration=50) 
            audio_chunk = silence_chunk + chunk + silence_chunk
            
            # Normalize
            normalized_chunk = self._match_target_amplitude(audio_chunk, -20.0)
            
            new_filename = filename+f'_v2_chunk_{chunk_idx}'
            normalized_chunk.export(
                os.path.join(self.output_splitted_audio_dir, new_filename+'.wav'),
                bitrate = "192k",
                format = "wav"
            )
            
            splitted_audio_name_lst.append(new_filename)
            chunk_idx += 1
        
        original_audio_name_lst.extend([filename]*len(splitted_audio_name_lst))

        if self.conditional_function != None:
            lst, _ = self._conditional_function_caller(lambda: self.conditional_function(splitted_audio_name_lst, original_audio_name_lst, self.output_splitted_audio_dir))
            splitted_audio_name_lst, original_audio_name_lst = lst[0], lst[1]
        
        return splitted_audio_name_lst, original_audio_name_lst


    def process_videos(self):
        video_title_lst = []
        splitted_audio_name_lst = []
        original_audio_name_lst = []
        voice_lst = []
        os.makedirs(self.output_audio_dir, exist_ok=True)
        os.makedirs(self.output_splitted_audio_dir, exist_ok=True) # Ensure output dir exists
        
        total_videos = len(self.df)
        
        for index, row in self.df.iterrows():
            if self.progress_callback:
                percent = int((index / total_videos) * 100)
                self.progress_callback(f"Processing video {index + 1}/{total_videos}: {row['video_title'][:30]}...", percent)
            
            if 'audio_filename' in row and pd.notna(row['audio_filename']):
                filename = row['audio_filename']
            else:
                 print(f"Warning: No audio filename for {row['video_title']}, skipping...")
                 continue

            # Check if file exists (handled inside split_audio now effectively, but kept simpler here)
            # Remove strict check here to allow fuzzy match in split_audio
            pass
            
            # --- RESUME LOGIC ---
            # Check if ANY chunks for this file already exist to avoid re-splitting
            # We assume if chunk_0 exists, the file was processed.
            # Filename format: {filename}_v2_chunk_0.wav
            expected_first_chunk = os.path.join(self.output_splitted_audio_dir, filename + '_v2_chunk_0.wav')
            if os.path.exists(expected_first_chunk):
                if self.progress_callback:
                     self.progress_callback(f"Skipping {filename} (Already processed)", percent)
                print(f"DEBUG: Skipping {filename} - Chunks already exist.")
                
                # Logic to add existing chunks to list so CSV is still complete? 
                # Ideally yes, but that requires scanning. 
                # For now, let's just skip processing. 
                # WARNING: If we skip, they won't be in the *current* execution's output lists 
                # unless we scan for them.
                # Let's scan for them to keep the CSV complete.
                
                existing_chunks = [f for f in os.listdir(self.output_splitted_audio_dir) if f.startswith(filename + '_v2_chunk_')]
                # Sort them naturally/numerically if needed, but not critical for CSV listing
                
                if existing_chunks:
                    splitted_audio_name_lst.extend([os.path.splitext(c)[0] for c in existing_chunks])
                    original_audio_name_lst.extend([filename] * len(existing_chunks))
                    video_title_lst.extend([row['video_title']] * len(existing_chunks))
                    voice_lst.extend([row['voice']] * len(existing_chunks))
                continue
            # --------------------

            splitted_audio_lst, original_audio_lst = self.split_audio(filename)   
            
            if not splitted_audio_lst:
                print(f"DEBUG: No chunks generated for {filename}")
                     
            splitted_audio_name_lst.extend(splitted_audio_lst)
            original_audio_name_lst.extend(original_audio_lst)
            video_title_lst.extend([row['video_title']]*len(original_audio_lst))
            voice_lst.extend([row['voice']]*len(original_audio_lst))
            
        if self.progress_callback:
            self.progress_callback("Finalizing...", 100)
        
        output_df = pd.DataFrame({
            'channel_name': [self.channel_name]*len(video_title_lst),
            'video_title': video_title_lst,
            'original_audio_name': original_audio_name_lst,
            'splitted_audio_name': splitted_audio_name_lst,
            'voice': voice_lst,
        })

        output_df.to_csv(os.path.join(self.output_csv_dir, self.output_csv_name), encoding='utf-8-sig', index=False)

