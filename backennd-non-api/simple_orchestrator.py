import requests
import os
import time
import subprocess
import json
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from the current directory where the orchestrator .env file is located
    load_dotenv('.env')
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Or set environment variables manually.")

class SimpleOrchestrator:
    def __init__(self):
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:3000')
        self.api_key = os.getenv('USER_MEETINGS_API_KEY')
        self.active_bots: Dict[str, subprocess.Popen] = {}
        self.running = True
        
        if not self.api_key:
            raise Exception("USER_MEETINGS_API_KEY environment variable is required")
        
        print("🎯 Simple Meeting Orchestrator initialized")
        print(f"📡 API Base URL: {self.api_base_url}")
        print(f"🔑 API Key: {self.api_key[:8]}...")

    def extract_meeting_credentials(self, meeting_link: str) -> tuple:
        """Extract meeting ID and password from Zoom URL"""
        try:
            parsed = urllib.parse.urlparse(meeting_link)
            
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

    def fetch_all_meetings(self) -> List[dict]:
        """Fetch all meetings from the API"""
        try:
            url = f"{self.api_base_url}/api/orchestrator/meetings"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ API error: {response.status_code}")
                return []
            
            data = response.json()
            meetings = data.get('meetings', [])
            
            print(f"📋 Fetched {len(meetings)} meetings from API")
            return meetings
            
        except Exception as e:
            print(f"❌ Error fetching meetings: {e}")
            return []

    def fetch_users_with_meetings(self) -> Dict[str, List[dict]]:
        """Fetch all users and their meetings from the API"""
        try:
            # First, get all meetings
            meetings = self.fetch_all_meetings()
            
            # Group meetings by user ID
            users_with_meetings = {}
            for meeting in meetings:
                user_id = meeting.get('userId')
                if user_id:
                    if user_id not in users_with_meetings:
                        users_with_meetings[user_id] = []
                    users_with_meetings[user_id].append(meeting)
            
            print(f"👥 Found {len(users_with_meetings)} users with meetings")
            return users_with_meetings
            
        except Exception as e:
            print(f"❌ Error fetching users with meetings: {e}")
            return {}

    def should_start_bot_for_meeting(self, meeting: dict) -> bool:
        """Check if we should start a bot for this meeting"""
        meeting_id = meeting.get('id')
        user_id = meeting.get('userId')
        
        # If bot already running for this meeting, don't start another
        if meeting_id in self.active_bots:
            return False
        
        # Check if we already have a bot running for this user
        for active_meeting_id, process in self.active_bots.items():
            # You could store user_id with each bot process for better tracking
            # For now, we'll assume one bot per user is sufficient
            pass
        
        # Check if meeting has a link
        if not meeting.get('link'):
            print(f"⚠️ Meeting {meeting_id} has no link, skipping")
            return False
        
        # Only start bot for the most recent meeting per user
        # (This is handled in the main loop by only passing the most recent meeting)
        
        return True

    def start_meeting_bot(self, meeting: dict, user_id: str):
        """Start a meeting bot for a specific meeting"""
        try:
            meeting_id = meeting.get('id')
            meeting_link = meeting.get('link')
            
            if not meeting_link:
                print(f"⚠️ Meeting {meeting_id} has no link, skipping")
                return
            
            print(f"🤖 Starting bot for meeting: {meeting.get('meetingId', 'Unknown')}")
            
            # Extract meeting credentials from the link
            zoom_meeting_id, zoom_password = self.extract_meeting_credentials(meeting_link)
            
            if not zoom_meeting_id or not zoom_password:
                print(f"❌ Could not extract meeting credentials from link: {meeting_link}")
                return
            
            print(f"🔑 Extracted credentials - Meeting ID: {zoom_meeting_id}, Password: {zoom_password}")
            
            # Set environment variables for the bot
            env = os.environ.copy()
            env['MEETING_ID'] = zoom_meeting_id
            env['MEETING_PWD'] = zoom_password
            
            # Add the src directory to Python path so it can find the zoom_meeting_sdk module
            current_pythonpath = env.get('PYTHONPATH', '')
            src_path = os.path.abspath('py-zoom-meeting-sdk-main/py-zoom-meeting-sdk-main/src')
            if current_pythonpath:
                env['PYTHONPATH'] = f"{src_path}:{current_pythonpath}"
            else:
                env['PYTHONPATH'] = src_path
            
            print(f"🔧 Environment variables for bot:")
            print(f"   MEETING_ID: {env.get('MEETING_ID')}")
            print(f"   MEETING_PWD: {env.get('MEETING_PWD')}")
            print(f"   ZOOM_APP_CLIENT_ID: {env.get('ZOOM_APP_CLIENT_ID')}")
            print(f"   ZOOM_APP_CLIENT_SECRET: {env.get('ZOOM_APP_CLIENT_SECRET')}")
            
            # Create .env file for the Docker container
            env_file_path = 'py-zoom-meeting-sdk-main/py-zoom-meeting-sdk-main/.env'
            with open(env_file_path, 'w') as f:
                f.write(f"ZOOM_APP_CLIENT_ID={env.get('ZOOM_APP_CLIENT_ID')}\n")
                f.write(f"ZOOM_APP_CLIENT_SECRET={env.get('ZOOM_APP_CLIENT_SECRET')}\n")
                f.write(f"MEETING_ID={env.get('MEETING_ID')}\n")
                f.write(f"MEETING_PWD={env.get('MEETING_PWD')}\n")
                f.write(f"DEEPGRAM_API_KEY=\n")  # Optional
            
            print(f"📝 Created .env file at: {env_file_path}")
            
            # Start the bot process using Docker (following documentation)
            # Install zoom-meeting-sdk and run the script in the same container
            docker_cmd = [
                'docker-compose', 'run', '--rm', 'develop',
                'bash', '-c', 'pip install zoom-meeting-sdk && python sample_program/sample.py'
            ]
            
            bot_process = subprocess.Popen(
                docker_cmd,
                cwd='py-zoom-meeting-sdk-main/py-zoom-meeting-sdk-main/',
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # Use text mode for easier debugging
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            self.active_bots[meeting_id] = bot_process
            print(f"✅ Started bot process (PID: {bot_process.pid}) for meeting {meeting_id}")
            
            # Start a thread to monitor bot output in real-time
            import threading
            def monitor_bot_output():
                while bot_process.poll() is None:
                    stdout_line = bot_process.stdout.readline()
                    if stdout_line:
                        print(f"🤖 BOT OUTPUT: {stdout_line.strip()}")
                    stderr_line = bot_process.stderr.readline()
                    if stderr_line:
                        print(f"🤖 BOT ERROR: {stderr_line.strip()}")
                
                # Process has finished, get any remaining output
                stdout, stderr = bot_process.communicate()
                if stdout:
                    print(f"🤖 FINAL STDOUT: {stdout}")
                if stderr:
                    print(f"🤖 FINAL STDERR: {stderr}")
            
            monitor_thread = threading.Thread(target=monitor_bot_output, daemon=True)
            monitor_thread.start()
            
            # Check if process started successfully
            time.sleep(2)  # Give it a moment to start
            if bot_process.poll() is not None:
                # Process has already exited
                print(f"❌ Bot process failed to start (exit code: {bot_process.returncode})")
                # Remove from active bots since it failed
                del self.active_bots[meeting_id]
            else:
                print(f"✅ Bot process is running successfully")
            
        except Exception as e:
            print(f"❌ Error starting bot for meeting {meeting_id}: {e}")

    def check_bot_status(self):
        """Check if any bots have stopped and clean them up"""
        stopped_bots = []
        
        for meeting_id, process in self.active_bots.items():
            if process.poll() is not None:  # Process has finished
                print(f"🤖 Bot for meeting {meeting_id} has stopped (exit code: {process.returncode})")
                stopped_bots.append(meeting_id)
        
        # Remove stopped bots from active list
        for meeting_id in stopped_bots:
            del self.active_bots[meeting_id]

    def run(self):
        """Main orchestrator loop"""
        print("🚀 Starting Simple Meeting Orchestrator...")
        
        while self.running:
            try:
                # Check for stopped bots
                self.check_bot_status()
                
                # Fetch all users and their meetings
                users_with_meetings = self.fetch_users_with_meetings()
                
                # Check each user's meetings - only start bot for the most recent meeting
                for user_id, user_meetings in users_with_meetings.items():
                    if user_meetings:  # If user has meetings
                        # Get the most recent meeting (first in the list since it's sorted by createdAt desc)
                        most_recent_meeting = user_meetings[0]
                        if self.should_start_bot_for_meeting(most_recent_meeting):
                            self.start_meeting_bot(most_recent_meeting, user_id)
                
                # Log current status
                print(f"📊 Active bots: {len(self.active_bots)}")
                print(f"👥 Monitoring {len(users_with_meetings)} users")
                
                # Sleep for 30 seconds before next check
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("🛑 Shutting down orchestrator...")
                break
            except Exception as e:
                print(f"❌ Error in orchestrator loop: {e}")
                time.sleep(30)

    def cleanup(self):
        """Clean up all running bots"""
        print("🧹 Cleaning up bots...")
        for meeting_id, process in self.active_bots.items():
            try:
                process.terminate()
                print(f"🛑 Terminated bot for meeting {meeting_id}")
            except Exception as e:
                print(f"❌ Error terminating bot for meeting {meeting_id}: {e}")

def main():
    orchestrator = SimpleOrchestrator()
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    finally:
        orchestrator.cleanup()

if __name__ == "__main__":
    main()
