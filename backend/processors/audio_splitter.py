import os
import yt_dlp
import pandas as pd
from pydub import AudioSegment
from tqdm import tqdm
from pydub.silence import split_on_silence


class AudioSplitter:
    
    
    def __init__(self,
                 csv_path, 
                 audio_name,
                 channel_name,
                 output_csv_name,
                 silence_len=200, 
                 silence_thresh=-40,
                 output_splitted_audio_dir='./audios/splitted_audios',
                 output_audio_dir='./audios',
                 output_csv_dir='./datasets_csv/audio_datasets',
                 conditional_function=None,
                ):
        self.audio_name = audio_name
        self.channel_name = channel_name
        self.output_csv_name = output_csv_name
        self.silence_len = silence_len
        self.silence_thresh = silence_thresh
        self.output_splitted_audio_dir = output_splitted_audio_dir
        self.output_audio_dir = output_audio_dir
        self.output_csv_dir = output_csv_dir
        self.conditional_function = conditional_function
        self.ydl_opts = {
            'format': 'bestaudio',
            'extractaudio': True,
            'audioformat': 'wav',
            'verbose': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'skip_download': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]
        }

        self.df = pd.read_csv(csv_path, encoding='utf-8-sig')


    def _conditional_function_caller(self, func):
        return func()

    
    def _match_target_amplitude(self, aChunk, target_dBFS):
        change_in_dBFS = target_dBFS - aChunk.dBFS
        return aChunk.apply_gain(change_in_dBFS)


    def split_audio(self, filename):
        audio = AudioSegment.from_file(os.path.join(self.output_audio_dir, filename+'.wav'), format="wav")
        chunks = split_on_silence (
                audio,
                min_silence_len = self.silence_len,
                silence_thresh = self.silence_thresh
            )
        original_audio_name_lst = []
        splitted_audio_name_lst = []
        for i, chunk in tqdm(enumerate(chunks)):
            silence_chunk = AudioSegment.silent(duration=50)
            audio_chunk = silence_chunk + chunk + silence_chunk
            normalized_chunk = self._match_target_amplitude(audio_chunk, -20.0)
            new_filename = filename+f'_chunk_{i}'
            normalized_chunk.export(
                os.path.join(self.output_splitted_audio_dir, new_filename+'.wav'),
                bitrate = "192k",
                format = "wav"
            )
            
            splitted_audio_name_lst.append(new_filename)
        
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
        
        for index, row in self.df.iterrows():
            filename = f"{row['channel_name'].lower()}_{self.audio_name}_{index}"
            self.ydl_opts['outtmpl'] = os.path.join(self.output_audio_dir, f'{filename}')
            
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    ydl.download([row['video_link']])
                print(f"\n\nSuccessfully downloaded: {row['video_title']}")

            except Exception as e:
                print(f"\n\nError downloading {row['video_title']}: {str(e)}")

            splitted_audio_lst, original_audio_lst = self.split_audio(filename)            
            splitted_audio_name_lst.extend(splitted_audio_lst)
            original_audio_name_lst.extend(original_audio_lst)
            video_title_lst.extend([row['video_title']]*len(original_audio_lst))
            voice_lst.extend([row['voice']]*len(original_audio_lst))
        
        output_df = pd.DataFrame({
            'channel_name': [self.channel_name]*len(video_title_lst),
            'video_title': video_title_lst,
            'original_audio_name': original_audio_name_lst,
            'splitted_audio_name': splitted_audio_name_lst,
            'voice': voice_lst,
        })

        output_df.to_csv(os.path.join(self.output_csv_dir, self.output_csv_name), encoding='utf-8-sig', index=False)
