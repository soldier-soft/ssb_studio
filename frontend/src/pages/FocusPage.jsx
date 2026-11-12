import React, { useState, useEffect, useRef } from 'react';
import { 
  Maximize2, 
  Minimize2, 
  Play, 
  Pause, 
  RotateCcw, 
  Bell, 
  Volume2, 
  CheckCircle2, 
  Sparkles, 
  ShieldCheck, 
  Flame,
  FileText
} from 'lucide-react';
import confetti from 'canvas-confetti';
import soundService from '../services/soundEffects';

const PRESETS = [
  { label: '15m Quick Drill', minutes: 15 },
  { label: '25m Pomodoro', minutes: 25 },
  { label: '45m Psych Exam', minutes: 45 },
  { label: '60m Full Mock', minutes: 60 },
  { label: '90m Deep Study', minutes: 90 },
];

const QUOTES = [
  "\"The more you sweat in peace, the less you bleed in war.\" — General Norman Schwarzkopf",
  "\"An officer is known by his conduct under pressure, clarity of thought, and decisive courage.\"",
  "\"Courage is resistance to fear, mastery of fear — not absence of fear.\" — Mark Twain",
  "\"Discipline is the bridge between goals and accomplishment.\"",
  "\"Victory belongs to the most persevering.\" — Napoleon Bonaparte"
];

export default function FocusPage() {
  const [selectedMinutes, setSelectedMinutes] = useState(25);
  const [customMinutes, setCustomMinutes] = useState('');
  const [timeRemaining, setTimeRemaining] = useState(25 * 60);
  const [initialDuration, setInitialDuration] = useState(25 * 60);
  const [isRunning, setIsRunning] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [fiveMinAlarmTriggered, setFiveMinAlarmTriggered] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [quoteIndex, setQuoteIndex] = useState(0);
  const [notes, setNotes] = useState(localStorage.getItem('ssb_focus_scratchpad') || '');
  const [soundAlertsEnabled, setSoundAlertsEnabled] = useState(true);

  const containerRef = useRef(null);

  // Load quote
  useEffect(() => {
    setQuoteIndex(Math.floor(Math.random() * QUOTES.length));
  }, []);

  // Sync scratchpad
  useEffect(() => {
    localStorage.setItem('ssb_focus_scratchpad', notes);
  }, [notes]);

  // Main countdown loop with absolute deadline guard
  useEffect(() => {
    let interval = null;
    if (isRunning && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining((prev) => {
          const next = prev - 1;

          // 5-Minute Alarm Trigger Check (300 seconds)
          if (next === 300 && initialDuration > 300 && !fiveMinAlarmTriggered) {
            setFiveMinAlarmTriggered(true);
            if (soundAlertsEnabled) {
              soundService.playFocusFiveMinAlarm();
            }
          }

          // Complete check
          if (next <= 0) {
            setIsRunning(false);
            setIsCompleted(true);
            if (soundAlertsEnabled) {
              soundService.playCompletionAlarm();
            }
            try {
              confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 }
              });
            } catch (e) {}

            // Save completed session
            try {
              const prevHours = parseFloat(localStorage.getItem('ssb_focus_hours') || '0');
              const addedHours = initialDuration / 3600;
              localStorage.setItem('ssb_focus_hours', (prevHours + addedHours).toFixed(1));
            } catch (e) {}

            return 0;
          }

          return next;
        });
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning, timeRemaining, initialDuration, fiveMinAlarmTriggered, soundAlertsEnabled]);

  // Handle Fullscreen API
  const toggleFullscreen = () => {
    soundService.playClick();
    if (!document.fullscreenElement) {
      if (containerRef.current?.requestFullscreen) {
        containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
      } else if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
      }
    }
  };

  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFsChange);
    return () => document.removeEventListener('fullscreenchange', handleFsChange);
  }, []);

  const handleSelectPreset = (mins) => {
    soundService.playClick();
    setSelectedMinutes(mins);
    const secs = mins * 60;
    setInitialDuration(secs);
    setTimeRemaining(secs);
    setIsRunning(false);
    setIsCompleted(false);
    setFiveMinAlarmTriggered(false);
  };

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    const val = parseInt(customMinutes, 10);
    if (!isNaN(val) && val > 0 && val <= 360) {
      handleSelectPreset(val);
      setCustomMinutes('');
    }
  };

  const handlePlayPause = () => {
    soundService.playClick();
    if (isCompleted) {
      setTimeRemaining(initialDuration);
      setIsCompleted(false);
      setFiveMinAlarmTriggered(false);
      setIsRunning(true);
    } else {
      setIsRunning(!isRunning);
    }
  };

  const handleReset = () => {
    soundService.playClick();
    setIsRunning(false);
    setTimeRemaining(initialDuration);
    setIsCompleted(false);
    setFiveMinAlarmTriggered(false);
  };

  // Time formatters
  const formatTime = (totalSeconds) => {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    const pad = (n) => String(n).padStart(2, '0');

    if (hours > 0) {
      return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
    }
    return `${pad(minutes)}:${pad(seconds)}`;
  };

  // Progress percentage
  const progressPercent = initialDuration > 0 ? ((initialDuration - timeRemaining) / initialDuration) * 100 : 0;
  const isLast5Minutes = timeRemaining <= 300 && timeRemaining > 0 && initialDuration > 300;

  return (
    <div 
      ref={containerRef}
      className={`focus-fullscreen-container transition-all ${isFullscreen ? 'p-6 sm:p-12' : 'max-w-6xl mx-auto my-8 px-4'}`}
    >
      {/* Background radial glow */}
      <div className={`absolute inset-0 pointer-events-none transition-opacity duration-1000 ${
        isLast5Minutes ? 'bg-amber-500/10 opacity-100' : isCompleted ? 'bg-emerald-500/10 opacity-100' : 'opacity-0'
      }`} />

      {/* Header bar in Focus Screen */}
      <div className="w-full flex items-center justify-between z-10 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400 font-bold">
            ⚡
          </div>
          <div>
            <h1 className="text-lg font-extrabold text-[var(--text-primary)] tracking-wide">OFFICER FOCUS DRILL</h1>
            <p className="text-xs text-[var(--text-muted)]">5-Min Warning Bell &bull; Full-Screen Immersion</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Sound alert switch */}
          <button
            onClick={() => {
              setSoundAlertsEnabled(!soundAlertsEnabled);
              soundService.playClick();
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              soundAlertsEnabled 
                ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' 
                : 'bg-slate-800 text-slate-500 border-slate-700'
            }`}
          >
            <Bell className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">5m Reminder Bell</span>
          </button>

          {/* Fullscreen Button */}
          <button
            onClick={toggleFullscreen}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-500/15 text-sky-400 border border-sky-500/30 hover:bg-sky-500/25 transition-all"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">{isFullscreen ? 'Exit Fullscreen' : 'Fullscreen Focus'}</span>
          </button>
        </div>
      </div>

      {/* 5-Minute Warning Banner */}
      {isLast5Minutes && (
        <div className="w-full max-w-xl mb-6 p-3 rounded-xl bg-amber-500/15 border border-amber-500/40 text-amber-300 text-center animate-pulse z-10 flex items-center justify-center gap-2">
          <Bell className="w-4 h-4 text-amber-400 animate-bounce" />
          <span className="text-xs sm:text-sm font-bold tracking-wide uppercase">
            5 MINUTES REMAINING — WRAP UP FINAL THOUGHTS &amp; REVISIONS
          </span>
        </div>
      )}

      {/* Completion Banner */}
      {isCompleted && (
        <div className="w-full max-w-xl mb-6 p-4 rounded-xl bg-emerald-500/20 border border-emerald-500/50 text-emerald-300 text-center animate-slide-up z-10 flex items-center justify-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <span className="text-sm font-extrabold tracking-wide uppercase">
            SESSION COMPLETE! OFFICER OBJECTIVE ACHIEVED.
          </span>
        </div>
      )}

      {/* Centerpiece: Big Radial Timer Cockpit */}
      <div className="relative flex items-center justify-center my-6 z-10">
        {/* SVG Circular Progress Ring */}
        <svg className="w-72 h-72 sm:w-96 sm:h-96 -rotate-90 transform">
          <circle
            cx="50%"
            cy="50%"
            r="44%"
            className="stroke-[var(--border-color)] fill-none stroke-[8px]"
          />
          <circle
            cx="50%"
            cy="50%"
            r="44%"
            className={`fill-none stroke-[10px] transition-all duration-1000 ${
              isLast5Minutes 
                ? 'stroke-amber-400' 
                : isCompleted 
                  ? 'stroke-emerald-400' 
                  : 'stroke-sky-400'
            }`}
            strokeDasharray={2 * Math.PI * 165}
            strokeDashoffset={(2 * Math.PI * 165) * (1 - progressPercent / 100)}
            strokeLinecap="round"
          />
        </svg>

        {/* Center Digital Clock Display */}
        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className="text-[11px] sm:text-xs font-bold tracking-widest uppercase text-[var(--text-muted)] mb-1">
            {isRunning ? 'TACTICAL STUDY CADENCE' : isCompleted ? 'MISSION ACCOMPLISHED' : 'STANDBY READY'}
          </span>
          <span className={`font-mono font-black tracking-tight text-5xl sm:text-7xl ${
            isLast5Minutes 
              ? 'text-amber-400 animate-pulse' 
              : isCompleted 
                ? 'text-emerald-400' 
                : 'text-[var(--text-primary)]'
          }`}>
            {formatTime(timeRemaining)}
          </span>
          <span className="text-xs text-[var(--text-muted)] mt-2 font-medium">
            {Math.round(progressPercent)}% elapsed of {selectedMinutes}m drill
          </span>
        </div>
      </div>

      {/* Main Control Actions */}
      <div className="flex items-center gap-4 z-10 my-4">
        <button
          onClick={handlePlayPause}
          className={`px-8 py-3.5 rounded-xl text-base font-extrabold shadow-lg flex items-center gap-2.5 transition-all ${
            isRunning 
              ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-amber-600/30' 
              : 'bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white shadow-sky-500/30'
          }`}
        >
          {isRunning ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 fill-current" />}
          <span>{isRunning ? 'Pause Session' : isCompleted ? 'Restart Session' : 'Start Focus'}</span>
        </button>

        <button
          onClick={handleReset}
          title="Reset Timer"
          className="p-3.5 rounded-xl border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)] transition-all"
        >
          <RotateCcw className="w-5 h-5" />
        </button>
      </div>

      {/* Presets & Custom Input */}
      {!isRunning && (
        <div className="w-full max-w-xl z-10 mt-4 space-y-3">
          <div className="flex flex-wrap items-center justify-center gap-2">
            {PRESETS.map((p) => (
              <button
                key={p.minutes}
                onClick={() => handleSelectPreset(p.minutes)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  selectedMinutes === p.minutes && !customMinutes
                    ? 'bg-sky-500 text-white shadow-md shadow-sky-500/30'
                    : 'bg-[var(--bg-card)] text-[var(--text-secondary)] border border-[var(--border-color)] hover:border-sky-400'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleCustomSubmit} className="flex items-center justify-center gap-2">
            <input
              type="number"
              placeholder="Custom mins (1-360)"
              value={customMinutes}
              onChange={(e) => setCustomMinutes(e.target.value)}
              className="w-40 px-3 py-1.5 text-xs rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-primary)] focus:outline-none focus:border-sky-400"
            />
            <button
              type="submit"
              className="px-3 py-1.5 text-xs font-bold rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-sky-500 hover:text-white transition-all"
            >
              Set Time
            </button>
          </form>
        </div>
      )}

      {/* Focus Scratchpad */}
      <div className="w-full max-w-xl mt-6 z-10">
        <div className="glass-card p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="flex items-center gap-2 text-xs font-bold text-[var(--text-secondary)]">
              <FileText className="w-3.5 h-3.5 text-sky-400" />
              Focus Scratchpad / Candidate Notes
            </span>
            <span className="text-[10px] text-[var(--text-muted)]">Autosaved locally</span>
          </div>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Jot down tactical ideas, story keywords, or psychological reflections..."
            rows={3}
            className="w-full p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-color)] text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-sky-400 resize-none font-mono"
          />
        </div>
      </div>

      {/* Motivational Quote Footer */}
      <div className="w-full max-w-2xl mt-8 text-center z-10">
        <p className="text-xs italic text-[var(--text-muted)] max-w-lg mx-auto">
          {QUOTES[quoteIndex]}
        </p>
      </div>
    </div>
  );
}

