# import required modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from record_audio import AudioRecorder
#from speech_to_text import SpeechToText
import os
import tempfile
from dotenv import load_dotenv
import requests

load_dotenv()

class JoinGoogleMeet:
    def __init__(self):
        self.mail_address = os.getenv('GOOGLE_EMAIL')
        self.password = os.getenv('GOOGLE_PASSWORD')
        # create chrome instance
        opt = Options()
        opt.add_argument('--disable-blink-features=AutomationControlled')
        opt.add_argument('--start-maximized')
        opt.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.geolocation": 0,
            "profile.default_content_setting_values.notifications": 1
        })
        self.driver = webdriver.Chrome(options=opt)

    def Glogin(self):
        # Login Page
        self.driver.get(
            'https://accounts.google.com/ServiceLogin?hl=en&passive=true&continue=https://www.google.com/&ec=GAZAAQ')
    
        # input Gmail
        self.driver.find_element(By.ID, "identifierId").send_keys(self.mail_address)
        self.driver.find_element(By.ID, "identifierNext").click()
        self.driver.implicitly_wait(10)
    
        # input Password
        self.driver.find_element(By.XPATH,
            '//*[@id="password"]/div[1]/div/div[1]/input').send_keys(self.password)
        self.driver.implicitly_wait(10)
        self.driver.find_element(By.ID, "passwordNext").click()
        self.driver.implicitly_wait(10)    
        # go to google home page
        self.driver.get('https://google.com/')
        self.driver.implicitly_wait(100)
        print("Gmail login activity: Done")
 
    def turnOffMicCam(self, meet_link):
        # Navigate to Google Meet URL
        self.driver.get(meet_link)
        time.sleep(5)  # Wait for page to load
        
        print("Checking meeting controls...")
        print(f"Current URL: {self.driver.current_url}")
        
        # Check if we're actually on a Google Meet page
        if "meet.google.com" not in self.driver.current_url:
            print("Not on Google Meet page, waiting for redirect...")
            time.sleep(10)
        
        # Turn off microphone using better XPath selector
        try:
            mic_button = self.driver.find_element(
                By.XPATH, "//div[@aria-label='Turn off microphone']"
            )
            if mic_button:
                mic_button.click()
                print("Microphone turned off.")
        except Exception as e:
            print(f"Microphone button not found or already muted: {e}")
        
        time.sleep(1)
        
        # Turn off camera using better XPath selector
        try:
            camera_button = self.driver.find_element(
                By.XPATH, "//div[@aria-label='Turn off camera']"
            )
            if camera_button:
                camera_button.click()
                print("Camera turned off.")
        except Exception as e:
            print(f"Camera button not found or already off: {e}")
        
        time.sleep(1)
        
        # Try to join the meeting
        try:
            join_button = self.driver.find_element(By.XPATH, "//span[text()='Join now']")
            join_button.click()
            print("Joined the meeting.")
        except Exception as e:
            print(f"Join now button not found: {e}")
            try:
                ask_to_join_button = self.driver.find_element(
                    By.XPATH, "//span[text()='Ask to join']"
                )
                ask_to_join_button.click()
                print("Requested to join the meeting.")
            except Exception as e2:
                print(f"Neither 'Join now' nor 'Ask to join' button was found: {e2}")
        
        print("Meeting controls setup completed - continuing...")
        
        # If no controls were found, that's okay - just continue
        print("Continuing with join process...")
    
    def checkIfJoined(self):
        try:
            # Wait for the join button to appear
            join_button = WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.uArJ5e.UQuaGc.Y5sE8d.uyXBBb.xKiqt'))
            )
            print("Meeting has been joined")
        except (TimeoutException, NoSuchElementException):
            print("Meeting has not been joined")
    
    def AskToJoin(self, audio_path, duration):
        # The join logic is now handled in turnOffMicCam method
        # Just wait a bit and start recording
        time.sleep(5)
        print("Starting audio recording...")
        
        # Start audio recording
        AudioRecorder().get_audio(audio_path, duration)
        print("Audio recording completed")

def get_latest_meeting_link():
    """Fetch the latest meeting link from the database via API"""
    try:
        # Make a request to your Next.js API
        response = requests.get('http://localhost:3000/api/meetings')
        
        if response.status_code == 200:
            data = response.json()
            if data.get('meetings') and len(data['meetings']) > 0:
                latest_meeting = data['meetings'][0]  # First one is latest due to DESC order
                return latest_meeting.get('link')
        
        print("No meetings found in database")
        return None
    except Exception as e:
        print(f"Error fetching meeting link: {e}")
        return None

def main():
    import signal
    
    def timeout_handler(signum, frame):
        print("Script timed out after 5 minutes. Exiting...")
        exit(1)
    
    # Set a 5-minute timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    
    try:
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "output.wav")
        
        # Get the latest meeting link from database
        meet_link = get_latest_meeting_link()
        
        if not meet_link:
            print("No meeting link found. Using environment variable as fallback.")
            meet_link = os.getenv('MEETING_LINK')
        
        if not meet_link:
            print("No meeting link available. Exiting.")
            return
        
        duration = int(os.getenv('RECORDING_DURATION', 60))
        
        print(f"Using meeting link: {meet_link}")
        
        obj = JoinGoogleMeet()
        obj.Glogin()
        obj.turnOffMicCam(meet_link)
        obj.AskToJoin(audio_path, duration)
        # SpeechToText().transcribe(audio_path)  # Commented out since module is missing
        
        # Cancel the alarm if we get here successfully
        signal.alarm(0)
        
    except Exception as e:
        print(f"Error in main: {e}")
        signal.alarm(0)  # Cancel the alarm
        raise

#call the main function
if __name__ == "__main__":
    main()