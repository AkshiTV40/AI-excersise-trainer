import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const EXERCISE_TARGETS = {
  squat: { minDuration: 0, maxDuration: 0, description: 'Count reps, not time' },
  pushup: { minDuration: 0, maxDuration: 0, description: 'Count reps, not time' },
  lunge: { minDuration: 0, maxDuration: 0, description: 'Count reps, not time' },
  plank: {
    beginner: 30,
    intermediate: 60,
    advanced: 90,
    description: 'Hold the plank position'
  },
  wall_sit: {
    beginner: 30,
    intermediate: 60,
    advanced: 90,
    description: 'Hold the wall sit position'
  },
  deadlift: { minDuration: 0, maxDuration: 0, description: 'Count reps, not time' },
  bench_press: { minDuration: 0, maxDuration: 0, description: 'Count reps, not time' },
  overhead_press: { minDuration: 0, maxDuration: 0, description: 'Count reps, not time' },
  bicep_curl: { minDuration: 0, maxDuration: 0, description: 'Count reps, not time' },
  tricep_extension: { minDuration: 0, maxDuration: 0, description: 'Count reps, not time' }
};

const FITNESS_LEVELS = {
  beginner: { label: 'Beginner', color: 'bg-green-500', description: 'New to exercise' },
  intermediate: { label: 'Intermediate', color: 'bg-yellow-500', description: 'Regular exercise' },
  advanced: { label: 'Advanced', color: 'bg-red-500', description: 'Experienced athlete' }
};

function ExerciseTimer({ selectedExercise }) {
  const [isRunning, setIsRunning] = useState(false);
  const [time, setTime] = useState(0);
  const [fitnessLevel, setFitnessLevel] = useState('intermediate');
  const [targetTime, setTargetTime] = useState(60);

  const exerciseTargets = EXERCISE_TARGETS[selectedExercise] || EXERCISE_TARGETS.squat;
  const hasTimer = exerciseTargets.minDuration > 0 || exerciseTargets.maxDuration > 0;

  useEffect(() => {
    let interval;
    if (isRunning) {
      interval = setInterval(() => {
        setTime((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  useEffect(() => {
    if (exerciseTargets[fitnessLevel]) {
      setTargetTime(exerciseTargets[fitnessLevel]);
    }
  }, [fitnessLevel, selectedExercise]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getProgress = () => {
    if (targetTime === 0) return 0;
    return Math.min((time / targetTime) * 100, 100);
  };

  const getStatus = () => {
    if (targetTime === 0) return null;
    if (time < targetTime * 0.5) return 'Just getting started!';
    if (time < targetTime) return `Keep going! ${targetTime - time}s left`;
    if (time < targetTime * 1.2) return 'Great job! Target reached!';
    return 'Excellent work! You exceeded the target!';
  };

  const handleStart = () => {
    setIsRunning(true);
    setTime(0);
  };

  const handleStop = () => {
    setIsRunning(false);
  };

  const handleReset = () => {
    setIsRunning(false);
    setTime(0);
  };

  if (!hasTimer) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Exercise Timer</h3>
        <p className="text-gray-500 text-sm">{exerciseTargets.description}</p>
        <p className="text-gray-400 text-xs mt-2">This exercise is rep-based, not time-based.</p>
      </div>
    );
  }

  return (
    <motion.div 
      className="bg-white rounded-lg shadow-sm p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Exercise Timer</h3>
      
      {/* Description */}
      <p className="text-sm text-gray-600 mb-4">{exerciseTargets.description}</p>

      {/* Fitness Level Selector */}
      <div className="mb-4">
        <label className="text-sm font-medium text-gray-700 mb-2 block">Your Fitness Level</label>
        <div className="flex space-x-2">
          {Object.entries(FITNESS_LEVELS).map(([level, info]) => (
            <button
              key={level}
              onClick={() => setFitnessLevel(level)}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                fitnessLevel === level
                  ? `${info.color} text-white`
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {info.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {FITNESS_LEVELS[fitnessLevel].description}
        </p>
      </div>

      {/* Target Time */}
      <div className="mb-4 p-4 bg-blue-50 rounded-lg">
        <div className="text-center">
          <p className="text-sm text-gray-600 mb-1">Target Duration</p>
          <p className="text-3xl font-bold text-blue-600">{targetTime}s</p>
          <p className="text-xs text-gray-500 mt-1">for {fitnessLevel} level</p>
        </div>
      </div>

      {/* Timer Display */}
      <div className="mb-4">
        <div className="relative h-32 bg-gray-100 rounded-lg overflow-hidden">
          {/* Progress Bar */}
          <motion.div 
            className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-green-400 to-green-500"
            style={{ height: `${getProgress()}%` }}
            initial={{ height: 0 }}
            animate={{ height: `${getProgress()}%` }}
            transition={{ duration: 0.5 }}
          />
          
          {/* Time Display */}
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-5xl font-bold text-gray-900">
              {formatTime(time)}
            </span>
          </div>

          {/* Target Line */}
          <div 
            className="absolute left-0 right-0 h-1 bg-red-500"
            style={{ bottom: `${Math.min((targetTime / (targetTime * 1.5)) * 100, 100)}%` }}
          />
        </div>
      </div>

      {/* Status Message */}
      {isRunning && (
        <motion.div 
          className="mb-4 p-3 rounded-lg text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <p className={`text-sm font-medium ${
            time >= targetTime ? 'text-green-600' : 'text-blue-600'
          }`}>
            {getStatus()}
          </p>
        </motion.div>
      )}

      {/* Control Buttons */}
      <div className="flex space-x-3">
        {!isRunning ? (
          <motion.button
            onClick={handleStart}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Start Timer
          </motion.button>
        ) : (
          <motion.button
            onClick={handleStop}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Stop
          </motion.button>
        )}
        <motion.button
          onClick={handleReset}
          className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          Reset
        </motion.button>
      </div>

      {/* Recommendation */}
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-semibold text-gray-900 mb-2">Recommendation</h4>
        <p className="text-sm text-gray-600">
          {fitnessLevel === 'beginner' && `Start with ${exerciseTargets.beginner}s and gradually increase as you get stronger.`}
          {fitnessLevel === 'intermediate' && `Aim for ${exerciseTargets.intermediate}s. Good challenge without overexertion.`}
          {fitnessLevel === 'advanced' && `${exerciseTargets.advanced}s is a solid target for your fitness level. Push yourself!`}
        </p>
      </div>
    </motion.div>
  );
}

export default ExerciseTimer;