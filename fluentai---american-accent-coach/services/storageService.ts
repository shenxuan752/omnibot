import { HistorySession, AnalysisResult } from '../types';

const STORAGE_KEY = 'fluentai_history';

export const saveSession = (text: string, result: AnalysisResult) => {
  try {
    const existingData = localStorage.getItem(STORAGE_KEY);
    const history: HistorySession[] = existingData ? JSON.parse(existingData) : [];
    
    // Check if the most recent entry (index 0) has the same text.
    // This handles the "Retry" case where we want to update the latest attempt 
    // rather than spamming history with duplicates of the same sentence.
    if (history.length > 0 && history[0].text.trim() === text.trim()) {
       history[0].result = result;
       history[0].timestamp = Date.now();
       // We keep the original ID to maintain referential integrity if needed, 
       // or we could update it. Updating timestamp is sufficient.
    } else {
       // New session
       const newSession: HistorySession = {
         id: crypto.randomUUID(),
         timestamp: Date.now(),
         text,
         result
       };
       history.unshift(newSession);
    }
    
    // Limit to last 50 sessions
    if (history.length > 50) {
      history.pop();
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  } catch (error) {
    console.error("Failed to save session:", error);
  }
};

export const getHistory = (): HistorySession[] => {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error("Failed to load history:", error);
    return [];
  }
};

export const clearHistory = () => {
  localStorage.removeItem(STORAGE_KEY);
};