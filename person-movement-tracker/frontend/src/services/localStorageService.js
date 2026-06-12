const STORAGE_KEYS = {
  SESSIONS: 'person_tracker_sessions',
  SETTINGS: 'person_tracker_settings',
  EXERCISE_HISTORY: 'exercise_history',
  USER_PREFERENCES: 'user_preferences'
};

export const storageService = {
  saveSession(sessionData) {
    try {
      const sessions = this.getSessions();
      const newSession = {
        id: sessionData.id || `session_${Date.now()}`,
        timestamp: new Date().toISOString(),
        ...sessionData
      };
      sessions.unshift(newSession);
      const limitedSessions = sessions.slice(0, 100);
      localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(limitedSessions));
      return newSession;
    } catch (error) {
      console.error('Error saving session:', error);
      return null;
    }
  },

  getSessions() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.SESSIONS);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting sessions:', error);
      return [];
    }
  },

  getSession(sessionId) {
    const sessions = this.getSessions();
    return sessions.find(s => s.id === sessionId);
  },

  deleteSession(sessionId) {
    try {
      const sessions = this.getSessions();
      const filtered = sessions.filter(s => s.id !== sessionId);
      localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(filtered));
      return true;
    } catch (error) {
      console.error('Error deleting session:', error);
      return false;
    }
  },

  clearSessions() {
    localStorage.removeItem(STORAGE_KEYS.SESSIONS);
  },

  saveExerciseResult(result) {
    try {
      const history = this.getExerciseHistory();
      history.unshift({
        id: `exercise_${Date.now()}`,
        timestamp: new Date().toISOString(),
        ...result
      });
      const limited = history.slice(0, 500);
      localStorage.setItem(STORAGE_KEYS.EXERCISE_HISTORY, JSON.stringify(limited));
      return true;
    } catch (error) {
      console.error('Error saving exercise result:', error);
      return false;
    }
  },

  getExerciseHistory() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.EXERCISE_HISTORY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting exercise history:', error);
      return [];
    }
  },

  getExerciseHistoryByType(exerciseType) {
    const history = this.getExerciseHistory();
    return history.filter(h => h.exerciseType === exerciseType);
  },

  saveSettings(settings) {
    try {
      localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(settings));
      return true;
    } catch (error) {
      console.error('Error saving settings:', error);
      return false;
    }
  },

  getSettings() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.SETTINGS);
      return data ? JSON.parse(data) : {
        cameraFacing: 'user',
        videoQuality: '720p',
        processingInterval: 100,
        soundFeedback: true,
        showSkeleton: true
      };
    } catch (error) {
      console.error('Error getting settings:', error);
      return {};
    }
  },

  saveUserPreferences(prefs) {
    try {
      const current = this.getUserPreferences();
      const updated = { ...current, ...prefs };
      localStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(updated));
      return true;
    } catch (error) {
      console.error('Error saving user preferences:', error);
      return false;
    }
  },

  getUserPreferences() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.USER_PREFERENCES);
      return data ? JSON.parse(data) : {
        name: '',
        fitnessLevel: 'beginner',
        goals: []
      };
    } catch (error) {
      console.error('Error getting user preferences:', error);
      return {};
    }
  },

  exportData() {
    return {
      sessions: this.getSessions(),
      exerciseHistory: this.getExerciseHistory(),
      settings: this.getSettings(),
      preferences: this.getUserPreferences(),
      exportDate: new Date().toISOString()
    };
  },

  importData(data) {
    try {
      if (data.sessions) {
        localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(data.sessions));
      }
      if (data.exerciseHistory) {
        localStorage.setItem(STORAGE_KEYS.EXERCISE_HISTORY, JSON.stringify(data.exerciseHistory));
      }
      if (data.settings) {
        localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(data.settings));
      }
      if (data.preferences) {
        localStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(data.preferences));
      }
      return true;
    } catch (error) {
      console.error('Error importing data:', error);
      return false;
    }
  },

  clearAll() {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
  },

  getStorageUsage() {
    let total = 0;
    Object.values(STORAGE_KEYS).forEach(key => {
      const data = localStorage.getItem(key);
      if (data) {
        total += data.length * 2;
      }
    });
    return {
      bytes: total,
      kb: (total / 1024).toFixed(2),
      mb: (total / (1024 * 1024)).toFixed(2)
    };
  }
};

export default storageService;
