@echo off
REM Start HTML UI Server
REM This script starts a simple HTTP server to serve the HTML UI

cd /d "%~dp0html-ui"

echo.
echo ========================================
echo Person Movement Tracker - HTML UI
echo ========================================
echo.
echo Starting HTTP server on port 8080...
echo.
echo Open your browser to: http://localhost:8080
echo.
echo Press Ctrl+C to stop the server.
echo.
echo ========================================
echo.

python -m http.server 8080
