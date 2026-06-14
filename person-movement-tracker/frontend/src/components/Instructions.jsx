import React from 'react';
import { motion } from 'framer-motion';

const Instructions = () => {
  const sections = [
    {
      title: "Getting Started",
      content: [
        "Welcome to the AI Exercise Trainer! This app analyses your exercise form using AI-powered pose detection.",
        "Use Live Analysis for real-time form feedback, Upload Clip to analyse a saved video, or YouTube Compare to compare your form with professional technique."
      ]
    },
    {
      title: "Live Exercise Analysis",
      content: [
        "1. Click 'Live Analysis' tab",
        "2. Select your exercise (Squat, Push-up, or Lunge)",
        "3. Click 'Start Tracking' and perform your exercise",
        "4. Watch real-time form feedback and rep count",
        "5. Click 'Stop Tracking' when done"
      ]
    },
    {
      title: "Upload Clip Analysis",
      content: [
        "1. Click 'Upload Clip' tab",
        "2. Select your exercise type",
        "3. Choose a 5-30 second video file from your device",
        "4. Optionally paste a YouTube reference URL for comparison",
        "5. Click 'Analyse Clip' to get detailed AI coaching feedback"
      ]
    },
    {
      title: "Tips for Best Results",
      content: [
        "• Ensure good, even lighting in your exercise area",
        "• Wear form-fitting clothing for better pose detection",
        "• Stay centered in the camera frame",
        "• Keep the camera stable at waist height",
        "• Use a plain background without distractions",
        "• Record 5-15 seconds of continuous, proper form"
      ]
    },
    {
      title: "Understanding Your Results",
      content: [
        "• **Form Score**: Percentage rating (85%+ = Excellent, 70-84% = Good, <70% = Needs Work)",
        "• **Rep Count**: Number of completed repetitions detected",
        "• **Joint Angles**: Measurements of key joint positions",
        "• **Critical Issues**: Major form problems requiring immediate attention",
        "• **Warning Issues**: Minor form improvements suggested",
        "• **Info Messages**: General feedback and tips"
      ]
    },
    {
      title: "Example Videos",
      content: [
        "**Push-ups:**",
        "• Perfect Form: https://www.youtube.com/watch?v=IODxDxX7oi4",
        "• Tutorial: https://www.youtube.com/watch?v=_l3ySVKYVJ8",
        "",
        "**Squats:**",
        "• Bodyweight: https://www.youtube.com/watch?v=aclHkVaku9U",
        "• Goblet Squat: https://www.youtube.com/watch?v=Dy28eq2PjcM",
        "",
        "**Lunges:**",
        "• Forward Lunge: https://www.youtube.com/watch?v=QOVaHwm-Q6U",
        "",
        "**Planks:**",
        "• Forearm Plank: https://www.youtube.com/watch?v=pSHjTRCQxIw"
      ]
    },
    {
      title: "Troubleshooting",
      content: [
        "**Camera Issues:**",
        "• Grant camera permissions when prompted",
        "• Close other apps using the camera",
        "• Try refreshing the page",
        "",
        "**Analysis Problems:**",
        "• Ensure you're fully visible in frame",
        "• Check lighting conditions",
        "• Try different camera angles",
        "• Record closer to the camera",
        "",
        "**Slow Performance:**",
        "• Use a modern browser (Chrome recommended)",
        "• Close other browser tabs",
        "• Ensure stable internet connection"
      ]
    }
  ];

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Instructions & Guide
        </h1>
        <p className="text-xl text-gray-600">
          Learn how to use the AI Exercise Trainer for optimal exercise form analysis
        </p>
      </motion.div>

      <div className="space-y-6">
        {sections.map((section, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-lg shadow-sm p-6"
          >
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              {section.title}
            </h2>
            <div className="space-y-3">
              {section.content.map((item, itemIndex) => (
                <div key={itemIndex} className="text-gray-700">
                  {item.startsWith('•') || item.startsWith('**') || /^\d+\./.test(item) ? (
                    <div className="flex items-start">
                      <span className="text-blue-600 mr-2 mt-1">•</span>
                      <div>
                        {item.split('\n').map((line, lineIndex) => (
                          <div key={lineIndex} className={line.startsWith('**') ? 'font-semibold mt-2' : ''}>
                            {line.replace(/^\*\*|\*\*$/g, '')}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-700">{item}</p>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 text-center"
      >
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Ready to Start Analyzing?
        </h3>
        <p className="text-gray-600 mb-4">
          Begin with a simple exercise like push-ups and see how the AI analyzes your form!
        </p>
        <div className="flex justify-center space-x-4">
          <button
            onClick={() => window.location.href = '#exercise'}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Start Exercise Analysis
          </button>
          <button
            onClick={() => window.location.href = '#youtube'}
            className="bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors"
          >
            Compare with YouTube
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default Instructions;