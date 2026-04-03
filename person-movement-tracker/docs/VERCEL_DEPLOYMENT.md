# Vercel Deployment Guide

This guide explains how to deploy the Person Movement Tracker to Vercel.

## Overview

The Person Movement Tracker is a full-stack application with:
- **Frontend**: React + Vite (deployed to Vercel)
- **Backend**: FastAPI + Python (deployed separately)

## Prerequisites

1. A Vercel account (free tier available)
2. A GitHub account with the repository cloned
3. A backend deployment (see Backend Deployment section)

## Frontend Deployment to Vercel

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Push your code to GitHub** (already done)
   - Repository: https://github.com/AkshiTV40/Person-movement-tracker

2. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/dashboard
   - Click "Add New Project"

3. **Import your repository**
   - Select `AkshiTV40/Person-movement-tracker`
   - Click "Import"

4. **Configure the project**
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

5. **Add Environment Variables**
   - `VITE_API_URL`: Your backend API URL (e.g., `https://your-backend.onrender.com`)
   - `VITE_WS_URL`: Your WebSocket URL (e.g., `wss://your-backend.onrender.com`)

6. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete

### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy the frontend**
   ```bash
   cd frontend
   vercel
   ```

4. **Follow the prompts**
   - Set up and deploy to Vercel
   - Add environment variables when prompted

## Backend Deployment Options

Since Vercel is primarily for frontend applications, you need to deploy the backend separately. Here are some options:

### Option 1: Render (Recommended - Free Tier)

1. **Create a Render account**
   - Visit: https://render.com
   - Sign up for free

2. **Create a new Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select `AkshiTV40/Person-movement-tracker`

3. **Configure the service**
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**
   - `MODEL_NAME`: `yolov8n` (or your preferred model)
   - `DEVICE`: `cpu` (or `cuda` if GPU is available)
   - `REDIS_URL`: Your Redis URL (optional)

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

6. **Copy your backend URL**
   - Use this URL as `VITE_API_URL` in Vercel

### Option 2: Railway

1. **Create a Railway account**
   - Visit: https://railway.app
   - Sign up for free

2. **Create a new project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `AkshiTV40/Person-movement-tracker`

3. **Configure the service**
   - Select the `backend` directory
   - Add environment variables

4. **Deploy**
   - Railway will automatically deploy

### Option 3: Vercel Serverless Functions (Advanced)

You can also deploy the backend as Vercel Serverless Functions:

1. **Create a `api` directory in the root**
2. **Convert FastAPI routes to Vercel functions**
3. **Use `vercel.json` to configure**

This approach requires significant refactoring and is not recommended for beginners.

## Environment Variables

### Frontend (Vercel)
```env
VITE_API_URL=https://your-backend-url.com
VITE_WS_URL=wss://your-backend-url.com
```

### Backend (Render/Railway)
```env
MODEL_NAME=yolov8n
DEVICE=cpu
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=https://your-frontend-url.vercel.app
```

## Troubleshooting

### 404 Error on Vercel

If you're getting a 404 error, check the following:

1. **Verify the build output directory**
   - Make sure `vite.config.js` has `outDir: 'dist'`
   - Make sure Vercel is looking for `dist` folder

2. **Check the root directory**
   - In Vercel settings, set Root Directory to `frontend`

3. **Verify the build command**
   - Build command should be `npm run build`

4. **Check environment variables**
   - Make sure `VITE_API_URL` is set correctly

5. **Check the vercel.json configuration**
   - Ensure routes are properly configured

### CORS Issues

If you're getting CORS errors:

1. **Update backend CORS settings**
   - Add your Vercel URL to `CORS_ORIGINS`
   - Example: `CORS_ORIGINS=https://your-app.vercel.app`

2. **Check API calls in frontend**
   - Make sure API calls use the correct URL

### WebSocket Connection Issues

If WebSocket connections fail:

1. **Verify WebSocket URL**
   - Use `wss://` for production (not `ws://`)
   - Include the full path: `wss://your-backend.com/ws/track`

2. **Check backend WebSocket configuration**
   - Ensure WebSocket endpoint is accessible

## Post-Deployment Checklist

- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Render/Railway
- [ ] Environment variables configured
- [ ] CORS settings updated
- [ ] WebSocket connection working
- [ ] Camera access working
- [ ] Person detection working
- [ ] Tracking visualization working

## Monitoring

### Vercel Dashboard
- Visit: https://vercel.com/dashboard
- View logs, analytics, and deployment history

### Backend Monitoring
- Render: https://dashboard.render.com
- Railway: https://dashboard.railway.app

## Cost

- **Vercel**: Free tier available (100GB bandwidth/month)
- **Render**: Free tier available (750 hours/month)
- **Railway**: Free tier available ($5 credit/month)

## Support

If you encounter issues:
1. Check Vercel deployment logs
2. Check backend deployment logs
3. Review this documentation
4. Check the GitHub Issues page

## Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Render Documentation](https://render.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
