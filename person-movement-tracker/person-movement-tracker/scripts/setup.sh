#!/bin/bash

echo "Setting up Person Movement Tracker..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Create virtual environment for backend
echo "Creating Python virtual environment..."
cd backend
python3 -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix/Mac
    source venv/bin/activate
fi

# Install backend dependencies
echo "Installing backend dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download models
echo "Downloading AI models..."
cd ..
python scripts/download_models.py

# Setup frontend
echo "Setting up frontend..."
cd frontend
npm install

# Create data directories
echo "Creating data directories..."
cd ..
mkdir -p data/{uploads,sessions,exports}

echo ""
echo "Setup complete!"
echo ""
echo "To start the backend:"
echo "  cd backend && source venv/bin/activate && uvicorn src.main:app --reload"
echo ""
echo "To start the frontend:"
echo "  cd frontend && npm run dev"
echo ""
echo "Or use Docker Compose:"
echo "  docker-compose up --build"