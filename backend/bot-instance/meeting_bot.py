import os
import json
import time
import logging
import requests
import redis
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeetingBot:
    def __init__(self):
        # Get environment variables from Kubernetes
        self.user_id = os.getenv("USER_ID")
        self.meeting_id = os.getenv("MEETING_ID")
        self.instance_id = os.getenv("INSTANCE_ID")
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:3000")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Zoom SDK credentials (essential for joining meetings)
        self.zoom_client_id = os.getenv("ZOOM_APP_CLIENT_ID")
        self.zoom_client_secret = os.getenv("ZOOM_APP_CLIENT_SECRET")
        self.zoom_jwt_token = os.getenv("ZOOM_JWT_TOKEN")
        
        # Meeting credentials
        self.meeting_password = os.getenv("MEETING_PASSWORD")
        self.display_name = os.getenv("DISPLAY_NAME", "MeetingBot")
        
        # Parse meeting data
        meeting_data_str = os.getenv("MEETING_DATA", "{}")
        self.meeting_data = json.loads(meeting_data_str)
        
        # Initialize Redis connection
        self.redis_client = redis.from_url(self.redis_url)
        
        # Bot state
        self.is_running = False
        self.meeting_started = False
        self.meeting_ended = False
        
        logger.info(f"Bot instance initialized: {self.instance_id}")
        logger.info(f"User: {self.user_id}, Meeting: {self.meeting_id}")
    
    def start(self):
        """Start the bot instance"""
        self.is_running = True
        logger.info(f"Starting bot instance {self.instance_id}")
        
        try:
            # Main bot loop
            while self.is_running:
                current_time = datetime.now()
                meeting_time = datetime.fromisoformat(self.meeting_data.get("start_time", "").replace("Z", "+00:00"))
                
                # Check if it's time to join the meeting
                if not self.meeting_started and current_time >= meeting_time - timedelta(minutes=5):
                    self.join_meeting()
                
                # Check if meeting has started
                if not self.meeting_started and current_time >= meeting_time:
                    self.meeting_started = True
                    self.on_meeting_start()
                
                # Check if meeting has ended
                duration_minutes = int(self.meeting_data.get("duration", "60"))
                meeting_end_time = meeting_time + timedelta(minutes=duration_minutes)
                
                if self.meeting_started and not self.meeting_ended and current_time >= meeting_end_time:
                    self.meeting_ended = True
                    self.on_meeting_end()
                    break
                
                # Sleep for a bit
                time.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            logger.error(f"Error in bot instance {self.instance_id}: {str(e)}")
        finally:
            self.cleanup()
    
    def join_meeting(self):
        """Join the meeting using Zoom SDK"""
        try:
            meeting_link = self.meeting_data.get("link")
            meeting_id = self.meeting_data.get("meetingId")
            password = self.meeting_data.get("password", "")
            
            logger.info(f"Joining meeting: {meeting_link}")
            logger.info(f"Meeting ID: {meeting_id}, Password: {password}")
            
            # Check if we have the required Zoom credentials
            if not all([self.zoom_client_id, self.zoom_client_secret]):
                logger.error("Missing Zoom credentials - cannot join meeting")
                self.log_action("join_failed", {
                    "reason": "missing_zoom_credentials",
                    "meeting_link": meeting_link,
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            # Here you would implement the actual Zoom SDK joining logic
            # Similar to your original test_join_meeting.py script
            # For now, log that we have the credentials and would join
            self.log_action("joining_meeting", {
                "meeting_link": meeting_link,
                "meeting_id": meeting_id,
                "has_password": bool(password),
                "timestamp": datetime.now().isoformat()
            })
            
            # TODO: Implement actual Zoom SDK joining
            # This would use the zoom_meeting_sdk like your original script
            
        except Exception as e:
            logger.error(f"Failed to join meeting: {str(e)}")
            self.log_action("join_failed", {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def on_meeting_start(self):
        """Called when meeting starts"""
        logger.info(f"Meeting started for {self.instance_id}")
        
        # Start monitoring the meeting
        self.start_meeting_monitoring()
        
        self.log_action("meeting_started", {
            "timestamp": datetime.now().isoformat()
        })
    
    def on_meeting_end(self):
        """Called when meeting ends"""
        logger.info(f"Meeting ended for {self.instance_id}")
        
        # Stop monitoring
        self.stop_meeting_monitoring()
        
        # Generate meeting summary
        self.generate_meeting_summary()
        
        self.log_action("meeting_ended", {
            "timestamp": datetime.now().isoformat()
        })
    
    def start_meeting_monitoring(self):
        """Start monitoring the meeting"""
        logger.info(f"Starting meeting monitoring for {self.instance_id}")
        
        # Start monitoring in a separate thread
        self.monitoring_thread = threading.Thread(target=self.monitor_meeting)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def stop_meeting_monitoring(self):
        """Stop monitoring the meeting"""
        logger.info(f"Stopping meeting monitoring for {self.instance_id}")
        # The monitoring thread will stop when the main loop ends
    
    def monitor_meeting(self):
        """Monitor the meeting (runs in separate thread)"""
        try:
            while self.meeting_started and not self.meeting_ended:
                # Here you would implement meeting monitoring logic
                # - Check if meeting is still active
                # - Monitor participants
                # - Record audio/video if needed
                # - Take notes
                
                # For now, just log that we're monitoring
                logger.debug(f"Monitoring meeting {self.meeting_id}")
                
                time.sleep(60)  # Check every minute
                
        except Exception as e:
            logger.error(f"Error monitoring meeting: {str(e)}")
    
    def generate_meeting_summary(self):
        """Generate summary after meeting ends"""
        try:
            logger.info(f"Generating meeting summary for {self.instance_id}")
            
            # Here you would implement summary generation
            # - Process recorded audio/video
            # - Generate transcript
            # - Create action items
            # - Send summary to user
            
            summary = {
                "meeting_id": self.meeting_id,
                "user_id": self.user_id,
                "duration": self.meeting_data.get("duration"),
                "participants": [],  # Would be populated during monitoring
                "action_items": [],
                "summary": "Meeting completed successfully",
                "generated_at": datetime.now().isoformat()
            }
            
            # Send summary to API
            self.send_summary_to_api(summary)
            
        except Exception as e:
            logger.error(f"Failed to generate meeting summary: {str(e)}")
    
    def send_summary_to_api(self, summary: Dict):
        """Send meeting summary to the API"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/meetings/{self.meeting_id}/summary",
                json=summary,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"Summary sent successfully for {self.meeting_id}")
            else:
                logger.error(f"Failed to send summary: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending summary to API: {str(e)}")
    
    def log_action(self, action: str, data: Dict):
        """Log bot actions"""
        log_entry = {
            "instance_id": self.instance_id,
            "user_id": self.user_id,
            "meeting_id": self.meeting_id,
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in Redis for monitoring
        self.redis_client.lpush(f"bot_logs:{self.instance_id}", json.dumps(log_entry))
        
        # Also log to console
        logger.info(f"Action: {action} - {json.dumps(data)}")
    
    def cleanup(self):
        """Clean up resources"""
        logger.info(f"Cleaning up bot instance {self.instance_id}")
        
        # Mark instance as completed in Redis
        self.redis_client.setex(
            f"bot_completed:{self.instance_id}",
            3600,  # Expire in 1 hour
            json.dumps({
                "completed_at": datetime.now().isoformat(),
                "user_id": self.user_id,
                "meeting_id": self.meeting_id
            })
        )
        
        # The pod will be automatically cleaned up by Kubernetes
        self.is_running = False

def main():
    """Main entry point for the bot instance"""
    bot = MeetingBot()
    bot.start()

if __name__ == "__main__":
    main()
