import React, { useCallback, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useRecordSession } from '../hooks/useRecordSession';

const RecordSession = ({ selectedExercise = 'squat' }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const [isCameraOn, setIsCameraOn] = useState(false);
  const [durationSeconds, setDurationSeconds] = useState(15);
  const [referenceVideoId, setReferenceVideoId] = useState('');
  const [referenceVideoPath, setReferenceVideoPath] = useState('');

  const { status, error, sessionComplete, start, stop, sendFrameDataUrl } = useRecordSession({
    durationSeconds,
  });

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setIsCameraOn(true);
      }
    } catch (e) {
      console.error(e);
      setIsCameraOn(false);
    }
  }, []);

  const stopCamera = useCallback(() => {
    try {
      if (videoRef.current?.srcObject) {
        videoRef.current.srcObject.getTracks().forEach((t) => t.stop());
      }
    } catch (_) {}
    if (videoRef.current) videoRef.current.srcObject = null;
    setIsCameraOn(false);
  }, []);

  const captureLoopRef = useRef(null);

  useEffect(() => {
    return () => {
      if (captureLoopRef.current) clearInterval(captureLoopRef.current);
      stopCamera();
    };
  }, [stopCamera]);

  useEffect(() => {
    if (!isCameraOn || status !== 'recording') return;
    if (!canvasRef.current || !videoRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    captureLoopRef.current = setInterval(() => {
      try {
        if (!videoRef.current) return;
        if (videoRef.current.readyState !== 4) return;
        canvas.width = videoRef.current.videoWidth || 1280;
        canvas.height = videoRef.current.videoHeight || 720;
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.75);
        sendFrameDataUrl(dataUrl);
      } catch (e) {
        console.error(e);
      }
    }, 100);

    return () => {
      if (captureLoopRef.current) clearInterval(captureLoopRef.current);
      captureLoopRef.current = null;
    };
  }, [isCameraOn, status, sendFrameDataUrl]);

  const handleStart = useCallback(async () => {
    if (!isCameraOn) await startCamera();
    await start({
      type: selectedExercise || 'squat',
      referenceVideoId: referenceVideoId ? Number(referenceVideoId) : null,
      referenceVideoPath: referenceVideoPath || null,
    });
  }, [isCameraOn, referenceVideoId, referenceVideoPath, startCamera, selectedExercise, start]);

  const handleStop = useCallback(() => {
    stop();
  }, [stop]);

  const durationLabel = Math.round(sessionComplete?.duration_seconds ?? sessionComplete?.duration ?? 0);
  const videoHref = sessionComplete?.video_url?.startsWith('http')
    ? sessionComplete.video_url
    : `${import.meta.env.VITE_API_URL || ''}${sessionComplete.video_url}`;

  return (
    <motion.div
      className="card p-6 bg-white rounded-2xl shadow-sm border border-gray-100"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">Record Live Session</h3>
        <div className="flex items-center space-x-2">
          <div className={`w-2.5 h-2.5 rounded-full ${isCameraOn ? 'bg-green-500' : 'bg-gray-400'}`} />
          <span className="text-xs text-gray-600">Camera {isCameraOn ? 'On' : 'Off'}</span>
        </div>
      </div>

      <div className="mb-3 grid grid-cols-2 gap-2 text-sm">
        <div>
          <div className="text-gray-500">Status</div>
          <div className="font-semibold text-gray-900">{status}</div>
        </div>
        <div>
          <div className="text-gray-500">SQLite video id</div>
          <div className="font-semibold text-gray-900">{sessionComplete?.video_id ?? 'Not saved'}</div>
        </div>
      </div>

      {error && (
        <div className="mb-3 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="relative bg-black rounded-xl overflow-hidden" style={{ aspectRatio: '16/9' }}>
          {sessionComplete?.video_url && (
            <video
              src={videoHref}
              controls
              className="block w-full h-full object-cover"
            />
          )}
          {!sessionComplete?.video_url && (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={isCameraOn ? 'block w-full h-full object-cover' : 'hidden'}
            />
          )}
          {!isCameraOn && !sessionComplete?.video_url && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-900/50">
              <span className="text-white text-sm">Camera is off</span>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium text-gray-700">Duration (seconds)</label>
            <input
              type="number"
              min={5}
              max={60}
              value={durationSeconds}
              onChange={(e) => setDurationSeconds(Number(e.target.value) || 15)}
              className="w-full mt-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Reference video id (optional)</label>
            <input
              type="number"
              min={1}
              value={referenceVideoId}
              onChange={(e) => setReferenceVideoId(e.target.value)}
              placeholder="SQLite video id"
              className="w-full mt-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Reference video path (optional)</label>
            <input
              type="text"
              value={referenceVideoPath}
              onChange={(e) => setReferenceVideoPath(e.target.value)}
              placeholder="backend/data/videos/recordings/ref.mp4"
              className="w-full mt-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleStart}
              disabled={status === 'recording' || status === 'processing'}
              className={`flex-1 py-3 rounded-lg font-semibold text-white transition-all ${
                status === 'recording' || status === 'processing'
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              Start Recording
            </button>
            <button
              onClick={handleStop}
              disabled={status !== 'recording'}
              className={`flex-1 py-3 rounded-lg font-semibold text-white transition-all ${
                status !== 'recording'
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              Stop
            </button>
          </div>

          {sessionComplete?.video_url && (
            <div className="p-4 rounded-xl bg-green-50 border border-green-200">
              <div className="text-sm font-semibold text-green-900 mb-2">Recorded clip saved</div>
              <div className="text-xs text-green-800 space-y-1">
                <div>Exercise: {sessionComplete.exercise_type}</div>
                <div>Duration: {durationLabel}s</div>
                <div>Frames: {sessionComplete.frames_processed ?? 'N/A'}</div>
                <div>Actual FPS: {sessionComplete.actual_fps ?? 'N/A'}</div>
                <div>Analysis: {sessionComplete.analysis_status ?? 'N/A'}</div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <a
                  className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-semibold"
                  href={videoHref}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open Video
                </a>
                <a
                  className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-white border border-green-300 hover:bg-green-50 text-green-800 text-sm font-semibold"
                  href={videoHref}
                  download={`exercise_${sessionComplete.exercise_type}_${sessionComplete.video_id}.mp4`}
                >
                  Download Video
                </a>
              </div>
            </div>
          )}

          {sessionComplete?.feedback && (
            <div className="p-4 rounded-xl bg-blue-50 border border-blue-200">
              <div className="text-sm font-semibold text-blue-900 mb-2">Analysis feedback</div>
              <p className="text-sm whitespace-pre-line text-blue-900">{sessionComplete.feedback}</p>
            </div>
          )}

          <canvas ref={canvasRef} className="hidden" />
        </div>
      </div>
    </motion.div>
  );
};

export default RecordSession;
