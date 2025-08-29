import zoom_meeting_sdk as zoom
import jwt
from deepgram_transcriber import DeepgramTranscriber
from datetime import datetime, timedelta
import os
import requests
import urllib.parse
import json

import cv2
import numpy as np
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib

def save_yuv420_frame_as_png(frame_bytes, width, height, output_path):
    try:
        # Convert bytes to numpy array
        yuv_data = np.frombuffer(frame_bytes, dtype=np.uint8)
        # Reshape into I420 format with U/V planes
        yuv_frame = yuv_data.reshape((height * 3//2, width))
        # Convert from YUV420 to BGR
        bgr_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)
        # Save as PNG
        cv2.imwrite(output_path, bgr_frame)
    except Exception as e:
        print(f"Error saving frame to {output_path}: {e}")

def generate_jwt(client_id, client_secret):
    iat = datetime.utcnow()
    exp = iat + timedelta(hours=24)
    payload = {
        "iat": iat,
        "exp": exp,
        "appKey": client_id,
        "tokenExp": int(exp.timestamp())
    }
    token = jwt.encode(payload, client_secret, algorithm="HS256")
    return token

def extract_meeting_info_from_url(meeting_url):
    """Extract meeting ID and password from Zoom URL"""
    try:
        parsed = urllib.parse.urlparse(meeting_url)
        
        # Extract meeting ID from path
        path_parts = parsed.path.split('/')
        meeting_id = None
        for part in path_parts:
            if part.isdigit():
                meeting_id = part
                break
        
        # Extract password from query parameters
        query_params = urllib.parse.parse_qs(parsed.query)
        password = query_params.get('pwd', [None])[0]
        
        return meeting_id, password
    except Exception as e:
        print(f"Error parsing meeting URL: {e}")
        return None, None

def fetch_meeting_from_api(api_base_url, api_key, user_id):
    """Fetch meeting information from the API"""
    try:
        url = f"{api_base_url}/api/user-meetings?userId={user_id}"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        print(f"Fetching meetings from: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 401:
            print("❌ Authentication failed. Check your API key.")
            return None
        elif response.status_code == 404:
            print("❌ User not found.")
            return None
        elif response.status_code != 200:
            print(f"❌ API error: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        meetings = data.get('meetings', [])
        
        if not meetings:
            print("❌ No meetings found for this user.")
            return None
        
        # Return the most recent meeting
        latest_meeting = meetings[0]  # Already sorted by createdAt desc
        print(f"✅ Found meeting: {latest_meeting.get('meetingId', 'Unknown')}")
        return latest_meeting
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error fetching meeting: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response from API: {e}")
        return None
    except Exception as e:
        print(f"❌ Error fetching meeting: {e}")
        return None

def normalized_rms_audio(pcm_data: bytes, sample_width: int = 2) -> bool:
    """Determine if PCM audio data contains significant audio or is essentially silence."""
    if len(pcm_data) == 0:
        return True
    import array
    samples = array.array('h')
    samples.frombytes(pcm_data)
    sum_squares = sum(sample * sample for sample in samples)
    rms = (sum_squares / len(samples)) ** 0.5
    normalized_rms = rms / 32767.0
    return normalized_rms

def create_red_yuv420_frame(width=640, height=360):
    bgr_frame = np.zeros((height, width, 3), dtype=np.uint8)
    bgr_frame[:, :] = [0, 0, 255]  # Pure red in BGR
    yuv_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2YUV_I420)
    return yuv_frame.tobytes()

class APIMeetingBot:
    def __init__(self):
        self.meeting_service = None
        self.setting_service = None
        self.auth_service = None
        self.auth_event = None
        self.recording_event = None
        self.meeting_service_event = None
        self.audio_source = None
        self.audio_helper = None
        self.audio_settings = None
        self.use_audio_recording = True
        self.use_video_recording = os.environ.get('RECORD_VIDEO') == 'true'
        self.video_frame_counter = 0
        self.video_sender = None
        self.transcriber = None
        
        # API configuration
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:3000')
        self.api_key = os.getenv('USER_MEETINGS_API_KEY')
        self.user_id = os.getenv('USER_ID')  # Will be set by orchestrator
        self.specific_meeting_id = os.getenv('MEETING_ID')  # Specific meeting to join
        
        # Meeting info (will be fetched from API)
        self.meeting_id = None
        self.meeting_password = None
        self.meeting_link = None

    def cleanup(self):
        print("CleanUPSDK() called")
        zoom.CleanUPSDK()
        print("CleanUPSDK() finished")

    def fetch_meeting_info(self):
        """Fetch meeting information from API instead of environment variables"""
        if not self.api_key:
            raise Exception('No USER_MEETINGS_API_KEY found in environment')
        if not self.user_id:
            raise Exception('No USER_ID found in environment')
        
        print(f"🔍 Fetching meeting info for user: {self.user_id}")
        
        # If we have a specific meeting ID, fetch that meeting
        if self.specific_meeting_id:
            meeting_data = self.fetch_specific_meeting()
        else:
            # Otherwise, fetch the most recent meeting
            meeting_data = fetch_meeting_from_api(self.api_base_url, self.api_key, self.user_id)
        
        if not meeting_data:
            raise Exception('Failed to fetch meeting data from API')
        
        self.meeting_link = meeting_data.get('link')
        if not self.meeting_link:
            raise Exception('No meeting link found in API response')
        
        # Extract meeting ID and password from the link
        self.meeting_id, self.meeting_password = extract_meeting_info_from_url(self.meeting_link)
        
        if not self.meeting_id:
            raise Exception('Could not extract meeting ID from link')
        if not self.meeting_password:
            raise Exception('Could not extract meeting password from link')
        
        print(f"✅ Meeting info fetched:")
        print(f"   Meeting ID: {self.meeting_id}")
        print(f"   Password: {self.meeting_password}")
        print(f"   Link: {self.meeting_link}")

    def fetch_specific_meeting(self):
        """Fetch a specific meeting by ID"""
        try:
            # Get all meetings for the user
            url = f"{self.api_base_url}/api/user-meetings?userId={self.user_id}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ API error: {response.status_code}")
                return None
            
            data = response.json()
            meetings = data.get('meetings', [])
            
            # Find the specific meeting
            for meeting in meetings:
                if meeting.get('id') == self.specific_meeting_id:
                    print(f"✅ Found specific meeting: {meeting.get('meetingId', 'Unknown')}")
                    return meeting
            
            print(f"❌ Meeting with ID {self.specific_meeting_id} not found")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching specific meeting: {e}")
            return None

    def init(self):
        # Fetch meeting info from API first
        self.fetch_meeting_info()
        
        # Check for Zoom credentials
        if os.environ.get('ZOOM_APP_CLIENT_ID') is None:
            raise Exception('No ZOOM_APP_CLIENT_ID found in environment')
        if os.environ.get('ZOOM_APP_CLIENT_SECRET') is None:
            raise Exception('No ZOOM_APP_CLIENT_SECRET found in environment')

        init_param = zoom.InitParam()
        init_param.strWebDomain = "https://zoom.us"
        init_param.strSupportUrl = "https://zoom.us"
        init_param.enableGenerateDump = True
        init_param.emLanguageID = zoom.SDK_LANGUAGE_ID.LANGUAGE_English
        init_param.enableLogByDefault = True

        init_sdk_result = zoom.InitSDK(init_param)
        if init_sdk_result != zoom.SDKERR_SUCCESS:
            raise Exception('InitSDK failed')

        self.create_services()

    def join_meeting(self):
        """Join meeting using data fetched from API"""
        if not self.meeting_id or not self.meeting_password:
            raise Exception('Meeting ID or password not available')
        
        display_name = "API Meeting Bot"
        meeting_number = int(self.meeting_id)

        join_param = zoom.JoinParam()
        join_param.userType = zoom.SDKUserType.SDK_UT_WITHOUT_LOGIN

        param = join_param.param
        param.meetingNumber = meeting_number
        param.userName = display_name
        param.psw = self.meeting_password
        param.isVideoOff = False
        param.isAudioOff = False
        param.isAudioRawDataStereo = False
        param.isMyVoiceInMix = False
        param.eAudioRawdataSamplingRate = zoom.AudioRawdataSamplingRate.AudioRawdataSamplingRate_32K

        join_result = self.meeting_service.Join(join_param)
        print("join_result =", join_result)

        self.audio_settings = self.setting_service.GetAudioSettings()
        self.audio_settings.EnableAutoJoinAudio(True)

    # ... rest of the methods remain the same as the original meeting_bot.py
    # (I'll include the key ones, but you can copy the rest from the original)

    def on_user_join_callback(self, joined_user_ids, user_name):
        print("on_user_join_callback called. joined_user_ids =", joined_user_ids, "user_name =", user_name)

    def on_chat_msg_notification_callback(self, chat_msg_info, content):
        print("\n=== on_chat_msg_notification called ===")
        print(f"Message ID: {chat_msg_info.GetMessageID()}")
        print(f"Sender ID: {chat_msg_info.GetSenderUserId()}")
        print(f"Sender Name: {chat_msg_info.GetSenderDisplayName()}")
        print(f"Content: {chat_msg_info.GetContent()}")
        print("=====================\n")

    def auth_return(self, result):
        if result == zoom.AUTHRET_SUCCESS:
            print("Auth completed successfully.")
            return self.join_meeting()
        raise Exception("Failed to authorize. result =", result)

    def meeting_status_changed(self, status, iResult):
        print("meeting_status_changed called. status =", status, "iResult=", iResult)
        if status == zoom.MEETING_STATUS_INMEETING:
            return self.on_join()

    def on_join(self):
        print("Successfully joined meeting!")
        # Add your meeting logic here

    def create_services(self):
        self.meeting_service = zoom.CreateMeetingService()
        self.setting_service = zoom.CreateSettingService()
        
        self.meeting_service_event = zoom.MeetingServiceEventCallbacks(
            onMeetingStatusChangedCallback=self.meeting_status_changed
        )
        
        meeting_service_set_revent_result = self.meeting_service.SetEvent(self.meeting_service_event)
        if meeting_service_set_revent_result != zoom.SDKERR_SUCCESS:
            raise Exception("Meeting Service set event failed")

        self.auth_event = zoom.AuthServiceEventCallbacks(
            onAuthenticationReturnCallback=self.auth_return
        )
        
        self.auth_service = zoom.CreateAuthService()
        set_event_result = self.auth_service.SetEvent(self.auth_event)
        print("set_event_result =", set_event_result)

        # Use the auth service
        auth_context = zoom.AuthContext()
        auth_context.jwt_token = generate_jwt(
            os.environ.get('ZOOM_APP_CLIENT_ID'), 
            os.environ.get('ZOOM_APP_CLIENT_SECRET')
        )

        result = self.auth_service.SDKAuth(auth_context)
        if result == zoom.SDKError.SDKERR_SUCCESS:
            print("Authentication successful")
        else:
            print("Authentication failed with error:", result)

    def leave(self):
        if self.meeting_service is None:
            return
        status = self.meeting_service.GetMeetingStatus()
        if status == zoom.MEETING_STATUS_IDLE:
            return
        self.meeting_service.Leave(zoom.LEAVE_MEETING)

def main():
    bot = APIMeetingBot()
    try:
        bot.init()
        # Keep the bot running
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down bot...")
        bot.leave()
        bot.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        bot.cleanup()

if __name__ == "__main__":
    main()
