import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

const CameraFeed = ({ videoRef, canvasRef, isActive, isProcessing, mode, onFrameCapture }) => {
  const captureIntervalRef = useRef(null);

  useEffect(() => {
    // Start frame capture when active and in exercise mode
    if (isActive && mode === 'exercise' && onFrameCapture && canvasRef.current) {
      captureIntervalRef.current = setInterval(() => {
        if (canvasRef.current) {
          onFrameCapture(canvasRef.current);
        }
      }, 100); // Capture at 10 FPS
    } else {
      if (captureIntervalRef.current) {
        clearInterval(captureIntervalRef.current);
        captureIntervalRef.current = null;
      }
    }

    return () => {
      if (captureIntervalRef.current) {
        clearInterval(captureIntervalRef.current);
      }
    };
  }, [isActive, mode, onFrameCapture]);

  return (
    <motion.div 
      className="card overflow-hidden card-hover"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
          {mode === 'exercise' ? 'Exercise Tracking' : 'Camera Feed'}
        </h2>
        <div className="flex items-center space-x-3">
          {isProcessing && (
            <motion.span 
              className="text-sm font-semibold text-primary-600"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              Processing...
            </motion.span>
          )}
          <div className={`w-4 h-4 rounded-full ${isActive ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
        </div>
      </div>
 
      <div className="relative bg-black rounded-2xl overflow-hidden shadow-2xl" style={{ aspectRatio: '16/9' }}>
        {/* Video Element */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`absolute inset-0 w-full h-full object-cover ${isActive ? 'block' : 'hidden'}`}
        />
 
        {/* Canvas for Drawing Detections */}
        <canvas
          ref={canvasRef}
          className={`absolute inset-0 w-full h-full ${isActive ? 'block' : 'hidden'}`}
        />
 
        {/* Placeholder when camera is off */}
        {!isActive && (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
            <motion.div 
              className="text-center"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <motion.svg 
                className="w-20 h-20 text-gray-600 mx-auto mb-6" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </motion.svg>
              <p className="text-gray-400 text-xl font-medium mb-2">Camera is off</p>
              <p className="text-gray-500 text-sm">Click "Start Tracking" to begin</p>
            </motion.div>
          </div>
        )}
 
        {/* Processing Indicator */}
        {isProcessing && (
          <motion.div 
            className="absolute top-6 right-6 bg-black/70 backdrop-blur-lg rounded-xl px-4 py-3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center space-x-3">
              <motion.div 
                className="w-3 h-3 bg-primary-500 rounded-full"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
              />
              <span className="text-white text-sm font-semibold">
                {mode === 'exercise' ? 'Analyzing Form...' : 'AI Processing'}
              </span>
            </div>
          </motion.div>
        )}
      </div>
 
      {/* Camera Info */}
      {isActive && (
        <motion.div 
          className="mt-6 grid grid-cols-3 gap-4 text-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          {[
            { label: 'Resolution', value: '1280 × 720', icon: '📱' },
            { label: 'Frame Rate', value: '30 FPS', icon: '⚡' },
            { label: 'Latency', value: '< 100ms', icon: '⏱️' }
          ].map((info, index) => (
            <motion.div 
              key={index}
              className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200"
              whileHover={{ scale: 1.05, y: -2 }}
              transition={{ duration: 0.2 }}
            >
              <div className="text-center">
                <div className="text-2xl mb-1">{info.icon}</div>
                <span className="text-gray-600 block text-xs mb-1">{info.label}</span>
                <p className="font-bold text-gray-900">{info.value}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
};

export default CameraFeed;