import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://jexqgfbvilrlpadrbxwc.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblOGnPJi';

let supabase = null;
let supabaseInitialized = false;
let supabaseInitError = null;

const initializeSupabase = () => {
  if (supabaseInitialized) {
    return supabase;
  }
  
  try {
    if (supabaseUrl && supabaseAnonKey) {
      supabase = createClient(supabaseUrl, supabaseAnonKey);
    }
    supabaseInitialized = true;
    return supabase;
  } catch (error) {
    console.warn('Failed to initialize Supabase client:', error);
    supabaseInitError = error;
    supabaseInitialized = true;
    return null;
  }
};

export const isSupabaseConfigured = () => {
  initializeSupabase();
  return supabase !== null;
};

export const supabaseService = {
  async initialize(userId) {
    const supabaseClient = initializeSupabase();
    if (!supabaseClient) {
      console.warn('Supabase not configured');
      return false;
    }
    try {
      const { data, error } = await supabaseClient
        .from('users')
        .upsert({ id: userId, updated_at: new Date().toISOString() })
        .select();
      if (error) throw error;
      return true;
    } catch (error) {
      console.error('Supabase initialization error:', error);
      return false;
    }
  },

  async saveExerciseSession(userId, sessionData) {
    const supabaseClient = initializeSupabase();
    if (!supabaseClient) return { success: false, error: 'Supabase not configured' };
    try {
      const { data, error } = await supabaseClient
        .from('users')
        .upsert({ id: userId, updated_at: new Date().toISOString() })
        .select();
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      console.error('Error saving exercise session:', error);
      return { success: false, error: error.message };
    }
  },

  async getExerciseSessions(userId, limit = 50) {
    const supabaseClient = initializeSupabase();
    if (!supabaseClient) return { success: false, error: 'Supabase not configured', data: [] };
    try {
      const { data, error } = await supabaseClient
        .from('exercise_sessions')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
        .limit(limit);
      if (error) throw error;
      return { success: true, data: data || [] };
    } catch (error) {
      console.error('Error getting exercise sessions:', error);
      return { success: false, error: error.message, data: [] };
    }
  },

  async syncLocalData(userId, localData) {
    const supabaseClient = initializeSupabase();
    if (!supabaseClient) return { success: false, error: 'Supabase not configured' };
    try {
      const sessions = localData.exerciseHistory || [];
      const results = { synced: 0, failed: 0 };
      for (const session of sessions) {
        const result = await this.saveExerciseSession(userId, {
          id: session.id,
          exerciseType: session.exerciseType,
          repCount: session.repCount,
          formScore: session.formScore,
          duration: session.duration,
          feedback: session.feedback,
          timestamp: session.timestamp
        });
        if (result.success) results.synced++;
        else results.failed++;
      }
      return { success: true, ...results };
    } catch (error) {
      console.error('Error syncing local data:', error);
      return { success: false, error: error.message };
    }
  },

  async getUserStats(userId) {
    const supabaseClient = initializeSupabase();
    if (!supabaseClient) return { success: false, error: 'Supabase not configured' };
    try {
      const { data, error } = await supabaseClient
        .from('exercise_sessions')
        .select('exercise_type, form_score, rep_count, created_at')
        .eq('user_id', userId);
      if (error) throw error;
      
      const stats = {
        totalSessions: data.length,
        averageFormScore: 0,
        totalReps: 0,
        byExercise: {}
      };
      
      if (data.length > 0) {
        stats.averageFormScore = data.reduce((sum, s) => sum + (s.form_score || 0), 0) / data.length;
        stats.totalReps = data.reduce((sum, s) => sum + (s.rep_count || 0), 0);
        data.forEach(s => {
          const type = s.exercise_type;
          if (!stats.byExercise[type]) {
            stats.byExercise[type] = { sessions: 0, avgScore: 0, totalReps: 0 };
          }
          stats.byExercise[type].sessions++;
          stats.byExercise[type].totalReps += s.rep_count || 0;
        });
        Object.keys(stats.byExercise).forEach(type => {
          const exerciseData = data.filter(d => d.exercise_type === type);
          stats.byExercise[type].avgScore = exerciseData.reduce((sum, s) => sum + (s.form_score || 0), 0) / exerciseData.length;
        });
      }
      
      return { success: true, stats };
    } catch (error) {
      console.error('Error getting user stats:', error);
      return { success: false, error: error.message };
    }
  },

  async deleteSession(sessionId) {
    const supabaseClient = initializeSupabase();
    if (!supabaseClient) return { success: false, error: 'Supabase not configured' };
    try {
      const { error } = await supabaseClient
        .from('exercise_sessions')
        .delete()
        .eq('session_id', sessionId);
      if (error) throw error;
      return { success: true };
    } catch (error) {
      console.error('Error deleting session:', error);
      return { success: false, error: error.message };
    }
  },

  async updateUserProfile(userId, profileData) {
    const supabaseClient = initializeSupabase();
    if (!supabaseClient) return { success: false, error: 'Supabase not configured' };
    try {
      const { data, error } = await supabaseClient
        .from('user_profiles')
        .upsert({
          user_id: userId,
          ...profileData,
          updated_at: new Date().toISOString()
        })
        .select();
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      console.error('Error updating profile:', error);
      return { success: false, error: error.message };
    }
  }
};

export default supabaseService;