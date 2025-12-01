import React, { useState, useRef } from 'react';
import { AppState, AnalysisResult, HistorySession } from './types';
import { generateChallenge, analyzePronunciation } from './services/geminiService';
import { saveSession, getHistory } from './services/storageService';
import { initTelegramApp, getTelegramUser } from './services/telegramService';
import AnalysisView from './components/AnalysisView';
import { Mic, Square, Edit3, Sparkles, ArrowRight, Loader2, History, ChevronRight, Calendar, User, Database } from 'lucide-react';

const App: React.FC = () => {
  const [appState, setAppState] = useState<AppState>(AppState.LANDING);
  const [practiceText, setPracticeText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [recordingMimeType, setRecordingMimeType] = useState<string>("");
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  // History State
  const [history, setHistory] = useState<HistorySession[]>([]);

  const [telegramUser, setTelegramUser] = useState<any>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  // Initialize Telegram Web App
  React.useEffect(() => {
    const isTg = initTelegramApp();
    if (isTg) {
      const user = getTelegramUser();
      if (user) setTelegramUser(user);
    }
  }, []);

  // Navigation handlers
  const startChallenge = async () => {
    setAppState(AppState.PRACTICE);
    setPracticeText("Loading challenge...");

    // Get latest history to enable adaptive learning
    const currentHistory = getHistory();
    setHistory(currentHistory);

    const text = await generateChallenge(currentHistory);
    setPracticeText(text);
  };

  const writeOwn = () => {
    setPracticeText("");
    setAppState(AppState.PRACTICE);
  };

  const showHistory = () => {
    setHistory(getHistory());
    setAppState(AppState.HISTORY);
  };

  const loadHistorySession = (session: HistorySession) => {
    setPracticeText(session.text);
    setAnalysisResult(session.result);
    setAudioUrl(null); // We don't save large audio blobs in local storage
    setAudioBlob(null);
    setAppState(AppState.RESULTS);
  };

  const getSupportedMimeType = () => {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/aac',
      'audio/ogg'
    ];
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    return ''; // Browser default
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = getSupportedMimeType();
      setRecordingMimeType(mimeType);

      const options = mimeType ? { mimeType } : undefined;
      mediaRecorderRef.current = new MediaRecorder(stream, options);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const type = mimeType || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
      };

      mediaRecorderRef.current.start(100);
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Please allow microphone access to use this app.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const analyze = async () => {
    if (!audioBlob) return;
    setAppState(AppState.ANALYZING);

    const result = await analyzePronunciation(audioBlob, practiceText, recordingMimeType || 'audio/webm');

    // Save to history
    saveSession(practiceText, result);

    setAnalysisResult(result);
    setAppState(AppState.RESULTS);
  };

  // --- Views ---

  const renderLanding = () => (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="bg-slate-900 p-10 rounded-3xl shadow-2xl shadow-black/50 max-w-md w-full text-center border border-slate-800 relative overflow-hidden">
        {/* Decorative background blur */}
        <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-600/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="flex justify-center mb-6 relative z-10">
          <div className="bg-slate-800 p-4 rounded-2xl border border-slate-700 shadow-inner">
            <Sparkles className="text-blue-400 w-8 h-8" />
          </div>
        </div>
        <h1 className="text-3xl font-bold text-white mb-3 relative z-10">
          Fluent<span className="text-blue-500">AI</span>
        </h1>
        {telegramUser && (
          <p className="text-blue-400 mb-2 font-medium relative z-10">
            Welcome, {telegramUser.first_name}!
          </p>
        )}
        <p className="text-slate-400 mb-8 leading-relaxed text-sm relative z-10">
          Your AI-powered dialect coach. Master the American accent with real-time phoneme analysis and rhythm feedback.
        </p>

        <div className="space-y-3 relative z-10">
          <button
            onClick={startChallenge}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-4 px-6 rounded-xl transition-all shadow-lg shadow-blue-900/30 flex items-center justify-center gap-2 group"
          >
            <Sparkles size={18} className="text-blue-200 group-hover:text-white" />
            Generate Challenge
          </button>
          <button
            onClick={writeOwn}
            className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold py-4 px-6 rounded-xl transition-all flex items-center justify-center gap-2"
          >
            <Edit3 size={18} /> Write My Own
          </button>
          <button
            onClick={showHistory}
            className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold py-4 px-6 rounded-xl transition-all flex items-center justify-center gap-2"
          >
            <Database size={18} /> View History
          </button>
        </div>
      </div>
      <p className="mt-8 text-slate-600 text-xs">Powered by Gemini 2.5 Flash</p>
    </div>
  );

  const renderHistory = () => (
    <div className="min-h-screen pt-10 px-4 pb-20 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <button
          onClick={() => setAppState(AppState.LANDING)}
          className="bg-slate-900 border border-slate-800 p-2 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          <ArrowRight size={20} className="rotate-180" />
        </button>
        <h2 className="text-2xl font-bold text-white">Practice History</h2>
      </div>

      {history.length === 0 ? (
        <div className="text-center py-20 bg-slate-900 rounded-2xl border border-slate-800">
          <div className="inline-block p-4 bg-slate-800 rounded-full mb-4">
            <History className="text-slate-500 w-8 h-8" />
          </div>
          <p className="text-slate-400">No practice sessions found.</p>
          <button
            onClick={() => setAppState(AppState.LANDING)}
            className="mt-4 text-blue-400 font-medium hover:text-blue-300 transition-colors"
          >
            Start practicing
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {history.map(session => (
            <button
              key={session.id}
              onClick={() => loadHistorySession(session)}
              className="w-full bg-slate-900 p-6 rounded-2xl border border-slate-800 hover:border-slate-600 shadow-sm hover:shadow-lg hover:shadow-blue-900/10 transition-all text-left group relative overflow-hidden"
            >
              <div className="flex justify-between items-start mb-3 relative z-10">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-500 uppercase tracking-wider">
                  <Calendar size={12} />
                  {new Date(session.timestamp).toLocaleDateString()}
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-bold border ${session.result.overallScore >= 80 ? 'bg-green-900/20 text-green-400 border-green-900/30' :
                  session.result.overallScore >= 50 ? 'bg-amber-900/20 text-amber-400 border-amber-900/30' :
                    'bg-red-900/20 text-red-400 border-red-900/30'
                  }`}>
                  {session.result.overallScore}% Score
                </div>
              </div>
              <h3 className="text-slate-200 font-serif text-lg line-clamp-2 mb-2 group-hover:text-blue-400 transition-colors relative z-10">
                "{session.text}"
              </h3>
              <div className="flex items-center gap-1 text-sm text-slate-500 font-medium group-hover:text-blue-400 transition-colors relative z-10">
                Review Analysis <ChevronRight size={14} />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );

  const renderPractice = () => (
    <div className="min-h-screen flex flex-col items-center pt-10 p-4">
      <div className="max-w-2xl w-full">
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => setAppState(AppState.LANDING)}
            className="text-slate-500 hover:text-slate-300 transition-colors"
          >
            <ArrowRight size={20} className="rotate-180" />
          </button>
          <span className="font-medium text-slate-500">Practice Session</span>
        </div>

        <div className="bg-slate-900 rounded-2xl p-8 shadow-lg shadow-black/20 border border-slate-800 mb-6">
          <div className="flex items-center gap-2 mb-4 text-blue-400 font-medium text-sm uppercase tracking-wide">
            <Edit3 size={16} />
            <span>Practice Text</span>
          </div>
          <textarea
            value={practiceText}
            onChange={(e) => setPracticeText(e.target.value)}
            className="w-full text-2xl font-serif text-slate-200 bg-transparent border-none focus:ring-0 resize-none placeholder-slate-600 leading-relaxed"
            rows={4}
            placeholder="Enter text to practice..."
          />
        </div>

        <div className="bg-slate-900 rounded-2xl p-12 shadow-lg shadow-black/20 border border-slate-800 flex flex-col items-center justify-center min-h-[300px] relative overflow-hidden">
          {/* Background glow for recording state */}
          {isRecording && <div className="absolute inset-0 bg-red-500/5 animate-pulse"></div>}

          {!audioBlob ? (
            <>
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 relative z-10 ${isRecording
                  ? 'bg-red-500 shadow-red-900/50 animate-pulse shadow-2xl scale-110'
                  : 'bg-blue-600 hover:bg-blue-500 shadow-blue-900/50 shadow-2xl'
                  }`}
              >
                {isRecording ? <Square className="text-white w-8 h-8" /> : <Mic className="text-white w-8 h-8" />}
              </button>
              <p className={`mt-8 font-medium transition-colors relative z-10 ${isRecording ? 'text-red-400' : 'text-slate-400'}`}>
                {isRecording ? "Listening... Read the text above." : "Tap microphone to record"}
              </p>
            </>
          ) : (
            <div className="w-full text-center relative z-10">
              <div className="mb-8">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-900/20 text-green-400 rounded-full border border-green-900/30 mb-6">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  Recording Captured
                </div>
                <audio src={audioUrl!} controls className="mx-auto w-full max-w-sm opacity-80 hover:opacity-100 transition-opacity" />
              </div>
              <div className="flex gap-4 justify-center">
                <button
                  onClick={() => { setAudioBlob(null); setAudioUrl(null); }}
                  className="px-6 py-3 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-all font-medium"
                >
                  Record Again
                </button>
                <button
                  onClick={analyze}
                  className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium shadow-lg shadow-blue-900/30 transition-all flex items-center gap-2"
                >
                  Start Analysis <ArrowRight size={18} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderAnalyzing = () => (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-blue-500 blur-xl opacity-20 rounded-full"></div>
        <Loader2 className="w-16 h-16 text-blue-500 animate-spin relative z-10" />
      </div>
      <h2 className="text-3xl font-bold text-white mb-3">Analyzing...</h2>
      <p className="text-slate-400 text-lg">Checking your phonemes, rhythm, and intonation.</p>
    </div>
  );

  return (
    <div>
      {appState === AppState.LANDING && renderLanding()}
      {appState === AppState.HISTORY && renderHistory()}
      {appState === AppState.PRACTICE && renderPractice()}
      {appState === AppState.ANALYZING && renderAnalyzing()}
      {appState === AppState.RESULTS && analysisResult && (
        <div className="min-h-screen pt-10 px-4">
          <AnalysisView
            result={analysisResult}
            userAudioUrl={audioUrl}
            originalText={practiceText}
            onRetry={() => { setAudioBlob(null); setAppState(AppState.PRACTICE); }}
            onNewChallenge={startChallenge}
            onBack={() => setAppState(AppState.HISTORY)}
          />
        </div>
      )}
    </div>
  );
};

export default App;