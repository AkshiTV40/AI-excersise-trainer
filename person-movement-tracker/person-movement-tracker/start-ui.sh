#!/bin/bash
# Start HTML UI Server
# This script starts a simple HTTP server to serve the HTML UI

cd "$(dirname "$0")/html-ui"

echo ""
echo "========================================"
echo "Person Movement Tracker - HTML UI"
echo "========================================"
echo ""
echo "Starting HTTP server on port 8080..."
echo ""
echo "Open your browser to: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""
echo "========================================"
echo ""

python -m http.server 8080
