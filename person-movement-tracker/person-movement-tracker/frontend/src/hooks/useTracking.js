import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '../services/api';

export const useTracking = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);
  const sessionIdRef = useRef(`session_${Date.now()}`);

  const processFrame = useCallback(async (imageData, modelType = 'yolov8', enableTracking = true) => {
    try {
      setError(null);
      
      const response = await api.trackFrame({
        image: imageData,
        session_id: sessionIdRef.current,
        model_type: modelType,
        enable_tracking: enableTracking
      });

      if (response.success) {
        setResults(response);
        return response;
      } else {
        throw new Error(response.error || 'Processing failed');
      }
    } catch (err) {
      console.error('Tracking error:', err);
      setError(err.message);
      return null;
    }
  }, []);

  const startTracking = useCallback((captureFrame, onFrameProcessed, options = {}) => {
    const { interval = 100, modelType = 'yolov8' } = options;
    
    setIsProcessing(true);
    
    intervalRef.current = setInterval(async () => {
      const frame = captureFrame();
      
      if (frame) {
        const result = await processFrame(frame, modelType);
        
        if (result && onFrameProcessed) {
          onFrameProcessed(result);
        }
      }
    }, interval);
  }, [processFrame]);

  const stopTracking = useCallback(() => {
    setIsProcessing(false);
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopTracking();
    };
  }, [stopTracking]);

  return {
    isProcessing,
    results,
    error,
    processFrame,
    startTracking,
    stopTracking,
    sessionId: sessionIdRef.current
  };
};