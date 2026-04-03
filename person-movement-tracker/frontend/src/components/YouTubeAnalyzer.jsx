import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../services/api';

function YouTubeAnalyzer() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [selectedExercise, setSelectedExercise] = useState('squat');
  const [exercises, setExercises] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);
  const [progress, setProgress] = useState(0);

  // Load supported exercises on mount
  useEffect(() => {
    loadExercises();
  }, []);

  const loadExercises = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/youtube/supported-exercises`);
      const data = await response.json();
      if (data.success) {
        setExercises(data.exercises);
      }
    } catch (err) {
      console.error('Failed to load exercises:', err);
    }
  };

  const handleGetVideoInfo = async () => {
    if (!youtubeUrl.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    try {
      setError(null);
      const formData = new FormData();
      formData.append('url', youtubeUrl);

      const response = await fetch(`${API_BASE_URL}/api/youtube/video-info`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      if (data.success) {
        setVideoInfo(data);
      } else {
        setError(data.error || 'Failed to get video information');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    }
  };

  const handleAnalyzeVideo = async () => {
    if (!youtubeUrl.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    try {
      setError(null);
      setIsAnalyzing(true);
      setProgress(0);
      setAnalysisResult(null);

      const formData = new FormData();
      formData.append('url', youtubeUrl);
      formData.append('exercise_type', selectedExercise);

      const response = await fetch(`${API_BASE_URL}/api/youtube/analyze`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      if (data.success) {
        setAnalysisResult(data);
        setProgress(100);
      } else {
        setError(data.detail || 'Analysis failed');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">YouTube Video Analysis</h2>
        <p className="text-gray-600">Fetch a YouTube video and analyze exercise form</p>
      </div>

      {/* Input Section */}
      <div className="mb-8 p-6 bg-gray-50 rounded-lg">
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            YouTube Video URL
          </label>
          <input
            type="text"
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isAnalyzing}
          />
          <p className="text-xs text-gray-500 mt-2">
            Supports: YouTube, Vimeo, and other major platforms
          </p>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Exercise Type to Analyze
          </label>
          <select
            value={selectedExercise}
            onChange={(e) => setSelectedExercise(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isAnalyzing}
          >
            {exercises.map((exercise) => (
              <option key={exercise.type} value={exercise.type}>
                {exercise.name} - {exercise.description}
              </option>
            ))}
          </select>
        </div>

        <div className="flex space-x-4">
          <button
            onClick={handleGetVideoInfo}
            disabled={isAnalyzing || !youtubeUrl.trim()}
            className="flex-1 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
          >
            Get Video Info
          </button>
          <button
            onClick={handleAnalyzeVideo}
            disabled={isAnalyzing || !youtubeUrl.trim()}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
          >
            {isAnalyzing ? 'Analyzing...' : 'Analyze Video'}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      {isAnalyzing && (
        <div className="mb-6">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 mt-2">Processing video... {progress}%</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 font-semibold">⚠️ Error</p>
          <p className="text-red-700 text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Video Info Section */}
      {videoInfo && videoInfo.success && (
        <div className="mb-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Video Information</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Title</p>
              <p className="font-semibold text-gray-900">{videoInfo.title}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Duration</p>
              <p className="font-semibold text-gray-900">
                {Math.floor(videoInfo.duration / 60)}:{String(videoInfo.duration % 60).padStart(2, '0')}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Uploader</p>
              <p className="font-semibold text-gray-900">{videoInfo.uploader}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Upload Date</p>
              <p className="font-semibold text-gray-900">{videoInfo.upload_date}</p>
            </div>
          </div>
          {videoInfo.thumbnail && (
            <div className="mt-4">
              <img
                src={videoInfo.thumbnail}
                alt="Video thumbnail"
                className="w-full max-w-md rounded-lg"
              />
            </div>
          )}
        </div>
      )}

      {/* Analysis Results Section */}
      {analysisResult && analysisResult.success && (
        <div className="mb-8">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-lg">
              <p className="text-sm text-gray-600">Form Score</p>
              <p className="text-3xl font-bold text-green-600">
                {analysisResult.summary.overall_form_score}%
              </p>
            </div>
            <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-lg">
              <p className="text-sm text-gray-600">Frames Analyzed</p>
              <p className="text-3xl font-bold text-blue-600">
                {analysisResult.analyzed_frames}
              </p>
            </div>
            <div className="p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 border border-yellow-200 rounded-lg">
              <p className="text-sm text-gray-600">Warnings</p>
              <p className="text-3xl font-bold text-yellow-600">
                {analysisResult.summary.warnings}
              </p>
            </div>
            <div className="p-4 bg-gradient-to-br from-red-50 to-red-100 border border-red-200 rounded-lg">
              <p className="text-sm text-gray-600">Critical Issues</p>
              <p className="text-3xl font-bold text-red-600">
                {analysisResult.summary.critical_issues}
              </p>
            </div>
          </div>

          {/* Status and Recommendations */}
          <div className="p-6 bg-gray-50 rounded-lg mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Analysis Summary</h3>
            <div className="mb-4">
              <p className="text-sm text-gray-600">Status</p>
              <p className={`text-2xl font-bold ${
                analysisResult.summary.status === 'EXCELLENT' ? 'text-green-600' :
                analysisResult.summary.status === 'GOOD' ? 'text-blue-600' :
                analysisResult.summary.status === 'NEEDS IMPROVEMENT' ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {analysisResult.summary.status}
              </p>
            </div>
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Recommendations</p>
              <ul className="space-y-2">
                {analysisResult.summary.recommendations.map((rec, idx) => (
                  <li key={idx} className="text-sm text-gray-700">
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Detailed Frame Analysis */}
          <div className="p-6 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Frame-by-Frame Analysis</h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {analysisResult.frame_analyses.slice(0, 10).map((frame, idx) => (
                <div key={idx} className="p-3 bg-white rounded border border-gray-200">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <p className="font-semibold text-gray-900">Frame {frame.frame_number}</p>
                      <p className="text-xs text-gray-500">
                        {frame.people_detected} person{frame.people_detected !== 1 ? 's' : ''} detected
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">{frame.form_score}%</p>
                      <p className="text-xs text-gray-500">Form Score</p>
                    </div>
                  </div>
                  {frame.issues.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <p className="text-xs font-semibold text-gray-600 mb-1">Issues:</p>
                      {frame.issues.map((issue, issueIdx) => (
                        <p
                          key={issueIdx}
                          className={`text-xs mb-1 ${
                            issue.severity === 'critical' ? 'text-red-600' :
                            issue.severity === 'warning' ? 'text-yellow-600' :
                            'text-blue-600'
                          }`}
                        >
                          • {issue.message} - {issue.suggestion}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
            {analysisResult.frame_analyses.length > 10 && (
              <p className="text-sm text-gray-500 mt-4">
                Showing first 10 frames of {analysisResult.analyzed_frames} total
              </p>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!analysisResult && !videoInfo && (
        <div className="text-center py-12 text-gray-400">
          <svg className="mx-auto h-12 w-12 mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-lg font-semibold">No video analyzed yet</p>
          <p className="text-sm mt-2">Enter a YouTube URL and click "Analyze Video" to get started</p>
        </div>
      )}
    </div>
  );
}

export default YouTubeAnalyzer;
