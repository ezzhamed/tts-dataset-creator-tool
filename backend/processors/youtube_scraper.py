import os
import time
import re

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import yt_dlp
from tqdm import tqdm


class YouTubeScraper:
    
    
    def __init__(self, channel_name, channel_url, voice, output_dir, csv_name, output_audio_dir='./audios', progress_callback=None):
        self.channel_name = channel_name
        self.channel_url = channel_url
        self.voice = voice
        self.output_dir = output_dir
        self.csv_name = csv_name
        self.output_audio_dir = output_audio_dir
        self.progress_callback = progress_callback
        self._driver = webdriver.Chrome()
        self.ydl_opts = {
            'format': 'bestaudio',
            'extractaudio': True,
            'audioformat': 'wav',
            'verbose': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'skip_download': False,
            'noplaylist': True,  # Download only the video, not the playlist
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]
        }
    
    
    def _scroll_to_end(self):
        last_height = self._driver.execute_script("return document.documentElement.scrollHeight")
        
        while True:
            self._driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)
            new_height = self._driver.execute_script("return document.documentElement.scrollHeight")
            
            if new_height == last_height:
                break
                
            last_height = new_height


    def _split_time_ago(self, text):
        splitted_text = text.split()
        num = splitted_text[0]
        time_period = splitted_text[1].replace('s', '')
        return num, time_period


    def _scrape_single_video(self):
        """Scrape a single video page"""
        video_title_lst = []
        release_date_lst1 = []
        release_date_lst2 = []
        video_link_lst = []
        video_duration_lst = []
        
        try:
            # Get video title
            title_el = self._driver.find_element(By.XPATH, '//h1[@class="style-scope ytd-watch-metadata"]/yt-formatted-string')
            video_title_lst.append(title_el.text)
            video_link_lst.append(self.channel_url)
            
            # Get video duration from the player
            try:
                duration_el = self._driver.find_element(By.CLASS_NAME, 'ytp-time-duration')
                video_duration_lst.append(duration_el.text)
            except:
                video_duration_lst.append("0:00")
            
            # For single videos, we use placeholder release dates
            release_date_lst1.append("0")
            release_date_lst2.append("unknown")
            
        except Exception as e:
            print(f"Error scraping single video: {e}")
            # Return empty lists if scraping fails
            return [], [], [], [], []
        
        return video_title_lst, release_date_lst1, release_date_lst2, video_link_lst, video_duration_lst

    def download_videos(self, df):
        os.makedirs(self.output_audio_dir, exist_ok=True)
        total_videos = len(df)
        downloaded_files = []
        
        print(f"Starting download of {total_videos} videos to {self.output_audio_dir}...")
        
        for index, row in df.iterrows():
            if self.progress_callback:
                # We allocate 50% for scraping (already done roughly) and 50% for downloading? 
                # Or just treat downloading as the main progress step since scraping is fast.
                # Let's say scraping was 10%, downloading is 90%.
                # percent = 10 + int((index / total_videos) * 90)
                percent = int((index / total_videos) * 100)
                self.progress_callback(f"Downloading {index + 1}/{total_videos}: {row['video_title'][:30]}...", percent)
            
            # Construct filename: channel_audio_index
            # We use a standard naming convention to easily find it later
            filename = f"{self.channel_name.lower()}_audio_{index}"
            file_path = os.path.join(self.output_audio_dir, f'{filename}')
            
            self.ydl_opts['outtmpl'] = file_path
            
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    ydl.download([row['video_link']])
                print(f"Successfully downloaded: {row['video_title']}")
                downloaded_files.append(filename)
            except Exception as e:
                print(f"Error downloading {row['video_title']}: {str(e)}")
                downloaded_files.append(None) # Mark as failed
                
        return downloaded_files

    def collect_data(self):
        self._driver.get(self.channel_url)
        time.sleep(2)

        # Check URL type
        is_playlist = "playlist" in self.channel_url or "list=" in self.channel_url
        is_single_video = "/watch?v=" in self.channel_url and not is_playlist

        if is_single_video:
            # Handle single video
            video_title_lst, release_date_lst1, release_date_lst2, video_link_lst, video_duration_lst = self._scrape_single_video()
        else:
            # Scroll for playlists and channels
            self._scroll_to_end()

            video_title_lst = []
            release_date_lst1 = []
            release_date_lst2 = []
            video_link_lst = []
            video_duration_lst = []
            
            if is_playlist:
                # Playlist Selectors
                video_elements = self._driver.find_elements(By.TAG_NAME, 'ytd-playlist-video-renderer')
                print(f"Found {len(video_elements)} videos in playlist")
                for video in video_elements:
                    try:
                        title_el = video.find_element(By.ID, 'video-title')
                        raw_href = title_el.get_attribute('href')
                        
                        # Clean the video URL - extract only the video ID
                        # Playlist URLs look like: /watch?v=VIDEO_ID&list=PLAYLIST_ID&index=N
                        # We need only: https://www.youtube.com/watch?v=VIDEO_ID
                        if raw_href:
                            video_id_match = re.search(r'[?&]v=([^&]+)', raw_href)
                            if video_id_match:
                                video_id = video_id_match.group(1)
                                clean_url = f"https://www.youtube.com/watch?v={video_id}"
                                video_link_lst.append(clean_url)
                                video_title_lst.append(title_el.get_attribute('title'))
                                print(f"Added video: {title_el.get_attribute('title')} - {clean_url}")
                                
                                # Duration
                                try:
                                    duration_el = video.find_element(By.XPATH, './/span[contains(@class, "ytd-thumbnail-overlay-time-status-renderer")]')
                                    video_duration_lst.append(duration_el.text.strip())
                                except:
                                    video_duration_lst.append("0:00")

                                # Playlist doesn't always show relative time easily, using placeholder
                                release_date_lst1.append("0")
                                release_date_lst2.append("unknown")
                    except Exception as e:
                        print(f"Error parsing video in playlist: {e}")
            else:
                # Channel Selectors (Existing)
                video_details = self._driver.find_elements(By.ID, 'video-title-link')
                video_time_dates = self._driver.find_elements(By.XPATH, '//*[@id="metadata-line"]/span[2]')
                video_durations = self._driver.find_elements(By.XPATH, '//*[@id="length"]')
                
                for i, video_detail in enumerate(video_details):            
                    try:
                        video_link_lst.append(video_detail.get_attribute('href'))
                        video_title_lst.append(video_detail.get_attribute('title'))
                        
                        try:
                            video_duration_lst.append(video_durations[i].get_attribute('aria-label').split()[0])
                        except:
                            video_duration_lst.append("0:00")

                        try:
                            num, time_period = self._split_time_ago(video_time_dates[i].text)
                            release_date_lst1.append(num)
                            release_date_lst2.append(time_period)
                        except:
                            release_date_lst1.append("0")
                            release_date_lst2.append("unknown")
                    except Exception as e:
                        print(f"Error parsing video in channel: {e}")

        self._driver.quit()

        # If voice is not provided (e.g. empty string), try to use channel name or default
        voice_label = self.voice if self.voice else self.channel_name

        df = pd.DataFrame({
            'channel_name': [self.channel_name]*len(video_link_lst),
            'video_title': video_title_lst,
            'release_date_1': release_date_lst1,
            'release_date_2': release_date_lst2,
            'video_link': video_link_lst,
            'video_duration (min)': video_duration_lst,
            'voice': [voice_label]*len(video_link_lst),
        })
        
        # Start Downloading
        audio_filenames = self.download_videos(df)
        
        # Add filename column
        df['audio_filename'] = audio_filenames
        
        # Filter out failed downloads
        df = df[df['audio_filename'].notna()]
        
        df.to_csv(os.path.join(self.output_dir, self.csv_name), encoding='utf-8-sig', index=False)