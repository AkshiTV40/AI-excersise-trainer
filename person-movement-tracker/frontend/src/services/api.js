import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const api = {
  // Track a single frame
  trackFrame: async (data) => {
    try {
      const response = await apiClient.post('/api/track', data);
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // Upload image file for tracking
  trackFile: async (file, modelType = 'yolov8', enableTracking = true) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('model_type', modelType);
      formData.append('enable_tracking', enableTracking);

      const response = await apiClient.post('/api/track/file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // Get available models
  getModels: async () => {
    try {
      const response = await apiClient.get('/api/models');
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // Get device information
  getDeviceInfo: async () => {
    try {
      const response = await apiClient.get('/api/device');
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // Get session statistics
  getSessionStats: async (sessionId) => {
    try {
      const response = await apiClient.get(`/api/session/${sessionId}/stats`);
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // Health check
  healthCheck: async () => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // Exercise tracking
  trackExerciseFrame: async (imageData, sessionId, exerciseType, enableTracking = true) => {
    try {
      const response = await apiClient.post('/api/exercise/track', {
        image: imageData,
        session_id: sessionId,
        exercise_type: exerciseType,
        enable_tracking: enableTracking
      });
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // Analyze uploaded exercise video
  trackExerciseVideo: async (file, exerciseType = 'squat', referenceUrl = null, maxSeconds = 10) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('exercise_type', exerciseType);
      if (referenceUrl) {
        formData.append('reference_url', referenceUrl);
      }
      formData.append('max_seconds', maxSeconds);

      const response = await apiClient.post('/api/exercise/track/video', formData, {
        headers: {'Content-Type': 'multipart/form-data'},
        timeout: 120000,
      });
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // Get supported exercise types
  getExerciseTypes: async () => {
    try {
      const response = await apiClient.get('/api/exercise/types');
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // Reset exercise tracking
  resetExerciseTracking: async (exerciseType) => {
    try {
      const response = await apiClient.post('/api/exercise/reset', null, {
        params: { exercise_type: exerciseType }
      });
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },
};

export const trackExerciseFrame = api.trackExerciseFrame;
export const trackExerciseVideo = api.trackExerciseVideo;
export const trackFrame = api.trackFrame;
export const trackFile = api.trackFile;
export const getExerciseTypes = api.getExerciseTypes;
export const resetExerciseTracking = api.resetExerciseTracking;
export const getSessionStats = api.getSessionStats;
export const healthCheck = api.healthCheck;

export default apiClient;