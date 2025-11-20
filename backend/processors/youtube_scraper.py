import os
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By


class YouTubeScraper:
    
    
    def __init__(self, channel_name, channel_url, voice, output_dir, csv_name):
        self.channel_name = channel_name
        self.channel_url = channel_url
        self.voice = voice
        self.output_dir = output_dir
        self.csv_name = csv_name
        self._driver = webdriver.Chrome()
    
    
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
                for video in video_elements:
                    try:
                        title_el = video.find_element(By.ID, 'video-title')
                        video_link_lst.append(title_el.get_attribute('href'))
                        video_title_lst.append(title_el.get_attribute('title'))
                        
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
        
        df.to_csv(os.path.join(self.output_dir, self.csv_name), encoding='utf-8-sig', index=False)