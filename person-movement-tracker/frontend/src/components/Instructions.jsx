import React from 'react';
import { motion } from 'framer-motion';

const Instructions = () => {
  const sections = [
    {
      title: "🎯 Getting Started",
      content: [
        "Welcome to the Person Movement Tracker! This app analyzes your exercise form using AI-powered pose detection.",
        "Choose between Live Exercise Analysis or YouTube Video Comparison to improve your technique."
      ]
    },
    {
      title: "📹 Live Exercise Analysis",
      content: [
        "1. Click 'Exercise Analysis' in the main menu",
        "2. Select your exercise type (Push-up, Squat, Lunge, or Plank)",
        "3. Click 'Start Recording' and perform your exercise",
        "4. Record for 5-15 seconds of continuous movement",
        "5. Click 'Stop Recording' then 'Analyze Recorded Exercise'",
        "6. View your detailed form analysis and feedback"
      ]
    },
    {
      title: "📺 YouTube Comparison",
      content: [
        "1. Go to the 'YouTube Comparison' tab",
        "2. Copy a professional exercise video URL from YouTube",
        "3. Paste the URL in the input field",
        "4. Select the matching exercise type",
        "5. Click 'Analyze YouTube Video'",
        "6. Compare your form with professional technique"
      ]
    },
    {
      title: "💡 Tips for Best Results",
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
      title: "📊 Understanding Your Results",
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
      title: "🎥 Example Videos",
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
      title: "🔧 Troubleshooting",
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
          📚 Instructions & Guide
        </h1>
        <p className="text-xl text-gray-600">
          Learn how to use the Person Movement Tracker for optimal exercise form analysis
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