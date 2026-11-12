import React, { useState, useEffect } from 'react';
import { Target, Play, RotateCcw, CheckCircle2, AlertCircle } from 'lucide-react';
import soundService from '../services/soundEffects';
import itemPoolService from '../services/itemPoolService';

export default function SrtPage() {
  const [drillMode, setDrillMode] = useState(15); // 15 or 60
  const [situations, setSituations] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(30);
  const [isRunning, setIsRunning] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [responses, setResponses] = useState({});
  const [currentInput, setCurrentInput] = useState('');

  const loadSituations = (count) => {
    setDrillMode(count);
    const selected = itemPoolService.getItems('srt', count);
    setSituations(selected);
    setCurrentIndex(0);
    setTimeRemaining(30);
    setIsRunning(false);
    setIsCompleted(false);
    setResponses({});
    setCurrentInput('');
  };

  useEffect(() => {
    loadSituations(15);
  }, []);

  // 30s cadence
  useEffect(() => {
    let interval = null;
    if (isRunning && !isCompleted && situations.length > 0) {
      interval = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            handleNextSituation();
            return 30;
          }
          if (prev <= 5) {
            soundService.playHurryWarning();
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning, currentIndex, currentInput, situations, isCompleted]);

  const handleNextSituation = () => {
    const cur = situations[currentIndex];
    if (cur) {
      setResponses((prev) => ({
        ...prev,
        [cur.id]: currentInput.trim() || '(No reaction recorded)',
      }));
    }
    setCurrentInput('');
    soundService.playSlideAdvance();

    if (currentIndex + 1 < situations.length) {
      setCurrentIndex((i) => i + 1);
      setTimeRemaining(30);
    } else {
      setIsRunning(false);
      setIsCompleted(true);
      soundService.playCompletionAlarm();
    }
  };

  const currentSit = situations[currentIndex];

  return (
    <div className="max-w-4xl mx-auto my-8 px-4">
      <div className="glass-card p-6 sm:p-10 animate-slide-up space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-emerald-400">
                Situation Reaction Test (SRT)
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-[var(--text-primary)] mt-1">
              RULE 1 &amp; 2 DECISIVE REACTION DRILL
            </h1>
          </div>

          <div className="flex items-center gap-2">
            {!isRunning && !isCompleted && (
              <>
                <button
                  onClick={() => loadSituations(15)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    drillMode === 15 ? 'bg-emerald-600 text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] border border-[var(--border-color)]'
                  }`}
                >
                  15-Item Drill
                </button>
                <button
                  onClick={() => loadSituations(60)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    drillMode === 60 ? 'bg-emerald-600 text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] border border-[var(--border-color)]'
                  }`}
                >
                  60-Item Full Battery
                </button>
              </>
            )}

            <div className="text-right ml-4">
              <div className="text-[10px] font-bold uppercase text-[var(--text-muted)]">TIMER</div>
              <div className={`font-mono text-3xl font-black ${
                timeRemaining <= 5 ? 'text-amber-400 animate-pulse' : 'text-emerald-400'
              }`}>
                00:{String(timeRemaining).padStart(2, '0')}
              </div>
            </div>
          </div>
        </div>

        {/* Not Started */}
        {!isRunning && !isCompleted && (
          <div className="py-12 text-center space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/20">
              <Target className="w-8 h-8" />
            </div>
            <div className="max-w-md mx-auto">
              <h2 className="text-lg font-bold text-[var(--text-primary)]">Ready for SRT ({drillMode} Situations)?</h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                Strict Rule 1 serial numbering &amp; Rule 2 standardized reaction ending <code>(...)</code>. Deliver swift, practical, and heroic officer solutions.
              </p>
            </div>
            <button
              onClick={() => {
                soundService.playCountdown(0);
                setIsRunning(true);
              }}
              className="btn-primary px-8 py-3.5 text-base bg-emerald-600 hover:bg-emerald-500"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Start 30s Drill</span>
            </button>
          </div>
        )}

        {/* Active Test */}
        {isRunning && currentSit && (
          <div className="space-y-6">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-mono">
              <span>SITUATION {currentIndex + 1} OF {situations.length}</span>
              <span>{Math.round(((currentIndex + 1) / situations.length) * 100)}% COMPLETE</span>
            </div>

            {/* Situation Prompt Box */}
            <div className="p-8 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border-color)] shadow-xl animate-pop-in">
              <div className="text-xs uppercase font-extrabold text-[var(--text-muted)] tracking-wider mb-3">
                QUESTION #{currentSit.serial || (currentIndex + 1)}
              </div>
              <div className="text-lg sm:text-xl font-bold text-[var(--text-primary)] leading-relaxed">
                {currentSit.text}
              </div>
            </div>

            {/* Input Form */}
            <form onSubmit={(e) => { e.preventDefault(); handleNextSituation(); }}>
              <textarea
                rows={3}
                autoFocus
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                placeholder="What action did he take? Type practical reaction and press Submit..."
                className="w-full p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)] text-base text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-emerald-400 font-medium resize-none"
              />
              <div className="flex justify-end mt-2">
                <button type="submit" className="btn-primary text-xs py-2 px-6 bg-emerald-600 hover:bg-emerald-500">
                  <span>Submit Action &rarr;</span>
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Completed State */}
        {isCompleted && (
          <div className="space-y-6 animate-slide-up">
            <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-center">
              <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-2" />
              <h2 className="text-xl font-black text-[var(--text-primary)]">SRT DRILL COMPLETED!</h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                Completed {situations.length} situations under timed pressure.
              </p>
            </div>

            <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
              {situations.map((s, idx) => (
                <div key={s.id} className="p-3.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                  <div className="text-xs font-bold text-emerald-400 font-mono">#{idx + 1} {s.text}</div>
                  <div className="text-sm text-[var(--text-primary)] mt-1 pl-3 border-l-2 border-emerald-500">
                    &rarr; {responses[s.id] || '(No reaction recorded)'}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-center pt-4">
              <button onClick={() => loadSituations(drillMode)} className="btn-primary bg-emerald-600 hover:bg-emerald-500">
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

