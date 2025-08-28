import kubernetes
from kubernetes import client, config
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotOrchestrator:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        # Load Kubernetes config
        try:
            config.load_incluster_config()  # For running inside K8s
        except:
            config.load_kube_config()  # For local development
        
        # Initialize Kubernetes clients
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        
        # Initialize Redis for task queue
        self.redis_client = redis.from_url(redis_url)
        
        # Track active bot instances
        self.active_instances: Dict[str, Dict] = {}
    
    def create_bot_instance(self, user_id: str, meeting_id: str, meeting_data: Dict) -> str:
        """Create a new bot instance for a specific meeting"""
        instance_id = f"bot-{user_id}-{meeting_id}"
        
        try:
            # Create Kubernetes pod for this meeting
            pod = client.V1Pod(
                metadata=client.V1ObjectMeta(
                    name=instance_id,
                    labels={
                        "app": "meeting-bot",
                        "user": user_id,
                        "meeting": meeting_id,
                        "instance-type": "meeting-bot"
                    }
                ),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="meeting-bot",
                            image="meeting-bot:latest",  # Your bot Docker image
                            env=[
                                client.V1EnvVar(name="USER_ID", value=user_id),
                                client.V1EnvVar(name="MEETING_ID", value=meeting_id),
                                client.V1EnvVar(name="MEETING_DATA", value=json.dumps(meeting_data)),
                                client.V1EnvVar(name="INSTANCE_ID", value=instance_id),
                                client.V1EnvVar(name="API_BASE_URL", value="http://api-service:3000"),
                                client.V1EnvVar(name="REDIS_URL", value="redis://redis-service:6379"),
                                # Zoom SDK credentials (essential for joining meetings)
                                client.V1EnvVar(name="ZOOM_APP_CLIENT_ID", value=os.getenv("ZOOM_APP_CLIENT_ID", "")),
                                client.V1EnvVar(name="ZOOM_APP_CLIENT_SECRET", value=os.getenv("ZOOM_APP_CLIENT_SECRET", "")),
                                client.V1EnvVar(name="ZOOM_JWT_TOKEN", value=os.getenv("ZOOM_JWT_TOKEN", "")),
                                # Meeting credentials
                                client.V1EnvVar(name="MEETING_PASSWORD", value=meeting_data.get("password", "")),
                                client.V1EnvVar(name="DISPLAY_NAME", value=f"Bot-{user_id}"),
                            ],
                            resources=client.V1ResourceRequirements(
                                requests={
                                    "cpu": "100m",
                                    "memory": "128Mi"
                                },
                                limits={
                                    "cpu": "500m",
                                    "memory": "512Mi"
                                }
                            ),
                            image_pull_policy="Always"
                        )
                    ],
                    restart_policy="Never",
                    termination_grace_period_seconds=30
                )
            )
            
            # Deploy the pod
            created_pod = self.core_v1.create_namespaced_pod("default", pod)
            
            # Track the instance
            self.active_instances[instance_id] = {
                "user_id": user_id,
                "meeting_id": meeting_id,
                "pod_name": instance_id,
                "created_at": datetime.now(),
                "status": "creating"
            }
            
            logger.info(f"Created bot instance {instance_id} for user {user_id}, meeting {meeting_id}")
            return instance_id
            
        except Exception as e:
            logger.error(f"Failed to create bot instance {instance_id}: {str(e)}")
            raise
    
    def destroy_bot_instance(self, instance_id: str) -> bool:
        """Destroy a bot instance"""
        try:
            # Delete the pod
            self.core_v1.delete_namespaced_pod(
                name=instance_id,
                namespace="default"
            )
            
            # Remove from tracking
            if instance_id in self.active_instances:
                del self.active_instances[instance_id]
            
            logger.info(f"Destroyed bot instance {instance_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to destroy bot instance {instance_id}: {str(e)}")
            return False
    
    def get_bot_status(self, instance_id: str) -> Optional[Dict]:
        """Get status of a bot instance"""
        try:
            pod = self.core_v1.read_namespaced_pod(
                name=instance_id,
                namespace="default"
            )
            
            return {
                "instance_id": instance_id,
                "status": pod.status.phase,
                "pod_ip": pod.status.pod_ip,
                "created_at": pod.metadata.creation_timestamp,
                "user_id": self.active_instances.get(instance_id, {}).get("user_id"),
                "meeting_id": self.active_instances.get(instance_id, {}).get("meeting_id")
            }
            
        except Exception as e:
            logger.error(f"Failed to get status for {instance_id}: {str(e)}")
            return None
    
    def list_active_instances(self) -> Dict[str, Dict]:
        """List all active bot instances"""
        return self.active_instances.copy()
    
    def cleanup_expired_instances(self, max_age_hours: int = 24):
        """Clean up bot instances that have been running too long"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        instances_to_cleanup = []
        for instance_id, instance_data in self.active_instances.items():
            if instance_data["created_at"] < cutoff_time:
                instances_to_cleanup.append(instance_id)
        
        for instance_id in instances_to_cleanup:
            logger.info(f"Cleaning up expired instance {instance_id}")
            self.destroy_bot_instance(instance_id)
    
    def scale_based_on_queue(self):
        """Scale bot instances based on queue size"""
        queue_size = self.redis_client.llen("meeting_tasks")
        
        if queue_size > 100:  # High load
            logger.info(f"High queue load detected: {queue_size} tasks")
            # Could implement auto-scaling logic here
        
        return queue_size

# Example usage
if __name__ == "__main__":
    import threading
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    orchestrator = BotOrchestrator()
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy"})
    
    @app.route('/ready')
    def ready():
        return jsonify({"status": "ready"})
    
    @app.route('/create-instance', methods=['POST'])
    def create_instance():
        try:
            data = request.json
            instance_id = orchestrator.create_bot_instance(
                user_id=data['user_id'],
                meeting_id=data['meeting_id'],
                meeting_data=data['meeting_data']
            )
            return jsonify({"success": True, "instance_id": instance_id})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/user-instances/<user_id>')
    def get_user_instances(user_id):
        try:
            instances = orchestrator.list_active_instances()
            user_instances = {k: v for k, v in instances.items() if v.get('user_id') == user_id}
            return jsonify(user_instances)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    print("Bot Orchestrator started successfully!")
    print("Web server running on port 8080...")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=8080)
