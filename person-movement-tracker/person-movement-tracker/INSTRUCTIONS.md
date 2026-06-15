# 📚 Person Movement Tracker - Complete Instructions

Welcome to the Person Movement Tracker! This comprehensive guide will help you get started with AI-powered exercise form analysis and comparison.

## 🎯 What is Person Movement Tracker?

Person Movement Tracker is an advanced web application that uses AI and computer vision to:

- **Analyze exercise form** in real-time
- **Count repetitions** automatically
- **Provide detailed feedback** on technique
- **Compare with professional videos** from YouTube
- **Track progress** over time

## 🚀 Quick Start

### 1. Open the Application
Visit your deployed application (Vercel/Netlify) or run locally:
```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend (separate terminal)
cd backend && python -m src.main
```

### 2. Grant Camera Permissions
When you first visit the app, allow camera access for exercise analysis.

### 3. Start Analyzing
- Click "📚 Instructions" to learn how to use the app
- Click "💪 Exercise" to start live analysis
- Click "📺 YouTube" to compare with professional videos

## 📹 Live Exercise Analysis

### Step-by-Step Guide

1. **Select Mode**: Click "💪 Exercise" in the top navigation
2. **Choose Exercise**: Select from Push-up, Squat, Lunge, or Plank
3. **Start Camera**: The camera will activate automatically
4. **Record Exercise**:
   - Click "Start Recording"
   - Perform 5-15 seconds of continuous exercise
   - Click "Stop Recording"
5. **Analyze**: Click "Analyze Recorded Exercise"
6. **Review Results**: See your form score, rep count, and feedback

### Understanding Your Results

#### 📊 Form Score
- **85-100%**: Excellent form - keep it up!
- **70-84%**: Good form with minor improvements
- **50-69%**: Needs improvement - focus on corrections
- **<50%**: Major form issues - seek guidance

#### 🔢 Rep Count
- Automatically counted repetitions
- Works for Push-ups, Squats, Lunges, Planks

#### 📐 Joint Angles
- Real-time measurements of key joint positions
- Helps identify specific form issues

#### ⚠️ Form Issues
- **Critical**: Major problems requiring immediate attention
- **Warning**: Important improvements needed
- **Info**: Helpful suggestions for optimization

## 📺 YouTube Comparison

### Professional Video Analysis

1. **Find Reference Videos**: Use the provided examples or search YouTube
2. **Copy URL**: Paste any YouTube exercise video URL
3. **Select Exercise Type**: Match the video content
4. **Analyze**: Click "Analyze YouTube Video"
5. **Compare**: See professional form analysis

### Recommended YouTube Videos

#### Push-ups
- Perfect Form: `https://www.youtube.com/watch?v=IODxDxX7oi4`
- Military Style: `https://www.youtube.com/watch?v=OUgsJ8-Vi0E`
- Tutorial: `https://www.youtube.com/watch?v=_l3ySVKYVJ8`

#### Squats
- Bodyweight: `https://www.youtube.com/watch?v=aclHkVaku9U`
- Goblet Squat: `https://www.youtube.com/watch?v=Dy28eq2PjcM`
- Air Squat: `https://www.youtube.com/watch?v=COKYKgQ8KR0`

#### Lunges
- Forward Lunge: `https://www.youtube.com/watch?v=QOVaHwm-Q6U`
- Walking Lunge: `https://www.youtube.com/watch?v=L8fvypPrzzs`
- Reverse Lunge: `https://www.youtube.com/watch?v=0_9FqEYKwOc`

#### Planks
- Forearm Plank: `https://www.youtube.com/watch?v=pSHjTRCQxIw`
- High Plank: `https://www.youtube.com/watch?v=ASdvN_XEl_c`
- Side Plank: `https://www.youtube.com/watch?v=kiA9j-dR0Ic`

## 💡 Tips for Best Results

### 🎥 Video Recording
- **Lighting**: Bright, even lighting without harsh shadows
- **Background**: Plain, uncluttered background
- **Clothing**: Wear form-fitting clothes
- **Positioning**: Stay centered in frame, full body visible
- **Distance**: Keep camera 6-10 feet away
- **Angle**: Camera at waist height, slightly angled up
- **Stability**: Keep camera steady during recording

### 📱 Camera Setup
- **Resolution**: Higher resolution = better analysis
- **Frame Rate**: 30 FPS recommended
- **Focus**: Ensure you're in focus
- **Permissions**: Allow camera access when prompted

### 🏃 Exercise Performance
- **Duration**: 5-15 seconds of continuous movement
- **Consistency**: Maintain steady pace
- **Full Range**: Complete full range of motion
- **Breathing**: Natural breathing pattern
- **Focus**: Concentrate on proper form

## 🔧 Troubleshooting

### Camera Issues
**Problem**: Camera not working
**Solutions**:
- Refresh the page and re-grant permissions
- Close other apps using camera
- Try different browser (Chrome recommended)
- Check camera hardware

**Problem**: Poor video quality
**Solutions**:
- Improve lighting conditions
- Clean camera lens
- Adjust camera settings
- Try different camera angle

### Analysis Issues
**Problem**: No analysis results
**Solutions**:
- Ensure person is clearly visible
- Check lighting and contrast
- Try different camera position
- Record for longer duration

**Problem**: Inaccurate rep counting
**Solutions**:
- Perform exercise more clearly
- Maintain consistent pace
- Ensure full range of motion
- Try different exercise selection

**Problem**: Slow performance
**Solutions**:
- Close other browser tabs
- Use modern browser
- Check internet connection
- Wait for analysis to complete

### YouTube Issues
**Problem**: Video analysis fails
**Solutions**:
- Check YouTube URL is valid and public
- Ensure video is not age-restricted
- Try different video URLs
- Check internet connection

## 📊 Understanding Analysis Metrics

### Form Score Calculation
- Based on joint angles and movement patterns
- Compares against ideal form standards
- Weighted by exercise-specific criteria

### Rep Detection Algorithm
- Analyzes movement patterns and joint angles
- Detects start/end positions of repetitions
- Filters out incomplete movements

### Joint Angle Measurements
- Real-time tracking of key joints
- Measured in degrees from reference positions
- Used to identify form deviations

### Issue Severity Levels
- **Critical**: Safety concerns or major form issues
- **Warning**: Important technique improvements
- **Info**: Optimization suggestions

## 🛠️ Technical Details

### AI Models Used
- **MediaPipe Pose**: Real-time pose detection
- **Custom Exercise Analyzers**: Specialized for each exercise type
- **Computer Vision**: Frame analysis and processing

### Supported Browsers
- **Chrome**: Recommended (best performance)
- **Firefox**: Good support
- **Safari**: Basic support
- **Edge**: Good support

### System Requirements
- **Camera**: Any webcam or smartphone camera
- **Internet**: Required for analysis
- **Browser**: Modern browser with camera support
- **RAM**: 4GB+ recommended

## 📈 Progress Tracking

### Local Storage
- All analysis results saved locally
- Progress history maintained
- Export/import capabilities

### Session Management
- Automatic session tracking
- Exercise type recognition
- Performance metrics over time

## 🔒 Privacy & Security

### Data Handling
- All processing happens locally or on your server
- No personal data sent to third parties
- YouTube videos analyzed server-side only

### Permissions
- Camera access only when needed
- No persistent data collection
- Local storage for user preferences only

## 🎯 Best Practices

### Exercise Selection
- Start with familiar exercises
- Choose appropriate difficulty level
- Focus on one exercise type per session
- Gradually increase complexity

### Form Improvement
- Pay attention to critical issues first
- Make one change at a time
- Record progress regularly
- Compare with professional videos

### Regular Usage
- Consistent practice improves form
- Track progress over time
- Set realistic improvement goals
- Celebrate small victories

## 📞 Support & Help

### Getting Help
1. Check this documentation first
2. Try the troubleshooting section
3. Review browser console for errors
4. Test with different exercises

### Common Questions

**Q: Why isn't the camera working?**
A: Ensure you've granted camera permissions and no other apps are using it.

**Q: Why are rep counts wrong?**
A: Make sure you're performing the exercise clearly with full range of motion.

**Q: Can I analyze any exercise?**
A: Currently supports Push-ups, Squats, Lunges, and Planks. More coming soon!

**Q: Is my data secure?**
A: Yes, all analysis happens locally or on your server. No data sent to third parties.

## 🚀 Advanced Features

### Custom Analysis
- Exercise-specific form criteria
- Real-time feedback adjustments
- Progress visualization

### Integration Options
- API endpoints for custom integrations
- Webhook support for automation
- Export capabilities for data analysis

---

## 🎉 Ready to Start?

1. **Open the app** and click "📚 Instructions"
2. **Grant camera permissions** when prompted
3. **Try a push-up analysis** to see it in action
4. **Compare with YouTube videos** for professional feedback

**Happy exercising! 💪🎯**

---

*Last updated: 2026-04-04*
*Person Movement Tracker v1.0*