# GitHub Setup & Deployment Guide

## Step 1: Create a GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the **+** icon in the top right → **New repository**
3. Fill in the details:
   - **Repository name**: `person-movement-tracker`
   - **Description**: `Real-time person detection and tracking system with AI`
   - **Privacy**: Choose Public or Private
   - **Do NOT initialize with README** (we already have files)
4. Click **Create repository**

## Step 2: Push Your Code to GitHub

Copy and paste these commands into PowerShell in your project directory:

```powershell
# Navigate to project folder
cd "C:\Users\AkshiLocal\Image_recog\person-movement-tracker"

# Add remote repository (replace YOUR_USERNAME and YOUR_REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/person-movement-tracker.git

# Rename branch to main (GitHub default)
git branch -M main

# Push code to GitHub
git push -u origin main
```

**Note**: You'll be prompted for credentials. You can use:
- Your GitHub username and password, OR
- A Personal Access Token (recommended)

### Getting a Personal Access Token:
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click **Generate new token (classic)**
3. Check `repo` scope
4. Copy the token and use it as your password

## Step 3: Configure Remote HTTPS (Optional but Recommended)

To avoid entering credentials every time:

```powershell
# Store credentials (one-time setup)
git credential fill
host=github.com
protocol=https
# Press Enter twice, then enter when prompted

# Or use GitHub CLI (if installed):
gh auth login
```

## Quick Reference Commands

```powershell
# Check remote
git remote -v

# Push changes
git push

# Pull changes
git pull

# View commit history
git log --oneline

# Create a new branch
git checkout -b feature/new-feature
```

---

# Using the New HTML UI

## Features

The standalone HTML/CSS/JavaScript UI provides:

- **Real-time Camera Feed** - Live video stream with detection overlays
- **Multiple Detection Models** - YOLOv8, DETR, YOLOS options
- **Live Tracking** - Track multiple persons in real-time
- **Performance Stats** - FPS, inference time, detection count
- **Image Upload** - Process single images for detection
- **Responsive Design** - Works on desktop, tablet, and mobile

## How to Use

### 1. Start the Backend Server

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will run at `http://localhost:8000`

### 2. Open the HTML UI

Option A: Direct File Access
```powershell
# Open in default browser
Invoke-Item "C:\Users\AkshiLocal\Image_recog\person-movement-tracker\html-ui\index.html"
```

Option B: Web Server (Recommended)
```powershell
# Use Python's built-in server
cd "C:\Users\AkshiLocal\Image_recog\person-movement-tracker\html-ui"
python -m http.server 8080
```

Then open: `http://localhost:8080`

### 3. Using the UI

1. **Select Detection Model**
   - **YOLOv8**: Fast, good for real-time
   - **DETR**: More accurate, slower
   - **YOLOS**: Balanced speed/accuracy

2. **Enable/Disable Tracking**
   - Toggle the "Enable Tracking" checkbox
   - When enabled, tracks multiple persons across frames

3. **Start Tracking**
   - Click **Start** button
   - Allow camera permissions when prompted
   - Watch real-time detection and tracking

4. **Upload Image**
   - Click file input to select an image
   - Processing happens automatically
   - Results display with detection count

5. **Monitor Performance**
   - **Persons Detected**: Current detection count
   - **Inference Time**: Time to process frame
   - **FPS**: Frames per second
   - **Active Tracks**: Number of tracked persons

## Advantages of HTML UI vs Node.js

✅ **No Build Process** - Open and use immediately
✅ **Lightweight** - No npm dependencies
✅ **Standalone** - Works offline (after loading)
✅ **Cross-Platform** - Same in any browser
✅ **Easy to Modify** - Edit HTML/CSS/JS directly
✅ **Better Performance** - Direct browser APIs
✅ **Simpler Deployment** - Single HTML file

## Troubleshooting

### "Connection refused" or "Failed to connect"
- Ensure backend server is running on port 8000
- Check: `http://localhost:8000/docs` should show API docs

### Camera Permission Error
- Allow the browser to access your camera
- Check browser settings → Privacy & Security → Camera

### Slow Inference
- Switch to YOLOv8 model (faster)
- Reduce video resolution
- Ensure GPU is available

### No Detection Results
- Ensure person is visible in frame
- Try different lighting conditions
- Check backend console for errors

## File Locations

```
C:\Users\AkshiLocal\Image_recog\person-movement-tracker\
├── html-ui/
│   └── index.html          ← Open this file in browser
├── backend/
│   ├── src/
│   │   └── main.py         ← Start backend here
│   └── requirements.txt
└── frontend/               ← (Optional) Old Node.js version
    ├── package.json
    └── src/
```

## Next Steps

1. **Push to GitHub** - Follow Step 2 above
2. **Customize UI** - Edit `html-ui/index.html`
3. **Deploy Backend** - Use Docker or manual setup
4. **Add Features** - Extend API or UI as needed

---

## Docker Deployment (Optional)

If you prefer Docker:

```bash
cd person-movement-tracker

# Build and run with Docker Compose
docker-compose up --build

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# HTML UI: Copy html-ui/index.html to web server
```

---

## Support & Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **API Endpoints**: http://localhost:8000/redoc
- **Project Docs**: See `/docs` folder in repository
