import { useState, useCallback, useRef, useEffect } from 'react';
import { poseDetector } from '../services/poseDetectorService';
import storageService from '../services/localStorageService';
import supabaseService, { isSupabaseConfigured } from '../services/supabaseService';

export const useLocalExerciseTracking = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [repCount, setRepCount] = useState(0);
  const [formScore, setFormScore] = useState(100);
  const [exerciseHistory, setExerciseHistory] = useState([]);
  const [error, setError] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  
  const currentExerciseRef = useRef('squat');
  const lastStateRef = useRef('start');
  const sessionIdRef = useRef(`local_session_${Date.now()}`);
  const userIdRef = useRef(`user_${localStorage.getItem('device_id') || Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    localStorage.setItem('device_id', userIdRef.current);
    loadHistory();
    initializePoseDetector();
    
    return () => {
    };
  }, []);

  const loadHistory = useCallback(() => {
    const history = storageService.getExerciseHistory();
    setExerciseHistory(history);
  }, []);

  const initializePoseDetector = useCallback(async () => {
    try {
      const success = await poseDetector.initialize();
      setIsInitialized(success);
      console.log('Pose detector initialized:', success);
      return success;
    } catch (err) {
      console.error('Failed to initialize pose detector:', err);
      setError(err.message);
      return false;
    }
  }, []);

  const initialize = useCallback(async (onResults) => {
    return await initializePoseDetector();
  }, [initializePoseDetector]);

  const processFrame = useCallback(async (videoElement) => {
    if (!isInitialized) {
      await initializePoseDetector();
    }

    setIsProcessing(true);

    try {
      const results = await poseDetector.detectPose(videoElement);
      
      if (!results || !results.poseLandmarks) {
        setIsProcessing(false);
        return null;
      }

      const landmarks = results.poseLandmarks;
      const exerciseType = currentExerciseRef.current;
      const analysis = poseDetector.analyze(exerciseType, landmarks);

      if (analysis && analysis.valid) {
        setCurrentAnalysis(analysis);
        
        if (analysis.formScore !== undefined) {
          setFormScore(analysis.formScore);
        }

        if (lastStateRef.current !== analysis.state) {
          if (lastStateRef.current === 'end' && analysis.state === 'start') {
            setRepCount(prev => prev + 1);
          }
          lastStateRef.current = analysis.state;
        }

        setIsProcessing(false);
        return {
          landmarks,
          analysis,
          timestamp: Date.now()
        };
      }
      
      setIsProcessing(false);
      return null;
    } catch (err) {
      console.error('Error processing frame:', err);
      setIsProcessing(false);
      return null;
    }
  }, [isInitialized, initializePoseDetector]);

  const setExercise = useCallback((exerciseType) => {
    currentExerciseRef.current = exerciseType;
    setRepCount(0);
    setFormScore(100);
    lastStateRef.current = 'start';
  }, []);

  const saveSession = useCallback(async () => {
    const sessionData = {
      id: sessionIdRef.current,
      exerciseType: currentExerciseRef.current,
      repCount,
      formScore,
      timestamp: new Date().toISOString()
    };

    storageService.saveExerciseResult(sessionData);
    setExerciseHistory(prev => [sessionData, ...prev].slice(0, 100));

    if (isSupabaseConfigured()) {
      await supabaseService.saveExerciseSession(userIdRef.current, sessionData);
    }

    return sessionData;
  }, [repCount, formScore]);

  const clearHistory = useCallback(() => {
    storageService.clearAll();
    setExerciseHistory([]);
    setRepCount(0);
    setFormScore(100);
  }, []);

  const syncToCloud = useCallback(async () => {
    if (!isSupabaseConfigured()) {
      return { success: false, error: 'Supabase not configured' };
    }

    const localData = {
      exerciseHistory: storageService.getExerciseHistory()
    };

    return await supabaseService.syncLocalData(userIdRef.current, localData);
  }, []);

  const getStats = useCallback(async () => {
    const localStats = {
      totalSessions: exerciseHistory.length,
      averageFormScore: exerciseHistory.length > 0 
        ? exerciseHistory.reduce((sum, s) => sum + (s.formScore || 0), 0) / exerciseHistory.length
        : 0,
      totalReps: exerciseHistory.reduce((sum, s) => sum + (s.repCount || 0), 0),
      byExercise: {}
    };

    exerciseHistory.forEach(s => {
      const type = s.exerciseType;
      if (!localStats.byExercise[type]) {
        localStats.byExercise[type] = { sessions: 0, totalReps: 0, avgScore: 0 };
      }
      localStats.byExercise[type].sessions++;
      localStats.byExercise[type].totalReps += s.repCount || 0;
    });

    Object.keys(localStats.byExercise).forEach(type => {
      const typeSessions = exerciseHistory.filter(s => s.exerciseType === type);
      localStats.byExercise[type].avgScore = typeSessions.length > 0
        ? typeSessions.reduce((sum, s) => sum + (s.formScore || 0), 0) / typeSessions.length
        : 0;
    });

    if (isSupabaseConfigured()) {
      const cloudStats = await supabaseService.getUserStats(userIdRef.current);
      if (cloudStats.success) {
        return { local: localStats, cloud: cloudStats.stats, synced: true };
      }
    }

    return { local: localStats, synced: false };
  }, [exerciseHistory]);

  return {
    isProcessing,
    currentAnalysis,
    repCount,
    formScore,
    exerciseHistory,
    error,
    isInitialized,
    currentExercise: currentExerciseRef.current,
    sessionId: sessionIdRef.current,
    initialize,
    processFrame,
    setExercise,
    saveSession,
    clearHistory,
    syncToCloud,
    getStats,
    loadHistory
  };
};

export default useLocalExerciseTracking;
