import React, { useState } from 'react';
import { motion } from 'framer-motion';
import CameraFeed from './components/CameraFeed';
import ExerciseFeedback from './components/ExerciseFeedback';
import ExerciseSelector from './components/ExerciseSelector';
import YouTubeAnalyzer from './components/YouTubeAnalyzer';
import Instructions from './components/Instructions';
import ExerciseTimer from './components/ExerciseTimer';
import { useCamera } from './hooks/useCamera';
import { useExerciseTracking } from './hooks/useExerciseTracking';
import { trackExerciseVideo } from './services/api';

function App() {
  const [tab, setTab] = useState('live');
  const [isTracking, setIsTracking] = useState(false);
  const [selectedExercise, setSelectedExercise] = useState('squat');
  const [exerciseAnalysis, setExerciseAnalysis] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [referenceUrl, setReferenceUrl] = useState('');
  const [isVideoAnalyzing, setIsVideoAnalyzing] = useState(false);
  const [videoAnalysisResult, setVideoAnalysisResult] = useState(null);

  const { videoRef, canvasRef, startCamera, stopCamera, isActive } = useCamera();
  const { processExerciseFrame, isExerciseProcessing, resetExercise } = useExerciseTracking();

  const handleStartTracking = async () => {
    await startCamera();
    setIsTracking(true);
  };

  const handleStopTracking = () => {
    stopCamera();
    setIsTracking(false);
  };

  const handleExerciseChange = (exercise) => {
    setSelectedExercise(exercise);
    resetExercise();
    setExerciseAnalysis(null);
  };

  const handleVideoFileChange = (e) => {
    setVideoFile(e.target.files?.[0] || null);
    setVideoAnalysisResult(null);
  };

  const analyzeUploadedVideo = async () => {
    if (!videoFile) return;
    setIsVideoAnalyzing(true);
    try {
      const result = await trackExerciseVideo(videoFile, selectedExercise, referenceUrl || null, 10);
      setVideoAnalysisResult(result);
    } catch (err) {
      console.error('Video analysis failed:', err);
    } finally {
      setIsVideoAnalyzing(false);
    }
  };

  const handleTabChange = (newTab) => {
    setTab(newTab);
    if (isTracking) handleStopTracking();
  };

  const TABS = [
    { id: 'live', label: 'Live Analysis' },
    { id: 'upload', label: 'Upload Clip' },
    { id: 'youtube', label: 'YouTube Compare' },
    { id: 'guide', label: 'Guide' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
      <header className="glass-effect border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <motion.div
            className="flex items-center justify-between"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-center space-x-4">
              <motion.div
                className="w-11 h-11 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg"
                whileHover={{ scale: 1.08, rotate: 4 }}
                transition={{ type: 'spring', stiffness: 300 }}
              >
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </motion.div>
              <div>
                <h1 className="text-xl font-bold gradient-text">AI Exercise Trainer</h1>
                <p className="text-xs text-gray-500">
                  {tab === 'live' ? 'Real-time form analysis' :
                   tab === 'upload' ? 'Analyse your exercise clip' :
                   tab === 'youtube' ? 'Compare with YouTube pros' :
                   'How to use this app'}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex bg-white/70 backdrop-blur-sm rounded-xl p-1 border border-gray-200 shadow-sm">
                {TABS.map((t) => (
                  <motion.button
                    key={t.id}
                    onClick={() => handleTabChange(t.id)}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                      tab === t.id
                        ? 'bg-blue-600 text-white shadow'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                    whileTap={{ scale: 0.96 }}
                  >
                    {t.label}
                  </motion.button>
                ))}
              </div>

              {tab === 'live' && (
                <div className="flex items-center space-x-2">
                  <div className={`w-2.5 h-2.5 rounded-full ${isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                  <span className="text-xs font-medium text-gray-600">
                    {isActive ? 'Camera On' : 'Camera Off'}
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {tab === 'youtube' ? (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            <YouTubeAnalyzer />
          </motion.div>
        ) : tab === 'guide' ? (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            <Instructions />
          </motion.div>
        ) : tab === 'upload' ? (
          <motion.div
            className="grid grid-cols-1 lg:grid-cols-3 gap-8"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <div className="lg:col-span-1 space-y-6">
              <ExerciseSelector
                selectedExercise={selectedExercise}
                onExerciseChange={handleExerciseChange}
                isTracking={false}
                onStartTracking={() => {}}
                onStopTracking={() => {}}
                hideControls
              />
            </div>

            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                <h3 className="text-lg font-bold text-gray-900 mb-5">Upload Your Exercise Clip</h3>

                <label className="block mb-4">
                  <span className="text-sm font-medium text-gray-700 mb-1 block">Video file (5–30s)</span>
                  <input
                    type="file"
                    accept="video/*"
                    onChange={handleVideoFileChange}
                    className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                </label>

                <label className="block mb-5">
                  <span className="text-sm font-medium text-gray-700 mb-1 block">YouTube reference URL (optional)</span>
                  <input
                    type="url"
                    value={referenceUrl}
                    onChange={(e) => setReferenceUrl(e.target.value)}
                    placeholder="https://www.youtube.com/watch?v=..."
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                </label>

                <button
                  onClick={analyzeUploadedVideo}
                  disabled={!videoFile || isVideoAnalyzing}
                  className={`w-full py-3 rounded-xl font-semibold text-white transition-all ${
                    !videoFile || isVideoAnalyzing
                      ? 'bg-gray-300 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg'
                  }`}
                >
                  {isVideoAnalyzing ? 'Analysing…' : 'Analyse Clip'}
                </button>
              </div>

              {videoAnalysisResult && (
                <motion.div
                  className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100 space-y-4"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <h3 className="text-lg font-bold text-gray-900">Analysis Results</h3>

                  <div className="flex items-center space-x-4">
                    <div className="flex-1 bg-blue-50 rounded-xl p-4 text-center">
                      <p className="text-xs text-gray-500 mb-1">Form Score</p>
                      <p className="text-3xl font-bold text-blue-700">{videoAnalysisResult.user_form_score}%</p>
                    </div>
                    {videoAnalysisResult.comparison && (
                      <div className="flex-1 bg-purple-50 rounded-xl p-4 text-center">
                        <p className="text-xs text-gray-500 mb-1">vs Reference</p>
                        <p className={`text-3xl font-bold ${videoAnalysisResult.comparison.score_gap >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                          {videoAnalysisResult.comparison.score_gap >= 0 ? '+' : ''}{videoAnalysisResult.comparison.score_gap}
                        </p>
                      </div>
                    )}
                  </div>

                  {videoAnalysisResult.ai_guidance && (
                    <div className="bg-purple-50 border border-purple-100 rounded-xl p-4">
                      <p className="text-xs font-semibold text-purple-700 mb-2 uppercase tracking-wide">AI Coaching</p>
                      <div className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">
                        {videoAnalysisResult.ai_guidance}
                      </div>
                    </div>
                  )}

                  {videoAnalysisResult.reference_tutorials?.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Recommended tutorials</p>
                      <ul className="space-y-1">
                        {videoAnalysisResult.reference_tutorials.map((link, i) => (
                          <li key={i}>
                            <a href={link} target="_blank" rel="noreferrer" className="text-sm text-blue-600 hover:underline break-all">
                              {link}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </motion.div>
              )}
            </div>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <motion.div
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4 }}
              >
                <CameraFeed
                  videoRef={videoRef}
                  canvasRef={canvasRef}
                  isActive={isActive}
                  isProcessing={isExerciseProcessing}
                  mode="exercise"
                  onFrameCapture={(frame) => {
                    processExerciseFrame(frame, selectedExercise, setExerciseAnalysis);
                  }}
                />
              </motion.div>
            </div>

            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: 0.15 }}
              >
                <ExerciseSelector
                  selectedExercise={selectedExercise}
                  onExerciseChange={handleExerciseChange}
                  isTracking={isTracking}
                  onStartTracking={handleStartTracking}
                  onStopTracking={handleStopTracking}
                />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: 0.25 }}
              >
                <ExerciseFeedback analysis={exerciseAnalysis} />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: 0.35 }}
              >
                <ExerciseTimer selectedExercise={selectedExercise} />
              </motion.div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
