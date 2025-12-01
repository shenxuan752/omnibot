import React, { useState, useEffect } from 'react';
import { AnalysisResult, WordAnalysis } from '../types';
import { generateTTS } from '../services/geminiService';
import AudioPlayer from './AudioPlayer';
import { ChevronRight, AlertCircle, Copy, Mic, Volume2, Database, Loader2 } from 'lucide-react';

interface AnalysisViewProps {
  result: AnalysisResult;
  userAudioUrl: string | null;
  originalText: string;
  onRetry: () => void;
  onNewChallenge: () => void;
  onBack?: () => void;
}

const AnalysisView: React.FC<AnalysisViewProps> = ({ result, userAudioUrl, originalText, onRetry, onNewChallenge, onBack }) => {
  const [selectedWord, setSelectedWord] = useState<WordAnalysis | null>(null);
  const [hoveredWord, setHoveredWord] = useState<WordAnalysis | null>(null);
  const [playingWord, setPlayingWord] = useState<string | null>(null);
  
  const [nativeAudioUrl, setNativeAudioUrl] = useState<string | null>(null);
  const [coachAudioUrl, setCoachAudioUrl] = useState<string | null>(null);
  const [isLoadingNative, setIsLoadingNative] = useState(false);
  const [isLoadingCoach, setIsLoadingCoach] = useState(false);

  useEffect(() => {
    const firstError = result.wordBreakdown.find(w => !w.isCorrect);
    if (firstError) setSelectedWord(firstError);

    const prefetchProblemWords = async () => {
       const errors = result.wordBreakdown.filter(w => !w.isCorrect).slice(0, 5); 
       for (const error of errors) {
         await generateTTS(error.word, 'Kore');
       }
    };
    prefetchProblemWords();

  }, [result]);

  const handleFetchNative = async () => {
    if (nativeAudioUrl || isLoadingNative) return;
    setIsLoadingNative(true);
    const audio = await generateTTS(originalText, 'Kore');
    setNativeAudioUrl(audio);
    setIsLoadingNative(false);
  };

  const handleFetchCoach = async () => {
    if (coachAudioUrl || isLoadingCoach) return;
    setIsLoadingCoach(true);
    const script = `Here is what I noticed. ${result.coachNotes}`;
    const audio = await generateTTS(script, 'Puck');
    setCoachAudioUrl(audio);
    setIsLoadingCoach(false);
  };

  const playWord = async (word: string) => {
    if (playingWord) return;
    setPlayingWord(word);
    try {
      const audioUrl = await generateTTS(word, 'Kore');
      if (audioUrl) {
        const audio = new Audio(audioUrl);
        audio.onended = () => setPlayingWord(null);
        await audio.play();
      } else {
        setPlayingWord(null);
      }
    } catch (e) {
      console.error("Failed to play word", e);
      setPlayingWord(null);
    }
  };

  useEffect(() => {
    handleFetchNative();
  }, [originalText]);

  const copyProblemWords = () => {
    navigator.clipboard.writeText(result.problemWords.join(', '));
    alert('Words copied to clipboard!');
  };

  return (
    <div className="max-w-3xl mx-auto pb-20 animate-fade-in relative">
      
      {/* Navigation Bar */}
      <div className="flex items-center justify-between mb-6">
         {onBack ? (
            <button 
              onClick={onBack} 
              className="flex items-center gap-2 text-slate-400 hover:text-white font-medium px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 shadow-sm hover:border-slate-700 transition-all"
            >
              <Database size={18} /> 
              History Database
            </button>
         ) : (
           <div />
         )}
         
         <div className="text-sm font-medium text-slate-500 uppercase tracking-wider">Analysis Results</div>
      </div>

      {/* Header with Score */}
      <div className="bg-slate-900 rounded-2xl p-8 shadow-xl shadow-black/20 border border-slate-800 mb-6 text-center">
        <h2 className="text-slate-500 uppercase tracking-widest text-xs font-bold mb-4">Overall Score</h2>
        <div className="relative inline-flex items-center justify-center">
           <span className={`text-8xl font-bold tracking-tighter ${
             result.overallScore > 80 ? 'text-green-400' : result.overallScore > 50 ? 'text-amber-400' : 'text-red-400'
           }`}>
             {result.overallScore}
             <span className="text-4xl align-top opacity-50">%</span>
           </span>
        </div>
        
        {/* Action Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
           <div className="flex flex-col gap-2">
             <button 
               onClick={handleFetchCoach}
               disabled={isLoadingCoach}
               className="bg-blue-600 hover:bg-blue-500 text-white py-3 px-4 rounded-xl font-medium flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-900/20 disabled:opacity-70 disabled:cursor-not-allowed"
             >
               {isLoadingCoach ? <Loader2 className="animate-spin" size={18} /> : <Mic size={18} />}
               {isLoadingCoach ? 'Generating...' : 'Hear Coach'}
             </button>
             {coachAudioUrl && <AudioPlayer src={coachAudioUrl} label="Coach Feedback" />}
           </div>

           <div className="flex flex-col gap-2">
             <div className="h-[48px] flex items-center justify-center bg-slate-800/50 rounded-xl text-slate-400 font-medium border border-slate-700 text-sm">
                {userAudioUrl ? 'Your Recording' : 'Recording Not Saved'}
             </div>
             {userAudioUrl && <AudioPlayer src={userAudioUrl} label="Original" />}
           </div>

           <div className="flex flex-col gap-2">
             <div className="h-[48px] flex items-center justify-center bg-emerald-900/20 text-emerald-400 font-medium rounded-xl border border-emerald-900/30 text-sm">
                Shadowing Mode
             </div>
             <AudioPlayer 
                src={nativeAudioUrl} 
                label="Native Speaker" 
                enableSpeedControl={true} 
             />
           </div>
        </div>
      </div>

      {/* Interactive Text */}
      <div className="bg-slate-900 rounded-2xl p-8 shadow-sm border border-slate-800 mb-6 relative">
        <div className="flex items-center justify-between mb-4">
           <h3 className="text-slate-500 text-xs font-bold uppercase tracking-widest">Interactive Analysis</h3>
           <div className="bg-red-500/10 text-red-400 text-xs px-2 py-1 rounded border border-red-500/20 flex items-center gap-1 font-medium">
             <Volume2 size={12} /> Click red words to listen
           </div>
        </div>
        
        <p className="text-2xl leading-relaxed font-serif text-slate-200 relative z-0">
          {result.wordBreakdown.map((word, idx) => {
            const isError = !word.isCorrect;
            const isHovered = hoveredWord === word;
            const isPlaying = playingWord === word.word;
            
            return (
              <span
                key={idx}
                onMouseEnter={() => isError && setHoveredWord(word)}
                onMouseLeave={() => setHoveredWord(null)}
                onClick={() => {
                   if(isError) {
                     setSelectedWord(word);
                     playWord(word.word);
                   }
                }}
                className={`relative inline-block mr-1.5 px-1 rounded transition-colors border-b-2 ${
                  isError
                    ? 'border-red-500/50 cursor-pointer hover:bg-red-500/10 text-red-300' 
                    : 'border-transparent'
                } ${
                  selectedWord === word ? 'bg-red-500/20 border-red-400' : ''
                } ${
                  isPlaying ? 'bg-blue-500/20 !border-blue-400 text-blue-300' : ''
                }`}
              >
                {word.word}
                
                {/* Tooltip on Hover */}
                {isHovered && isError && (
                   <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-black border border-slate-700 text-white text-xs p-3 rounded-lg shadow-2xl z-50 pointer-events-none text-center leading-normal">
                      <span className="block font-medium mb-1 border-b border-slate-800 pb-1 text-slate-300">
                        Pronounced "{word.phoneticReceived}"
                      </span>
                      <span className="block text-slate-400">
                        instead of "{word.phoneticExpected}"
                      </span>
                      <span className="block mt-2 text-blue-400 font-bold flex items-center justify-center gap-1">
                         {playingWord === word.word ? <Loader2 size={10} className="animate-spin" /> : <Volume2 size={10} />} 
                         {playingWord === word.word ? 'Loading...' : 'Click to listen'}
                      </span>
                      {/* Triangle arrow */}
                      <span className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-black"></span>
                   </span>
                )}
              </span>
            );
          })}
        </p>

        {/* Dynamic Card for Selected Word Details */}
        {selectedWord && !selectedWord.isCorrect && (
          <div className="mt-6 bg-slate-800/50 border border-slate-700 rounded-xl p-4 flex items-start gap-3 animate-fade-in-up">
            <AlertCircle className="text-blue-400 shrink-0 mt-0.5" size={20} />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className="text-blue-200 font-medium">
                  Problem word: <span className="font-bold text-white">"{selectedWord.word}"</span>
                </p>
                <button 
                  onClick={() => playWord(selectedWord.word)}
                  className="text-xs bg-slate-800 border border-slate-600 text-blue-300 px-2 py-1 rounded flex items-center gap-1 hover:bg-slate-700 hover:text-white transition-colors"
                >
                  {playingWord === selectedWord.word ? <Loader2 size={12} className="animate-spin" /> : <Volume2 size={12} />}
                  Listen
                </button>
              </div>
              <p className="text-slate-400 mt-1 text-sm">
                {selectedWord.explanation}
              </p>
              <div className="flex items-center gap-4 mt-3 text-sm">
                <div className="text-red-300 bg-red-900/20 px-2 py-1 rounded border border-red-900/30">
                  You said: <span className="font-mono font-bold text-red-200">{selectedWord.phoneticReceived || "???"}</span>
                </div>
                <ChevronRight size={14} className="text-slate-600" />
                <div className="text-green-300 bg-green-900/20 px-2 py-1 rounded border border-green-900/30">
                  Target: <span className="font-mono font-bold text-green-200">{selectedWord.phoneticExpected || "..."}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-800">
          <h3 className="font-bold text-slate-200 mb-4 flex items-center gap-2">
             Detailed Breakdown
          </h3>
          <div className="space-y-5">
            <div>
              <div className="flex justify-between text-sm mb-2 font-medium">
                <span className="text-slate-400">Phoneme Accuracy</span>
                <span className="text-blue-300">{result.phonemeAccuracy}%</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-500 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)]" 
                  style={{ width: `${result.phonemeAccuracy}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2 font-medium">
                <span className="text-slate-400">Flow, Linking & Rhythm</span>
                <span className="text-purple-300">{result.flowRhythmScore}%</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-purple-500 rounded-full shadow-[0_0_10px_rgba(168,85,247,0.5)]" 
                  style={{ width: `${result.flowRhythmScore}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-800 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
             <Mic size={100} className="text-blue-500" />
          </div>
          <h3 className="font-bold text-blue-300 mb-3 flex items-center gap-2">
             ✨ Coach's Notes
          </h3>
          <p className="text-slate-300 text-sm leading-relaxed relative z-10">
            "{result.coachNotes}"
          </p>
        </div>
      </div>

      {/* Specific Fixes & Problem Words */}
      <div className="bg-slate-900 rounded-2xl p-8 shadow-sm border border-slate-800">
        <div className="flex items-center justify-between mb-4">
           <h3 className="font-bold text-slate-200">Problem Words</h3>
           <button 
             onClick={copyProblemWords}
             className="text-xs flex items-center gap-1 text-slate-500 hover:text-white font-medium transition-colors"
           >
             <Copy size={12} /> Copy List
           </button>
        </div>
        <div className="flex flex-wrap gap-2 mb-8">
           {result.problemWords.map((word, i) => (
             <span key={i} className="px-3 py-1 bg-red-900/20 text-red-300 rounded-lg text-sm border border-red-900/30">
               {word}
             </span>
           ))}
           {result.problemWords.length === 0 && <span className="text-slate-500 italic">No specific problem words found. Great job!</span>}
        </div>

        <h3 className="font-bold text-slate-200 mb-4">Specific Fixes</h3>
        <ul className="space-y-3">
          {result.specificFixes.map((fix, i) => (
            <li key={i} className="flex gap-3 text-slate-300 leading-relaxed group">
              <span className="text-blue-500 font-bold group-hover:text-blue-400">•</span>
              {fix}
            </li>
          ))}
        </ul>
      </div>

      {/* Footer Actions */}
      <div className="flex gap-4 mt-8 justify-center">
         <button onClick={onRetry} className="px-6 py-3 bg-slate-800 border border-slate-700 text-slate-300 font-medium rounded-xl hover:bg-slate-700 hover:text-white transition-all">
            Retry Same Text
         </button>
         <button onClick={onNewChallenge} className="px-6 py-3 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-500 transition-all shadow-lg shadow-blue-900/30">
            New Challenge
         </button>
      </div>
    </div>
  );
};

export default AnalysisView;