#!/bin/bash
# Start a local Redis server in a Docker container

REDIS_CONTAINER_NAME="meetbot-redis"

# Check if container already running
if [ "$(docker ps -q -f name=$REDIS_CONTAINER_NAME)" ]; then
    echo "Redis container already running."
else
    echo "Starting Redis container..."
    docker run -d --name $REDIS_CONTAINER_NAME -p 6379:6379 redis:7-alpine
fi

echo "Redis is running at redis://localhost:6379"
