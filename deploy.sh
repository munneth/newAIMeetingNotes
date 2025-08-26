#!/bin/bash

echo "🚀 Deploying Meeting Bot System to Kubernetes..."

# Build Docker images
echo "📦 Building Docker images..."

# Build bot orchestrator
cd backend/bot-orchestrator
docker build -t bot-orchestrator:latest .
cd ../..

# Build bot instance
cd backend/bot-instance
docker build -t meeting-bot:latest .
cd ../..

# Deploy to Kubernetes
echo "☸️  Deploying to Kubernetes..."

# Create namespace
kubectl create namespace meeting-bot --dry-run=client -o yaml | kubectl apply -f -

# Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml

# Deploy bot orchestrator
kubectl apply -f k8s/bot-orchestrator-deployment.yaml

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
kubectl wait --for=condition=ready pod -l app=redis --timeout=300s
kubectl wait --for=condition=ready pod -l app=bot-orchestrator --timeout=300s

echo "✅ Deployment complete!"
echo ""
echo "📊 Check status with:"
echo "   kubectl get pods"
echo "   kubectl get services"
echo ""
echo "📝 View logs with:"
echo "   kubectl logs -l app=bot-orchestrator"
echo "   kubectl logs -l app=redis"
