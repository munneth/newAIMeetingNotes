#!/bin/bash
set -e

REGISTRY=yourdockerhubusername/meetbot

echo "Building orchestrator image..."
docker build -t $REGISTRY-orchestrator:latest orchestrator/

echo "Building worker image..."
docker build -t $REGISTRY-worker:latest worker/

echo "Pushing images..."
docker push $REGISTRY-orchestrator:latest
docker push $REGISTRY-worker:latest

echo "Applying k8s manifests..."
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/orchestrator-deployment.yaml
kubectl apply -f k8s/meet-bot-job.yaml

echo "Deployment complete."
