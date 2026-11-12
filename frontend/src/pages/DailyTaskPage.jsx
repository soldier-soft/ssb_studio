import React, { useState, useEffect } from 'react';
import { 
  Flame, 
  CheckCircle2, 
  ArrowRight, 
  Play, 
  RotateCcw, 
  Copy, 
  ShieldCheck, 
  Clock, 
  Zap, 
  Target, 
  Image as ImageIcon,
  Award
} from 'lucide-react';
import confetti from 'canvas-confetti';
import soundService from '../services/soundEffects';
import itemPoolService from '../services/itemPoolService';

export default function DailyTaskPage({ setActivePage }) {
  const [taskData, setTaskData] = useState(null);
  const [phase, setPhase] = useState('briefing'); // briefing, tat, wat, srt, completed
  const [streak, setStreak] = useState(0);

  // TAT Phase State
  const [tatIdx, setTatIdx] = useState(0);
  const [tatSubPhase, setTatSubPhase] = useState('view'); // view (30s) or write (240s)
  const [tatTimer, setTatTimer] = useState(30);
  const [tatStories, setTatStories] = useState({});

  // WAT Phase State
  const [watIdx, setWatIdx] = useState(0);
  const [watTimer, setWatTimer] = useState(15);
  const [watResponses, setWatResponses] = useState({});
  const [currentWatInput, setCurrentWatInput] = useState('');

  // SRT Phase State
  const [srtIdx, setSrtIdx] = useState(0);
  const [srtTimer, setSrtTimer] = useState(30);
  const [srtResponses, setSrtResponses] = useState({});
  const [currentSrtInput, setCurrentSrtInput] = useState('');

  // Load Daily Task items
  useEffect(() => {
    loadDailyMission();
  }, []);

  const loadDailyMission = () => {
    const data = itemPoolService.getDailyTask();
    setTaskData(data);
    setStreak(itemPoolService.getStreak());
  };

  // -------------------------------------------------------------
  // TAT Timer Hook
  // -------------------------------------------------------------
  useEffect(() => {
    let interval = null;
    if (phase === 'tat') {
      interval = setInterval(() => {
        setTatTimer((prev) => {
          if (prev <= 1) {
            if (tatSubPhase === 'view') {
              // Transition to write phase (4 mins = 240s)
              soundService.playSlideAdvance();
              setTatSubPhase('write');
              return 240;
            } else {
              // Write phase finished
              soundService.playSlideAdvance();
              if (tatIdx + 1 < (taskData?.tat?.length || 2)) {
                setTatIdx((i) => i + 1);
                setTatSubPhase('view');
                return 30;
              } else {
                // Move to WAT phase
                setPhase('wat');
                setWatIdx(0);
                setWatTimer(15);
                soundService.playCountdown(0);
                return 0;
              }
            }
          }
          if (prev === 6 && tatSubPhase === 'view') {
            soundService.playHurryWarning();
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [phase, tatSubPhase, tatIdx, taskData]);

  // -------------------------------------------------------------
  // WAT Timer Hook
  // -------------------------------------------------------------
  useEffect(() => {
    let interval = null;
    if (phase === 'wat') {
      interval = setInterval(() => {
        setWatTimer((prev) => {
          if (prev <= 1) {
            handleWatNext();
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
  }, [phase, watIdx, currentWatInput, taskData]);

  const handleWatNext = () => {
    const currentWord = taskData?.wat[watIdx];
    if (currentWord) {
      setWatResponses((prev) => ({
        ...prev,
        [currentWord.id]: currentWatInput.trim() || '(No reaction recorded)',
      }));
    }
    setCurrentWatInput('');
    soundService.playSlideAdvance();

    if (watIdx + 1 < (taskData?.wat?.length || 15)) {
      setWatIdx((i) => i + 1);
      setWatTimer(15);
    } else {
      // Advance to SRT Phase
      setPhase('srt');
      setSrtIdx(0);
      setSrtTimer(30);
      soundService.playCountdown(0);
    }
  };

  // -------------------------------------------------------------
  // SRT Timer Hook
  // -------------------------------------------------------------
  useEffect(() => {
    let interval = null;
    if (phase === 'srt') {
      interval = setInterval(() => {
        setSrtTimer((prev) => {
          if (prev <= 1) {
            handleSrtNext();
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
  }, [phase, srtIdx, currentSrtInput, taskData]);

  const handleSrtNext = () => {
    const currentSit = taskData?.srt[srtIdx];
    if (currentSit) {
      setSrtResponses((prev) => ({
        ...prev,
        [currentSit.id]: currentSrtInput.trim() || '(No action recorded)',
      }));
    }
    setCurrentSrtInput('');
    soundService.playSlideAdvance();

    if (srtIdx + 1 < (taskData?.srt?.length || 15)) {
      setSrtIdx((i) => i + 1);
      setSrtTimer(30);
    } else {
      // Completed full daily routine!
      finishDailyMission();
    }
  };

  const finishDailyMission = () => {
    setPhase('completed');
    const newStreak = itemPoolService.recordDailyCompletion();
    setStreak(newStreak);
    soundService.playCompletionAlarm();
    try {
      confetti({
        particleCount: 120,
        spread: 80,
        origin: { y: 0.5 },
      });
    } catch (e) {}
  };

  const startMission = () => {
    soundService.playCountdown(0);
    setPhase('tat');
    setTatIdx(0);
    setTatSubPhase('view');
    setTatTimer(30);
  };

  if (!taskData) {
    return <div className="p-8 text-center text-slate-400">Loading daily mission...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto my-8 px-4">
      {/* Briefing Phase */}
      {phase === 'briefing' && (
        <div className="glass-card p-6 sm:p-10 animate-slide-up space-y-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-6">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-widest bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Officer Daily Workout
                </span>
                <span className="text-xs text-[var(--text-muted)] font-mono">{taskData.date}</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-black text-[var(--text-primary)]">
                TODAY'S PSYCHOLOGICAL ROUTINE
              </h1>
              <p className="text-sm text-[var(--text-secondary)] mt-1">
                Fresh non-repeating set guaranteed different from your last 2 days' practice.
              </p>
            </div>

            <div className="flex items-center gap-3 bg-[var(--bg-secondary)] px-4 py-2.5 rounded-xl border border-[var(--border-color)]">
              <Flame className="w-6 h-6 text-amber-500 animate-pulse" />
              <div>
                <div className="text-[10px] uppercase font-bold text-[var(--text-muted)]">Active Streak</div>
                <div className="text-base font-extrabold text-[var(--text-primary)]">{streak} Days Ready</div>
              </div>
            </div>
          </div>

          {/* Curriculum breakdown cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div className="w-8 h-8 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center font-bold mb-3">
                <ImageIcon className="w-4 h-4" />
              </div>
              <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Phase 1 &bull; TAT</div>
              <div className="text-lg font-black text-[var(--text-primary)] mt-0.5">2 Pictures</div>
              <p className="text-xs text-[var(--text-secondary)] mt-2">
                30s viewing phase &rarr; 4m writing phase for structured character &amp; action storytelling.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold mb-3">
                <Zap className="w-4 h-4" />
              </div>
              <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Phase 2 &bull; WAT</div>
              <div className="text-lg font-black text-[var(--text-primary)] mt-0.5">15 Words</div>
              <p className="text-xs text-[var(--text-secondary)] mt-2">
                15 seconds per word. Spontaneous association with automatic monotonic slide progression.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold mb-3">
                <Target className="w-4 h-4" />
              </div>
              <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Phase 3 &bull; SRT</div>
              <div className="text-lg font-black text-[var(--text-primary)] mt-0.5">15 Situations</div>
              <p className="text-xs text-[var(--text-secondary)] mt-2">
                30 seconds per situation. Sequential crisis management ending in natural reaction stems.
              </p>
            </div>
          </div>

          {/* Start Mission Button */}
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-[var(--border-color)]">
            <div className="text-xs text-[var(--text-muted)]">
              Total estimated duration: <strong>~22 Minutes</strong> &bull; Audio cues enabled
            </div>
            <button
              onClick={startMission}
              className="btn-primary w-full sm:w-auto px-8 py-3.5 text-base"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Commence Daily Routine</span>
            </button>
          </div>
        </div>
      )}

      {/* TAT Phase */}
      {phase === 'tat' && (
        <div className="glass-card p-6 sm:p-10 animate-slide-up space-y-6">
          <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-4">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                DAILY TASK &bull; PHASE 1: TAT
              </span>
              <h2 className="text-xl font-bold text-[var(--text-primary)] mt-1">
                Picture {tatIdx + 1} of {taskData.tat.length}: {taskData.tat[tatIdx]?.title}
              </h2>
            </div>

            <div className="text-right">
              <div className="text-[10px] uppercase font-bold text-[var(--text-muted)]">
                {tatSubPhase === 'view' ? 'VIEWING PHASE' : 'WRITING PHASE'}
              </div>
              <div className={`font-mono text-2xl sm:text-3xl font-black ${
                tatTimer <= 5 ? 'text-amber-400 animate-pulse' : 'text-sky-400'
              }`}>
                00:{String(tatTimer).padStart(2, '0')}
              </div>
            </div>
          </div>

          {/* Picture Viewer / Artwork Placeholder */}
          <div className="relative aspect-video rounded-xl bg-gradient-to-tr from-slate-900 to-slate-800 border border-[var(--border-color)] overflow-hidden flex flex-col items-center justify-center p-6 text-center">
            <div className="w-16 h-16 rounded-full bg-sky-500/10 border border-sky-500/30 flex items-center justify-center mb-3">
              <ImageIcon className="w-8 h-8 text-sky-400" />
            </div>
            <h3 className="text-lg font-extrabold text-[var(--text-primary)]">
              {taskData.tat[tatIdx]?.title}
            </h3>
            <p className="text-xs sm:text-sm text-[var(--text-secondary)] max-w-lg mt-2">
              {taskData.tat[tatIdx]?.desc}
            </p>
          </div>

          {/* Story input area */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-[var(--text-secondary)]">
                Your Story Response (Past &bull; Present &bull; Feelings &bull; Positive Resolution)
              </label>
              <span className="text-xs text-[var(--text-muted)] font-mono">
                {tatStories[taskData.tat[tatIdx]?.id]?.split(/\s+/).filter(Boolean).length || 0} words
              </span>
            </div>
            <textarea
              rows={6}
              disabled={tatSubPhase === 'view'}
              placeholder={tatSubPhase === 'view' ? "Observe scene carefully during 30s viewing phase..." : "Write your structured story here..."}
              value={tatStories[taskData.tat[tatIdx]?.id] || ''}
              onChange={(e) => setTatStories({ ...tatStories, [taskData.tat[tatIdx]?.id]: e.target.value })}
              className="w-full p-3.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)] text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-sky-400 resize-none font-sans"
            />
          </div>
        </div>
      )}

      {/* WAT Phase */}
      {phase === 'wat' && (
        <div className="glass-card p-6 sm:p-10 animate-slide-up space-y-6">
          <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-4">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                DAILY TASK &bull; PHASE 2: WAT
              </span>
              <h2 className="text-sm font-semibold text-[var(--text-secondary)] mt-1">
                Word {watIdx + 1} of {taskData.wat.length}
              </h2>
            </div>

            <div className="text-right">
              <div className="text-[10px] uppercase font-bold text-[var(--text-muted)]">TIMER</div>
              <div className={`font-mono text-3xl font-black ${
                watTimer <= 5 ? 'text-red-400 animate-pulse' : 'text-blue-400'
              }`}>
                00:{String(watTimer).padStart(2, '0')}
              </div>
            </div>
          </div>

          {/* Flash Word Card */}
          <div className="py-12 px-6 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border-color)] text-center animate-pop-in">
            <div className="text-xs uppercase font-extrabold text-[var(--text-muted)] tracking-widest mb-2">
              ASSOCIATE SPONTANEOUSLY
            </div>
            <div className="text-4xl sm:text-6xl font-black text-sky-400 tracking-wider">
              {taskData.wat[watIdx]?.word}
            </div>
            <div className="text-xs text-[var(--text-muted)] mt-2">
              {taskData.wat[watIdx]?.category}
            </div>
          </div>

          {/* Input field */}
          <div>
            <form onSubmit={(e) => { e.preventDefault(); handleWatNext(); }}>
              <input
                type="text"
                autoFocus
                value={currentWatInput}
                onChange={(e) => setCurrentWatInput(e.target.value)}
                placeholder="Type your spontaneous reaction and press Enter (or wait for 15s auto-advance)..."
                className="w-full px-4 py-3.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)] text-sm sm:text-base text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-sky-400 font-medium"
              />
            </form>
          </div>
        </div>
      )}

      {/* SRT Phase */}
      {phase === 'srt' && (
        <div className="glass-card p-6 sm:p-10 animate-slide-up space-y-6">
          <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-4">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                DAILY TASK &bull; PHASE 3: SRT
              </span>
              <h2 className="text-sm font-semibold text-[var(--text-secondary)] mt-1">
                Situation {srtIdx + 1} of {taskData.srt.length}
              </h2>
            </div>

            <div className="text-right">
              <div className="text-[10px] uppercase font-bold text-[var(--text-muted)]">TIMER</div>
              <div className={`font-mono text-3xl font-black ${
                srtTimer <= 5 ? 'text-amber-400 animate-pulse' : 'text-emerald-400'
              }`}>
                00:{String(srtTimer).padStart(2, '0')}
              </div>
            </div>
          </div>

          {/* Situation Prompt */}
          <div className="p-6 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border-color)] leading-relaxed">
            <div className="text-xs uppercase font-extrabold text-[var(--text-muted)] tracking-wider mb-2">
              CRISIS SITUATION #{taskData.srt[srtIdx]?.serial}
            </div>
            <div className="text-base sm:text-lg font-bold text-[var(--text-primary)]">
              {taskData.srt[srtIdx]?.text}
            </div>
          </div>

          {/* Response Box */}
          <div>
            <form onSubmit={(e) => { e.preventDefault(); handleSrtNext(); }}>
              <textarea
                rows={3}
                autoFocus
                value={currentSrtInput}
                onChange={(e) => setCurrentSrtInput(e.target.value)}
                placeholder="What action did he take? Type practical, decisive response..."
                className="w-full p-3.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)] text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-emerald-400 resize-none font-medium"
              />
              <div className="flex justify-end mt-2">
                <button type="submit" className="btn-primary text-xs py-2 px-5">
                  <span>Submit Reaction &rarr;</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Completed Debrief */}
      {phase === 'completed' && (
        <div className="glass-card p-6 sm:p-10 animate-slide-up space-y-8 text-center">
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/20">
            <Award className="w-8 h-8" />
          </div>

          <div>
            <h1 className="text-3xl font-black text-[var(--text-primary)]">DAILY MISSION COMPLETED!</h1>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Outstanding work officer. Your daily streak is now <strong>{streak} days</strong>.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-lg mx-auto">
            <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div className="text-2xl font-black text-sky-400">2 / 2</div>
              <div className="text-xs text-[var(--text-muted)] uppercase font-bold mt-1">TAT Stories</div>
            </div>
            <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div className="text-2xl font-black text-blue-400">15 / 15</div>
              <div className="text-xs text-[var(--text-muted)] uppercase font-bold mt-1">WAT Reactions</div>
            </div>
            <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div className="text-2xl font-black text-emerald-400">15 / 15</div>
              <div className="text-xs text-[var(--text-muted)] uppercase font-bold mt-1">SRT Solutions</div>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-4 border-t border-[var(--border-color)]">
            <button
              onClick={() => {
                soundService.playClick();
                setActivePage('dashboard');
              }}
              className="btn-primary px-6"
            >
              Return to Dashboard
            </button>
            <button
              onClick={() => {
                soundService.playClick();
                setActivePage('focus');
              }}
              className="btn-secondary px-6"
            >
              Go to Focus Timer
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

