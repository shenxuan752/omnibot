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

export interface WebAppUser {
  id: number;
  is_bot?: boolean;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
}

export interface WebApp {
  initData: string;
  initDataUnsafe: {
    query_id?: string;
    user?: WebAppUser;
    auth_date?: string;
    hash?: string;
  };
  version: string;
  platform: string;
  colorScheme: 'light' | 'dark';
  themeParams: {
    bg_color?: string;
    text_color?: string;
    hint_color?: string;
    link_color?: string;
    button_color?: string;
    button_text_color?: string;
  };
  isExpanded: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  headerColor: string;
  backgroundColor: string;
  isClosingConfirmationEnabled: boolean;
  BackButton: {
    isVisible: boolean;
    onClick: (callback: () => void) => void;
    offClick: (callback: () => void) => void;
    show: () => void;
    hide: () => void;
  };
  MainButton: {
    text: string;
    color: string;
    textColor: string;
    isVisible: boolean;
    isActive: boolean;
    isProgressVisible: boolean;
    setText: (text: string) => void;
    onClick: (callback: () => void) => void;
    offClick: (callback: () => void) => void;
    show: () => void;
    hide: () => void;
    enable: () => void;
    disable: () => void;
    showProgress: (leaveActive: boolean) => void;
    hideProgress: () => void;
  };
  HapticFeedback: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
    selectionChanged: () => void;
  };
  ready: () => void;
  expand: () => void;
  close: () => void;
  setHeaderColor: (color: string) => void;
  setBackgroundColor: (color: string) => void;
}