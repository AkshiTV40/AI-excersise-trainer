import React from 'react';
import { motion } from 'framer-motion';

const EXERCISES = [
  { id: 'squat', name: 'Squat', icon: '🏋️', description: 'Lower body exercise' },
  { id: 'pushup', name: 'Push-up', icon: '💪', description: 'Upper body exercise' },
  { id: 'lunge', name: 'Lunge', icon: '🚶', description: 'Leg exercise' },
];

function ExerciseSelector({ selectedExercise, onExerciseChange, isTracking, onStartTracking, onStopTracking }) {
  return (
    <motion.div 
      className="card card-hover"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h3 className="text-xl font-bold text-gray-900 mb-6 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
        Select Exercise
      </h3>
      
      {/* Exercise Cards */}
      <div className="space-y-4 mb-8">
        {EXERCISES.map((exercise, index) => (
          <motion.button
            key={exercise.id}
            onClick={() => onExerciseChange(exercise.id)}
            className={`w-full text-left p-5 rounded-xl border-2 transition-all ${
              selectedExercise === exercise.id
                ? 'border-primary-500 bg-gradient-to-r from-primary-50 to-blue-50 shadow-md'
                : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
            }`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
            whileHover={{ scale: 1.02, x: 5 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-center">
              <motion.span 
                className="text-3xl mr-4"
                animate={{ rotate: selectedExercise === exercise.id ? [0, 5, -5, 0] : 0 }}
                transition={{ duration: 0.5 }}
              >
                {exercise.icon}
              </motion.span>
              <div>
                <div className="font-semibold text-gray-900">{exercise.name}</div>
                <div className="text-sm text-gray-600">{exercise.description}</div>
              </div>
              {selectedExercise === exercise.id && (
                <motion.div
                  className="ml-auto"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 400 }}
                >
                  <svg className="w-6 h-6 text-primary-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </motion.div>
              )}
            </div>
          </motion.button>
        ))}
      </div>

      {/* Control Buttons */}
      <div className="flex space-x-4">
        {!isTracking ? (
          <motion.button
            onClick={onStartTracking}
            className="flex-1 btn-primary flex items-center justify-center space-x-2"
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
            className="flex-1 btn-danger flex items-center justify-center space-x-2"
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
      </div>

      {/* Tips */}
      <motion.div 
        className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-5 border border-blue-100"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <h4 className="text-sm font-bold text-blue-900 mb-3 flex items-center space-x-2">
          <span>💡</span>
          <span>Tips for Best Results</span>
        </h4>
        <ul className="text-sm text-blue-800 space-y-2">
          <li className="flex items-start space-x-2">
            <span className="text-blue-600 mt-1">•</span>
            <span>Stand in a well-lit area</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-blue-600 mt-1">•</span>
            <span>Ensure your full body is visible</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-blue-600 mt-1">•</span>
            <span>Keep the camera at eye level</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-blue-600 mt-1">•</span>
            <span>Wear form-fitting clothing</span>
          </li>
        </ul>
      </motion.div>
    </motion.div>
  );
}

export default ExerciseSelector;
