# 🚀 Quick Start Guide

## ⚡ 30-Second Setup

### Windows Users:

**Terminal 1 - Start Backend:**
```powershell
cd C:\Users\AkshiLocal\Image_recog\person-movement-tracker
.\start-backend.bat
```

**Terminal 2 - Start UI Server:**
```powershell
cd C:\Users\AkshiLocal\Image_recog\person-movement-tracker
.\start-ui.bat
```

Then open browser to: **http://localhost:8080**

---

## 📋 What You Need

- Python 3.8+ (for backend)
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Webcam (for live tracking)
- ~2GB disk space for ML models

---

## 🎯 Using the Application

1. **Start Backend** → Runs ML models and detection
2. **Start UI** → Opens in browser
3. **Click "Start"** → Grant camera permission
4. **Watch it work!** → Real-time person detection and tracking

---

## 🌐 GitHub Upload

See **GITHUB_SETUP.md** for detailed instructions on:
- Creating a GitHub repository
- Pushing your code
- Using git commands

Quick version:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/person-movement-tracker.git
git push -u origin main
```

---

## 🎨 UI Features

✨ **Modern Interface**
- Real-time video feed with detections
- Live performance metrics (FPS, inference time)
- Active tracking list
- Dark theme with smooth animations

🔧 **Controls**
- Switch between detection models (YOLOv8, DETR, YOLOS)
- Enable/disable tracking
- Upload images for detection
- Real-time statistics

📊 **Performance Monitoring**
- Frames per second (FPS)
- Inference time in milliseconds
- Number of active tracks
- Connection status

---

## 🛠️ Manual Start (If Scripts Don't Work)

### Backend:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### UI:
```bash
cd html-ui
python -m http.server 8080
# Open: http://localhost:8080
```

---

## 📍 File Locations

| Component | Location |
|-----------|----------|
| **HTML UI** | `html-ui/index.html` |
| **Backend** | `backend/src/main.py` |
| **API Docs** | `http://localhost:8000/docs` |
| **Config** | `backend/src/config.py` |

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port already in use** | Change port in start scripts |
| **Python not found** | Install Python 3.8+ |
| **Camera permission denied** | Check browser privacy settings |
| **Backend won't start** | Run `pip install -r requirements.txt` |
| **Slow inference** | Switch to YOLOv8 model |

---

## 📚 Documentation

- **Full Setup**: See `GITHUB_SETUP.md`
- **API Reference**: `docs/API.md`
- **Deployment**: `docs/DEPLOYMENT.md`

---

## 🎓 Project Structure

```
person-movement-tracker/
├── html-ui/              ← Open in browser
├── backend/              ← FastAPI server
│   ├── src/
│   │   ├── api/         ← REST endpoints
│   │   ├── models/      ← Detection models
│   │   └── services/    ← Business logic
│   └── requirements.txt
├── frontend/            ← (Optional) React version
├── docs/                ← Documentation
└── scripts/             ← Utilities
```

---

## 🚀 Next Steps

1. ✅ Get it running locally
2. ✅ Push to GitHub (see GITHUB_SETUP.md)
3. 📝 Customize models/settings in `backend/src/config.py`
4. 🐳 Deploy with Docker (see DEPLOYMENT.md)
5. 🔧 Extend with your own features

---

## 💡 Tips

- **Fast inference**: Use YOLOv8 model
- **Best accuracy**: Use DETR model
- **Balanced**: Use YOLOS model
- **Custom models**: Add to `backend/src/models/`
- **Dark environment**: Ensure good lighting

---

**Enjoy real-time person detection and tracking! 🎉**
