from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

class TikTokUploader:
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome driver for TikTok automation"""
        options = webdriver.ChromeOptions()
        options.add_argument("--user-data-dir=./chrome_profile")  # Persist login
        self.driver = webdriver.Chrome(options=options)
    
    def login(self, username: str, password: str):
        """Login to TikTok (manual step for first time)"""
        self.driver.get("https://www.tiktok.com/login")
        print("Please log in manually in the browser window, then press Enter here...")
        input("Press Enter after logging in...")
    
    def upload_video(self, video_path: str, caption: str, hashtags: list):
        """Upload video to TikTok"""
        try:
            # Go to upload page
            self.driver.get("https://www.tiktok.com/upload")
            
            # Upload file
            file_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(os.path.abspath(video_path))
            
            # Wait for upload to process
            time.sleep(10)
            
            # Add caption and hashtags
            full_caption = f"{caption} {' '.join(['#' + tag for tag in hashtags])}"
            
            caption_box = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-text='true']"))
            )
            caption_box.clear()
            caption_box.send_keys(full_caption)
            
            # Post video
            post_button = self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='publish-button']")
            post_button.click()
            
            print("Video uploaded successfully!")
            
        except Exception as e:
            print(f"Upload failed: {e}")
    
    def close(self):
        if self.driver:
            self.driver.quit()
