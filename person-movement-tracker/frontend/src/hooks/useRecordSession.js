import { useCallback, useEffect, useRef, useState } from 'react';

export const useRecordSession = ({
  wsUrl = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000') + '/ws/record-session',
  durationSeconds = 15,
} = {}) => {
  const wsRef = useRef(null);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);
  const [sessionComplete, setSessionComplete] = useState(null);
  const [exerciseType, setExerciseType] = useState('squat');

  const connect = useCallback(() => {
    return new Promise((resolve, reject) => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => resolve();
        ws.onerror = (evt) => reject(evt);
        ws.onmessage = (evt) => {
          try {
            const msg = JSON.parse(evt.data);

            if (msg.type === 'config_ack') {
              setStatus('recording');
              return;
            }

            if (msg.type === 'recording_started') {
              setStatus('recording');
              return;
            }

            if (msg.type === 'recording_stopped') {
              setStatus('processing');
              return;
            }

            if (msg.type === 'session_complete') {
              setSessionComplete(msg);
              setStatus('complete');
              return;
            }

            if (msg.type === 'error') {
              setError(msg.message || 'Recording error');
              setStatus('error');
            }
          } catch (_) {}
        };
      } catch (err) {
        reject(err);
      }
    });
  }, [wsUrl]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    wsRef.current = null;
  }, []);

  const sendConfig = useCallback(
    (type, options = {}) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
      wsRef.current.send(
        JSON.stringify({
          config: {
            exercise_type: type || exerciseType,
            duration_seconds: options.durationSeconds ?? durationSeconds,
            reference_video_id: options.referenceVideoId ?? null,
            reference_video_path: options.referenceVideoPath ?? null,
          },
        })
      );
    },
    [durationSeconds, exerciseType]
  );

  const sendFrameDataUrl = useCallback((dataUrl) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ image: dataUrl }));
  }, []);

  const start = useCallback(
    async ({ type, referenceVideoId = null, referenceVideoPath = null } = {}) => {
      setError(null);
      setSessionComplete(null);
      setExerciseType(type || 'squat');
      setStatus('idle');

      await connect();
      // Check if WebSocket is still open after connecting
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setError('WebSocket connection lost');
        setStatus('error');
        return;
      }
      sendConfig(type || exerciseType || 'squat', {
        durationSeconds,
        referenceVideoId,
        referenceVideoPath,
      });
    },
    [connect, durationSeconds, exerciseType, sendConfig]
  );

  const stop = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ command: 'stop' }));
  }, []);

  useEffect(() => {
    return () => disconnect();
  }, [disconnect]);

  return {
    status,
    error,
    sessionComplete,
    exerciseType,
    start,
    stop,
    sendFrameDataUrl,
  };
};

export default useRecordSession;