import { useState, useRef, useCallback } from 'react';
import { trackExerciseFrame } from '../services/api';
import useLocalExerciseTracking from './useLocalExerciseTracking';

export function useExerciseTracking() {
  const [isExerciseProcessing, setIsExerciseProcessing] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState(null);
  const [useLocalMode, setUseLocalMode] = useState(true);
  const frameCountRef = useRef(0);
  const lastProcessTimeRef = useRef(0);
  const sessionIdRef = useRef(`exercise_${Date.now()}`);
  
  const localTracking = useLocalExerciseTracking();

  const processExerciseFrame = useCallback(async (canvas, exerciseType, setAnalysis) => {
    const now = Date.now();
    if (now - lastProcessTimeRef.current < 100) {
      return;
    }
    lastProcessTimeRef.current = now;

    if (isExerciseProcessing) {
      return;
    }

    setIsExerciseProcessing(true);

    try {
      if (useLocalMode) {
        if (!localTracking.isInitialized) {
          await localTracking.initialize();
        }
        
        const videoElement = canvas;
        const result = await localTracking.processFrame(videoElement);
        
        if (result && result.analysis) {
          const localAnalysis = {
            exercise: exerciseType,
            rep_count: localTracking.repCount,
            state: result.analysis.state,
            angles: result.analysis.angles || {},
            form_issues: result.analysis.issues || [],
            feedback: result.analysis.issues?.map(i => `${i.severity}: ${i.message}`) || [],
            form_score: result.analysis.formScore,
            summary: result.analysis.summary
          };
          setAnalysis(localAnalysis);
          setLastAnalysis(localAnalysis);
        }
      } else {
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        const base64Data = imageData.split(',')[1];
        const result = await trackExerciseFrame(base64Data, sessionIdRef.current, exerciseType);

        if (result.success && result.analysis) {
          setAnalysis(result.analysis);
          setLastAnalysis(result.analysis);
        }
      }

      frameCountRef.current++;
    } catch (error) {
      console.error('Error processing exercise frame:', error);
      
      if (useLocalMode) {
        console.log('Falling back to server-side processing...');
        setUseLocalMode(false);
      }
    } finally {
      setIsExerciseProcessing(false);
    }
  }, [isExerciseProcessing, useLocalMode, localTracking]);

  const resetExercise = useCallback(() => {
    frameCountRef.current = 0;
    setLastAnalysis(null);
    sessionIdRef.current = `exercise_${Date.now()}`;
    if (localTracking) {
      localTracking.setExercise('squat');
      localTracking.repCount = 0;
      localTracking.formScore = 100;
    }
  }, [localTracking]);

  const setExerciseType = useCallback((type) => {
    if (localTracking) {
      localTracking.setExercise(type);
    }
  }, [localTracking]);

  const saveSession = useCallback(async () => {
    return await localTracking.saveSession();
  }, [localTracking]);

  const toggleLocalMode = useCallback(() => {
    setUseLocalMode(prev => !prev);
  }, []);

  return {
    processExerciseFrame,
    isExerciseProcessing,
    resetExercise,
    lastAnalysis,
    frameCount: frameCountRef.current,
    useLocalMode,
    setExerciseType,
    saveSession,
    toggleLocalMode,
    localTracking
  };
}
