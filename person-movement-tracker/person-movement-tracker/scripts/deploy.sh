#!/bin/bash

# Deployment script for Person Movement Tracker

set -e

echo "Deploying Person Movement Tracker..."

# Configuration
BACKEND_IMAGE="person-tracker-backend"
FRONTEND_IMAGE="person-tracker-frontend"
VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "latest")

# Function to deploy with Docker Compose
deploy_docker() {
    echo "Building and deploying with Docker Compose..."
    
    # Build images
    docker-compose build
    
    # Start services
    docker-compose up -d
    
    echo "Deployment complete!"
    echo "Backend: http://localhost:8000"
    echo "Frontend: http://localhost:3000"
}

# Function to deploy to production
deploy_production() {
    echo "Deploying to production..."
    
    # Build production images
    docker build -t $BACKEND_IMAGE:$VERSION ./backend
    docker build -t $FRONTEND_IMAGE:$VERSION ./frontend
    
    # Tag for registry (if using)
    # docker tag $BACKEND_IMAGE:$VERSION your-registry/$BACKEND_IMAGE:$VERSION
    # docker tag $FRONTEND_IMAGE:$VERSION your-registry/$FRONTEND_IMAGE:$VERSION
    
    # Push to registry (if using)
    # docker push your-registry/$BACKEND_IMAGE:$VERSION
    # docker push your-registry/$FRONTEND_IMAGE:$VERSION
    
    echo "Production images built: $VERSION"
}

# Function to deploy to HuggingFace Spaces
deploy_huggingface() {
    echo "Deploying to HuggingFace Spaces..."
    
    # Check if huggingface-cli is installed
    if ! command -v huggingface-cli &> /dev/null; then
        echo "huggingface-cli not found. Installing..."
        pip install huggingface-hub
    fi
    
    # Login to HuggingFace
    huggingface-cli login
    
    # Create space (if not exists)
    # huggingface-cli repo create person-movement-tracker --type space
    
    # Push to space
    git push origin main
    
    echo "Deployed to HuggingFace Spaces!"
}

# Parse command line arguments
case "${1:-docker}" in
    docker)
        deploy_docker
        ;;
    production)
        deploy_production
        ;;
    huggingface)
        deploy_huggingface
        ;;
    *)
        echo "Usage: $0 {docker|production|huggingface}"
        exit 1
        ;;
esac