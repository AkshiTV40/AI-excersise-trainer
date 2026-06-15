import React from 'react';
import { motion } from 'framer-motion';

const Controls = ({ 
  isTracking, 
  selectedModel, 
  onStartTracking, 
  onStopTracking, 
  onModelChange 
}) => {
  const models = [
    { id: 'yolov8', name: 'YOLOv8', description: 'Fast & accurate' },
    { id: 'detr', name: 'DETR', description: 'Transformer-based' },
    { id: 'yolos', name: 'YOLOS', description: 'Vision Transformer' }
  ];

  return (
    <motion.div 
      className="card card-hover"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <h2 className="text-xl font-bold text-gray-900 mb-6 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
        Controls
      </h2>

      {/* Model Selection */}
      <div className="mb-8">
        <label className="block text-sm font-semibold text-gray-700 mb-3">
          Detection Model
        </label>
        <div className="space-y-3">
          {models.map((model, index) => (
            <motion.label
              key={model.id}
              className={`flex items-center p-4 rounded-xl border-2 cursor-pointer transition-all ${
                selectedModel === model.id
                  ? 'border-primary-500 bg-gradient-to-r from-primary-50 to-blue-50'
                  : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
              }`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              whileHover={{ scale: 1.02, x: 5 }}
              whileTap={{ scale: 0.98 }}
            >
              <input
                type="radio"
                name="model"
                value={model.id}
                checked={selectedModel === model.id}
                onChange={() => onModelChange(model.id)}
                className="sr-only"
              />
              <div className="flex-1">
                <div className="font-semibold text-gray-900">{model.name}</div>
                <div className="text-sm text-gray-600">{model.description}</div>
              </div>
              {selectedModel === model.id && (
                <motion.svg 
                  className="w-6 h-6 text-primary-600" 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                  animate={{ rotate: [0, 360] }}
                  transition={{ duration: 0.5 }}
                >
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </motion.svg>
              )}
            </motion.label>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-4">
        {!isTracking ? (
          <motion.button
            onClick={onStartTracking}
            className="w-full btn-primary flex items-center justify-center space-x-3"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-lg font-semibold">Start Tracking</span>
          </motion.button>
        ) : (
          <motion.button
            onClick={onStopTracking}
            className="w-full btn-danger flex items-center justify-center space-x-3"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
            </svg>
            <span className="text-lg font-semibold">Stop Tracking</span>
          </motion.button>
        )}

        <motion.button 
          className="w-full btn-secondary flex items-center justify-center space-x-3"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          <span className="text-lg font-medium">Upload Video</span>
        </motion.button>
      </div>

      {/* Settings */}
      <motion.div 
        className="mt-8 pt-6 border-t border-gray-200"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Settings</h3>
        <div className="space-y-4">
          {[
            { label: 'Show Bounding Boxes', defaultChecked: true },
            { label: 'Show Track IDs', defaultChecked: true },
            { label: 'Save Session', defaultChecked: false }
          ].map((setting, index) => (
            <motion.div 
              key={index}
              className="flex items-center justify-between"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.5 + index * 0.1 }}
            >
              <span className="text-sm font-medium text-gray-700">{setting.label}</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  defaultChecked={setting.defaultChecked} 
                  className="sr-only peer" 
                />
                <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[3px] after:left-[3px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-primary-600" />
              </label>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default Controls;