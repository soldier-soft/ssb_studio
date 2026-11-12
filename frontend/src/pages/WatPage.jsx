import React, { useState, useEffect } from 'react';
import { Zap, Play, RotateCcw, CheckCircle2, ChevronRight, BarChart2 } from 'lucide-react';
import soundService from '../services/soundEffects';
import itemPoolService from '../services/itemPoolService';

export default function WatPage() {
  const [drillMode, setDrillMode] = useState(15); // 15 or 60
  const [words, setWords] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(15);
  const [isRunning, setIsRunning] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [responses, setResponses] = useState({});
  const [currentInput, setCurrentInput] = useState('');

  const loadWords = (count) => {
    setDrillMode(count);
    const selected = itemPoolService.getItems('wat', count);
    setWords(selected);
    setCurrentIndex(0);
    setTimeRemaining(15);
    setIsRunning(false);
    setIsCompleted(false);
    setResponses({});
    setCurrentInput('');
  };

  useEffect(() => {
    loadWords(15);
  }, []);

  // Main 15s monotonic cadence
  useEffect(() => {
    let interval = null;
    if (isRunning && !isCompleted && words.length > 0) {
      interval = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            handleNextWord();
            return 15;
          }
          if (prev <= 5) {
            soundService.playHurryWarning();
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning, currentIndex, currentInput, words, isCompleted]);

  const handleNextWord = () => {
    const cur = words[currentIndex];
    if (cur) {
      setResponses((prev) => ({
        ...prev,
        [cur.id]: currentInput.trim() || '(No response recorded)',
      }));
    }
    setCurrentInput('');
    soundService.playSlideAdvance();

    if (currentIndex + 1 < words.length) {
      setCurrentIndex((i) => i + 1);
      setTimeRemaining(15);
    } else {
      setIsRunning(false);
      setIsCompleted(true);
      soundService.playCompletionAlarm();
    }
  };

  const currentWord = words[currentIndex];

  return (
    <div className="max-w-4xl mx-auto my-8 px-4">
      <div className="glass-card p-6 sm:p-10 animate-slide-up space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" />
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-blue-400">
                Word Association Test (WAT)
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-[var(--text-primary)] mt-1">
              15-SECOND SPONTANEOUS CADENCE
            </h1>
          </div>

          <div className="flex items-center gap-2">
            {!isRunning && !isCompleted && (
              <>
                <button
                  onClick={() => loadWords(15)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    drillMode === 15 ? 'bg-blue-600 text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] border border-[var(--border-color)]'
                  }`}
                >
                  15-Word Sprint
                </button>
                <button
                  onClick={() => loadWords(60)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    drillMode === 60 ? 'bg-blue-600 text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] border border-[var(--border-color)]'
                  }`}
                >
                  60-Word Full Exam
                </button>
              </>
            )}

            <div className="text-right ml-4">
              <div className="text-[10px] font-bold uppercase text-[var(--text-muted)]">TIMER</div>
              <div className={`font-mono text-3xl font-black ${
                timeRemaining <= 5 ? 'text-red-400 animate-pulse' : 'text-blue-400'
              }`}>
                00:{String(timeRemaining).padStart(2, '0')}
              </div>
            </div>
          </div>
        </div>

        {/* Not Started State */}
        {!isRunning && !isCompleted && (
          <div className="py-12 text-center space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-blue-500/20 text-blue-400 flex items-center justify-center mx-auto shadow-lg shadow-blue-500/20">
              <Zap className="w-8 h-8" />
            </div>
            <div className="max-w-md mx-auto">
              <h2 className="text-lg font-bold text-[var(--text-primary)]">Ready for WAT Drill ({drillMode} Words)?</h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                Each word flashes for exactly 15 seconds. Write your immediate, spontaneous sentence exhibiting positive Officer-Like Qualities.
              </p>
            </div>
            <button
              onClick={() => {
                soundService.playCountdown(0);
                setIsRunning(true);
              }}
              className="btn-primary px-8 py-3.5 text-base"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Start 15s Cadence</span>
            </button>
          </div>
        )}

        {/* Active Test State */}
        {isRunning && currentWord && (
          <div className="space-y-6">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-mono">
              <span>PROGRESS: WORD {currentIndex + 1} OF {words.length}</span>
              <span>{Math.round(((currentIndex + 1) / words.length) * 100)}% COMPLETE</span>
            </div>

            {/* Word Flash Card */}
            <div className="py-16 px-6 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border-color)] text-center animate-pop-in shadow-xl">
              <div className="text-xs uppercase font-extrabold text-[var(--text-muted)] tracking-widest mb-3">
                ASSOCIATE SPONTANEOUSLY
              </div>
              <div className="text-5xl sm:text-7xl font-black text-sky-400 tracking-wider font-mono">
                {currentWord.word}
              </div>
              <div className="text-xs text-[var(--text-muted)] mt-4">
                ID: {currentWord.id} &bull; {currentWord.category}
              </div>
            </div>

            {/* Input Form */}
            <form onSubmit={(e) => { e.preventDefault(); handleNextWord(); }}>
              <input
                type="text"
                autoFocus
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                placeholder="Type your reaction sentence and press Enter (or auto-advances at 15s)..."
                className="w-full px-5 py-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)] text-base text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-sky-400 font-medium"
              />
            </form>
          </div>
        )}

        {/* Completed State */}
        {isCompleted && (
          <div className="space-y-6 animate-slide-up">
            <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-center">
              <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-2" />
              <h2 className="text-xl font-black text-[var(--text-primary)]">WAT DRILL COMPLETED!</h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                Completed {words.length} words. All responses recorded.
              </p>
            </div>

            <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
              {words.map((w, idx) => (
                <div key={w.id} className="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] flex items-start justify-between gap-4">
                  <div>
                    <span className="text-xs font-black text-sky-400 font-mono">#{idx + 1} {w.word}:</span>
                    <p className="text-sm text-[var(--text-primary)] mt-0.5">{responses[w.id] || '(No response)'}</p>
                  </div>
                  <span className="text-[10px] text-[var(--text-muted)] font-mono">{w.id}</span>
                </div>
              ))}
            </div>

            <div className="flex justify-center pt-4">
              <button onClick={() => loadWords(drillMode)} className="btn-primary">
                <RotateCcw className="w-4 h-4" />
                <span>Practice Another Set</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

