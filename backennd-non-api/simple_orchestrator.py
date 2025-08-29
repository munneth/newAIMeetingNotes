import requests
import os
import time
import subprocess
import json
import urllib.parse
import signal
import sys
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
        self.active_bots: Dict[str, dict] = {}  # Changed to store bot info including start time and duration
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

    def is_meeting_time(self, meeting: dict) -> bool:
        """Check if it's time for the meeting to start"""
        try:
            # Use the startTime field from the meeting
            start_time_str = meeting.get('startTime')
            if not start_time_str:
                print(f"⚠️ No start time found for meeting {meeting.get('id')}")
                return False
            
            # Parse the start time (time-only format HH:MM:SS)
            try:
                # Parse time string (HH:MM:SS)
                time_parts = start_time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = int(time_parts[2]) if len(time_parts) > 2 else 0
                
                # Use today's date with the specified time
                current_date = datetime.now().date()
                start_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute, second=second))
            except (ValueError, IndexError) as e:
                print(f"❌ Invalid time format: {start_time_str}, error: {e}")
                return False
            
            current_time = datetime.now(start_time.tzinfo if start_time.tzinfo else None)
            
            # Allow joining 2 minutes before and 5 minutes after scheduled start time
            time_diff = (current_time - start_time).total_seconds()
            is_time = -120 <= time_diff <= 300  # 2 minutes before to 5 minutes after
            
            if is_time:
                if time_diff < 0:
                    print(f"✅ Meeting {meeting.get('id')} is starting soon (in {abs(time_diff):.0f} seconds)")
                else:
                    print(f"✅ Meeting {meeting.get('id')} started {time_diff/60:.1f} minutes ago")
            else:
                if time_diff < 0:
                    print(f"⏰ Meeting {meeting.get('id')} starts in {abs(time_diff)/60:.1f} minutes")
                else:
                    print(f"⏰ Meeting {meeting.get('id')} started {time_diff/60:.1f} minutes ago (too late)")
            
            return is_time
            
        except Exception as e:
            print(f"❌ Error checking meeting time: {e}")
            import traceback
            traceback.print_exc()
            return False

    def should_bot_leave(self, meeting_id: str) -> bool:
        """Check if bot should leave based on duration"""
        if meeting_id not in self.active_bots:
            return False
        
        bot_info = self.active_bots[meeting_id]
        start_time = bot_info['start_time']
        duration_minutes = bot_info['duration_minutes']
        
        current_time = datetime.now()
        elapsed_minutes = (current_time - start_time).total_seconds() / 60
        
        should_leave = elapsed_minutes >= duration_minutes
        
        if should_leave:
            print(f"⏰ Bot for meeting {meeting_id} has been running for {elapsed_minutes:.1f} minutes, duration {duration_minutes} minutes reached")
        
        return should_leave

    def cleanup_bot(self, meeting_id: str):
        """Properly cleanup a bot instance"""
        if meeting_id not in self.active_bots:
            return
        
        bot_info = self.active_bots[meeting_id]
        process = bot_info['process']
        
        try:
            print(f"🧹 Cleaning up bot for meeting {meeting_id}")
            
            # Send SIGTERM to gracefully shutdown
            process.terminate()
            
            # Wait up to 10 seconds for graceful shutdown
            try:
                process.wait(timeout=10)
                print(f"✅ Bot for meeting {meeting_id} terminated gracefully")
            except subprocess.TimeoutExpired:
                print(f"⚠️ Bot for meeting {meeting_id} didn't terminate gracefully, forcing kill")
                process.kill()
                process.wait()
            
            # Remove from active bots
            del self.active_bots[meeting_id]
            print(f"✅ Bot for meeting {meeting_id} cleaned up successfully")
            
        except Exception as e:
            print(f"❌ Error cleaning up bot for meeting {meeting_id}: {e}")
            # Force remove from active bots even if cleanup fails
            if meeting_id in self.active_bots:
                del self.active_bots[meeting_id]

    def should_start_bot_for_meeting(self, meeting: dict) -> bool:
        """Check if we should start a bot for this meeting"""
        meeting_id = meeting.get('id')
        user_id = meeting.get('userId')
        
        # If bot already running for this meeting, don't start another
        if meeting_id in self.active_bots:
            bot_info = self.active_bots[meeting_id]
            process = bot_info['process']
            if process.poll() is None:  # Process is still running
                print(f"🤖 Bot already running for meeting {meeting_id} (PID: {process.pid})")
                return False
            else:
                print(f"🤖 Bot process for meeting {meeting_id} has stopped, will cleanup")
                self.cleanup_bot(meeting_id)
        
        # Check if we already have a bot running for this user
        for active_meeting_id, bot_info in self.active_bots.items():
            if bot_info.get('user_id') == user_id:
                print(f"🤖 Bot already running for user {user_id}")
                return False
        
        # Check if meeting has a link
        if not meeting.get('link'):
            print(f"⚠️ Meeting {meeting_id} has no link, skipping")
            return False
        
        # Check if it's time for the meeting
        if not self.is_meeting_time(meeting):
            return False
        
        print(f"✅ Meeting {meeting_id} is ready for bot to join")
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
            
            # Store bot information including start time and duration
            duration_minutes = int(meeting.get('duration', 30))  # Default to 30 minutes
            bot_info = {
                'process': bot_process,
                'user_id': user_id,
                'start_time': datetime.now(),
                'duration_minutes': duration_minutes,
                'meeting_id': meeting_id
            }
            
            self.active_bots[meeting_id] = bot_info
            print(f"✅ Started bot process (PID: {bot_process.pid}) for meeting {meeting_id}, duration: {duration_minutes} minutes")
            
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
                if meeting_id in self.active_bots:
                    del self.active_bots[meeting_id]
            else:
                print(f"✅ Bot process is running successfully")
                # Add a small delay to ensure the bot is fully started before continuing
                time.sleep(1)
            
        except Exception as e:
            print(f"❌ Error starting bot for meeting {meeting_id}: {e}")

    def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        print("🛑 Shutting down orchestrator...")
        self.running = False
        
        # Cleanup all active bots
        print("🧹 Cleaning up bots...")
        for meeting_id in list(self.active_bots.keys()):
            self.cleanup_bot(meeting_id)
        
        print("✅ Orchestrator shutdown complete")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)

    def check_bot_status(self):
        """Check if any bots have stopped or should leave based on duration"""
        bots_to_cleanup = []
        
        for meeting_id, bot_info in self.active_bots.items():
            process = bot_info['process']
            
            # Check if process has stopped unexpectedly
            if process.poll() is not None:
                print(f"🤖 Bot for meeting {meeting_id} has stopped unexpectedly (exit code: {process.returncode})")
                bots_to_cleanup.append(meeting_id)
                continue
            
            # Check if bot should leave based on duration
            if self.should_bot_leave(meeting_id):
                print(f"⏰ Bot for meeting {meeting_id} has reached its duration limit, cleaning up")
                bots_to_cleanup.append(meeting_id)
        
        # Clean up bots that need to be removed
        for meeting_id in bots_to_cleanup:
            self.cleanup_bot(meeting_id)

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
                for meeting_id, bot_info in self.active_bots.items():
                    elapsed_minutes = (datetime.now() - bot_info['start_time']).total_seconds() / 60
                    remaining = bot_info['duration_minutes'] - elapsed_minutes
                    print(f"   🤖 Meeting {meeting_id}: {elapsed_minutes:.1f}/{bot_info['duration_minutes']} minutes ({remaining:.1f} remaining)")
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
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, orchestrator.signal_handler)
    signal.signal(signal.SIGTERM, orchestrator.signal_handler)
    
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    finally:
        orchestrator.shutdown()

if __name__ == "__main__":
    main()
