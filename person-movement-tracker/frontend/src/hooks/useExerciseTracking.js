import { useState, useRef, useCallback } from 'react';  
import { trackExerciseFrame } from '../services/api';  
  
export function useExerciseTracking() {  
  const [isExerciseProcessing, setIsExerciseProcessing] = useState(false);  
  const [lastAnalysis, setLastAnalysis] = useState(null);  
  const frameCountRef = useRef(0);  
  const lastProcessTimeRef = useRef(0);  
  const sessionIdRef = useRef(`exercise_${Date.now()}`);  
  
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
      const imageData = canvas.toDataURL('image/jpeg', 0.8);  
      const base64Data = imageData.split(',')[1];  
      const result = await trackExerciseFrame(base64Data, sessionIdRef.current, exerciseType);  
  
      if (result.success && result.analysis) {  
        setAnalysis(result.analysis);  
        setLastAnalysis(result.analysis);  
      }  
  
      frameCountRef.current++;  
    } catch (error) {  
      console.error('Error processing exercise frame:', error);  
    } finally {  
      setIsExerciseProcessing(false);  
    }  
  }, [isExerciseProcessing]);  
  
  const resetExercise = useCallback(() => {  
    frameCountRef.current = 0;  
    setLastAnalysis(null);  
    sessionIdRef.current = `exercise_${Date.now()}`;  
  }, []);  
  
  return {  
    processExerciseFrame,  
    isExerciseProcessing,  
    resetExercise,  
    lastAnalysis,  
    frameCount: frameCountRef.current  
  };  
} 
