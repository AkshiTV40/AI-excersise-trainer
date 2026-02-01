# 🎯 Getting Started - Visual Guide

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your Browser                                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              HTML/CSS/JS UI (localhost:8080)              │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │     Webcam Feed + Detection Overlays                 │ │ │
│  │  │     Real-time Tracking Visualization                 │ │ │
│  │  │     Performance Stats (FPS, Inference Time)          │ │ │
│  │  │     Model Selection & Controls                       │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────┬──────────────────────────────────────────────┘
                  │ HTTP/JSON
                  │ ws://localhost:8000
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              Python FastAPI Backend (localhost:8000)             │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  YOLOv8 │ DETR │ YOLOS Detection Models (GPU/CPU)       │ │
│  │  DeepSORT Multi-Object Tracking                           │ │
│  │  Frame Processing & Analysis                             │ │
│  │  WebSocket Real-time Communication                       │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start in 3 Steps

### Step 1️⃣: Start Backend
```powershell
cd C:\Users\AkshiLocal\Image_recog\person-movement-tracker
.\start-backend.bat
```

**Wait for:**
```
Uvicorn running on http://127.0.0.1:8000
Application startup complete
```

### Step 2️⃣: Start UI (New PowerShell)
```powershell
cd C:\Users\AkshiLocal\Image_recog\person-movement-tracker
.\start-ui.bat
```

**Wait for:**
```
Serving HTTP on 0.0.0.0 port 8080
```

### Step 3️⃣: Open Browser
```
http://localhost:8080
```

**Browser should show the tracking application!**

---

## 🎨 UI Walkthrough

```
╔═══════════════════════════════════════════════════════════════╗
║  👁️  Person Movement Tracker          🟢 Camera Active        ║
╚═══════════════════════════════════════════════════════════════╝

┌────────────────────────────────────┐  ┌──────────────────────┐
│                                    │  │  Controls            │
│     WEBCAM FEED WITH              │  │  ┌────────────────┐  │
│     DETECTION BOXES               │  │  │ Model: YOLOv8  │  │
│                                    │  │ ┌────────────────┐  │
│     Real-time detections          │  │ │☑ Enable Track │  │
│     Bounding boxes & IDs          │  │ ┌────────────────┐  │
│                                    │  │ │ [Start] [Stop] │  │
│                                    │  │ ┌────────────────┐  │
│                                    │  │ │ Upload Image   │  │
│                                    │  │ └────────────────┘  │
├────────────────────────────────────┤  │                     │
│ Persons: 3  |  Inference: 25ms    │  │ Performance         │
│ FPS: 30     |  Time: 2023-01-31   │  │ ┌────────────────┐  │
└────────────────────────────────────┘  │ Active: 3      │  │
                                        │ Frames: 450    │  │
                                        │ Inference: 25ms│  │
                                        │ Status: Connected│  │
                                        └────────────────┘  │
                                        │                     │
                                        │ Active Tracks       │
                                        │ ┌────────────────┐  │
                                        │ │ Track #1 (85%)│  │
                                        │ │ Track #2 (92%)│  │
                                        │ │ Track #3 (78%)│  │
                                        │ └────────────────┘  │
                                        └──────────────────────┘
```

---

## 🔧 Windows File Navigation

### Open File Explorer
```
Press: Windows Key + E
Navigate to: C:\Users\AkshiLocal\Image_recog\person-movement-tracker
```

### File Locations
```
person-movement-tracker\
│
├─ 📄 README.md              ← Overview
├─ 📄 QUICKSTART.md          ← Start here!
├─ 📄 GITHUB_SETUP.md        ← GitHub upload
├─ 📄 SETUP_COMPLETE.md      ← This summary
│
├─ 🐍 start-backend.bat      ← Double-click to run
├─ 🌐 start-ui.bat           ← Double-click to run
│
├─ html-ui\
│  └─ 📄 index.html          ← Open in browser
│
└─ backend\
   └─ 📄 requirements.txt     ← Dependencies
```

---

## 🌐 Upload to GitHub

### 1️⃣ Create Repo on GitHub
Go to: https://github.com/new

Fill in:
- **Repository name**: `person-movement-tracker`
- **Description**: `Real-time person detection and tracking with AI`
- **Public/Private**: Choose one
- **DO NOT** check "Initialize with README"

### 2️⃣ Copy Command from GitHub
After creating repo, GitHub shows:
```
git remote add origin https://github.com/YOUR_USERNAME/person-movement-tracker.git
git branch -M main
git push -u origin main
```

### 3️⃣ Run Commands in PowerShell
```powershell
cd "C:\Users\AkshiLocal\Image_recog\person-movement-tracker"

# Paste the commands GitHub gave you
git remote add origin https://github.com/YOUR_USERNAME/person-movement-tracker.git
git branch -M main
git push -u origin main

# Enter your GitHub username and password (or token)
```

### 4️⃣ ✅ Done!
Your code is now on GitHub! Visit: https://github.com/YOUR_USERNAME/person-movement-tracker

---

## 📱 Test on Mobile

### Option 1: Same Network (Recommended)
1. Find your computer's IP:
```powershell
ipconfig
# Look for "IPv4 Address" (e.g., 192.168.x.x)
```

2. On mobile, open:
```
http://192.168.x.x:8080
```

### Option 2: USB Cable
```
Use tunneling tool like ngrok
```

---

## 🎯 Features to Try

### Detection Models
```
YOLOv8  → Fastest (~20ms)      ⚡⚡⚡
YOLOS   → Balanced (~50ms)      ⚡⚡
DETR    → Most Accurate (~100ms) ⚡
```

### Test Cases
1. **Live Camera** - Click "Start"
2. **Single Person** - One person in frame
3. **Multiple People** - 3+ people
4. **Image Upload** - Select an image file
5. **Different Models** - Try each one
6. **Low Light** - Test in dark room
7. **Fast Movement** - Walk around quickly

---

## ✅ Verification Checklist

```
Backend Server:
☐ Runs without errors
☐ Shows "Application startup complete"
☐ http://localhost:8000 is accessible
☐ http://localhost:8000/docs shows API docs

UI Server:
☐ Starts without errors
☐ Shows "Serving HTTP on 0.0.0.0 port 8080"
☐ Browser opens to http://localhost:8080
☐ UI is fully loaded and responsive

UI Functionality:
☐ Model dropdown is visible
☐ Start button is clickable
☐ Camera permission prompt appears
☐ Video feed shows
☐ Detection boxes appear
☐ Stats update in real-time
☐ FPS counter works
☐ Image upload works

GitHub:
☐ Repository created on GitHub
☐ Files pushed successfully
☐ Can see all files on GitHub.com
☐ README.md displays correctly
```

---

## 🆘 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| **"Port 8000 already in use"** | Close other apps or change port in script |
| **"Python not found"** | Install Python 3.8+ from python.org |
| **"Camera permission denied"** | Browser settings → Privacy → Allow Camera |
| **"Cannot find module..."** | Run: `pip install -r requirements.txt` |
| **"Slow inference time"** | Switch to YOLOv8 model |
| **"No detections appearing"** | Ensure good lighting, ensure person is visible |

---

## 📞 Getting Help

### Resources
- **API Docs**: http://localhost:8000/docs
- **Project Docs**: See `README.md`
- **Deployment**: See `docs/DEPLOYMENT.md`

### Common Commands
```powershell
# Check git status
git status

# View recent commits
git log --oneline -10

# See all branches
git branch -a

# Check network connection
Test-NetConnection localhost -Port 8000
```

---

## 🎓 Learning Path

1. **Get it running** - Follow Quick Start
2. **Explore UI** - Click all buttons, try all models
3. **Read docs** - Understand the architecture
4. **Upload to GitHub** - Share with others
5. **Customize** - Modify colors, add features
6. **Deploy** - Run on cloud (AWS/Azure)
7. **Scale** - Add more models, better tracking

---

## 🎉 You're All Set!

Everything is ready to go:

✅ Standalone HTML UI (no Node.js!)
✅ Python FastAPI backend
✅ Easy startup scripts
✅ Git repository initialized
✅ Complete documentation
✅ Ready for GitHub

**Next action:** Run `.\start-backend.bat` 🚀

---

**Questions?** Check the documentation files:
- `QUICKSTART.md`
- `GITHUB_SETUP.md`
- `README.md`

**Happy tracking!** 👁️✨
