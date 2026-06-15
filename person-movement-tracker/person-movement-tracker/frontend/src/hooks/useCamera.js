import { useRef, useState, useCallback, useEffect } from 'react';

export const useCamera = (options = {}) => {
  const {
    width = 1280,
    height = 720,
    facingMode = 'user',
    onFrameCapture = null,
    captureInterval = 100
  } = options;

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);
  
  const [isActive, setIsActive] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState(null);
  const [lightingCondition, setLightingCondition] = useState('unknown');
  const [frameCount, setFrameCount] = useState(0);

  const analyzeLighting = useCallback((video) => {
    try {
      const canvas = document.createElement('canvas');
      canvas.width = 64;
      canvas.height = 64;
      const ctx = canvas.getContext('2d');
      
      ctx.drawImage(video, 0, 0, 64, 64);
      const imageData = ctx.getImageData(0, 0, 64, 64);
      const data = imageData.data;
      
      let sum = 0;
      let r, g, b;
      for (let i = 0; i < data.length; i += 4) {
        r = data[i];
        g = data[i + 1];
        b = data[i + 2];
        sum += (r + g + b) / 3;
      }
      
      const average = sum / (data.length / 4);
      
      if (average > 180) {
        setLightingCondition('bright');
      } else if (average > 80) {
        setLightingCondition('good');
      } else if (average > 40) {
        setLightingCondition('dim');
      } else {
        setLightingCondition('poor');
      }
      
      return lightingCondition;
    } catch (err) {
      return 'unknown';
    }
  }, []);

  const startCamera = useCallback(async () => {
    try {
      setError(null);
      
      const constraints = {
        video: {
          width: { ideal: width },
          height: { ideal: height },
          facingMode: facingMode,
          brightness: { ideal: 1.0 },
          contrast: { ideal: 1.0 }
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        
        await videoRef.current.play();
        
        setIsActive(true);
        setFrameCount(0);
      }
    } catch (err) {
      console.error('Error accessing camera:', err);
      let errorMessage = err.message || 'Failed to access camera';
      
      if (err.name === 'NotAllowedError') {
        errorMessage = 'Camera access denied. Please allow camera access in your browser settings.';
      } else if (err.name === 'NotFoundError') {
        errorMessage = 'No camera found. Please connect a camera and try again.';
      } else if (err.name === 'NotReadableError') {
        errorMessage = 'Camera is in use by another application.';
      }
      
      setError(errorMessage);
      setIsActive(false);
    }
  }, [width, height, facingMode]);

  const stopCamera = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    
    setIsActive(false);
    setLightingCondition('unknown');
  }, []);

  const startRecording = useCallback(async (onRecordingComplete) => {
    if (!streamRef.current) {
      setError('Camera not active');
      return false;
    }

    try {
      recordedChunksRef.current = [];
      
      const mediaRecorder = new MediaRecorder(streamRef.current, {
        mimeType: 'video/webm;codecs=vp9'
      });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(recordedChunksRef.current, { type: 'video/webm' });
        if (onRecordingComplete) {
          onRecordingComplete(blob);
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100);
      setIsRecording(true);
      
      return true;
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Failed to start recording');
      return false;
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      return true;
    }
    return false;
  }, []);

  const captureFrame = useCallback(() => {
    if (!videoRef.current || !isActive) {
      return null;
    }

    const video = videoRef.current;
    
    if (video.readyState !== 4) {
      return null;
    }

    const canvas = canvasRef.current || document.createElement('canvas');
    canvas.width = video.videoWidth || width;
    canvas.height = video.videoHeight || height;
    
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    
    if (!ctx) {
      return null;
    }
    
    ctx.drawImage(video, 0, 0);
    
    analyzeLighting(video);
    
    const imageData = canvas.toDataURL('image/jpeg', 0.85);
    setFrameCount(prev => prev + 1);
    
    return {
      dataUrl: imageData,
      canvas,
      width: canvas.width,
      height: canvas.height,
      timestamp: Date.now()
    };
  }, [isActive, width, height, analyzeLighting]);

  const getImageElement = useCallback(() => {
    if (!videoRef.current || !isActive) {
      return null;
    }
    return videoRef.current;
  }, [isActive]);

  const startCaptureLoop = useCallback((callback) => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    intervalRef.current = setInterval(() => {
      if (callback) {
        callback(captureFrame());
      }
    }, captureInterval);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [captureFrame, captureInterval]);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return {
    videoRef,
    canvasRef,
    isActive,
    isRecording,
    error,
    lightingCondition,
    frameCount,
    startCamera,
    stopCamera,
    captureFrame,
    getImageElement,
    startCaptureLoop,
    analyzeLighting,
    startRecording,
    stopRecording
  };
};

export default useCamera;
