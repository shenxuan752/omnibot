export interface WordAnalysis {
  word: string;
  isCorrect: boolean;
  phoneticReceived?: string;
  phoneticExpected?: string;
  explanation?: string; // e.g., "Replaced 'zh' with 'r'"
}

export interface AnalysisResult {
  overallScore: number;
  phonemeAccuracy: number;
  flowRhythmScore: number;
  wordBreakdown: WordAnalysis[];
  coachNotes: string; // The "Coach's Notes" paragraph
  specificFixes: string[]; // Bullet points for fixes
  problemWords: string[]; // List of words to copy
}

export interface HistorySession {
  id: string;
  timestamp: number;
  text: string;
  result: AnalysisResult;
}

export enum AppState {
  LANDING = 'LANDING',
  PRACTICE = 'PRACTICE',
  ANALYZING = 'ANALYZING',
  RESULTS = 'RESULTS',
  HISTORY = 'HISTORY',
}

export interface TextChallenge {
  text: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  focus: string; // e.g., "R sounds", "TH sounds"
}

// Global definition for Telegram WebApp
declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        ready: () => void;
        expand: () => void;
        close: () => void;
        initDataUnsafe?: any;
        MainButton: {
          text: string;
          show: () => void;
          hide: () => void;
          onClick: (cb: () => void) => void;
        };
      };
    };
  }
}