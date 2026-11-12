import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Flame, 
  Clock, 
  Zap, 
  Target, 
  Image as ImageIcon, 
  Download, 
  ArrowRight, 
  RotateCw, 
  CheckCircle2, 
  Award,
  Sparkles
} from 'lucide-react';
import soundService from '../services/soundEffects';
import itemPoolService from '../services/itemPoolService';

export default function Dashboard({ setActivePage }) {
  const [metrics, setMetrics] = useState(null);
  const [streak, setStreak] = useState(0);

  useEffect(() => {
    setMetrics(itemPoolService.getPoolMetrics());
    setStreak(itemPoolService.getStreak());
  }, []);

  return (
    <div className="max-w-7xl mx-auto my-8 px-4 sm:px-6 lg:px-8 space-y-8 animate-slide-up">
      {/* Hero Header & Developer Banner */}
      <div className="glass-card p-6 sm:p-10 relative overflow-hidden">
        <div className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-sky-500/10 blur-3xl pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-3 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-sky-500/15 text-sky-400 border border-sky-500/30">
                100% Offline-First Preparation
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                🎖️ Developed by Lt. V. Elangovan
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[var(--text-primary)] tracking-tight">
              SSB Psychological <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-blue-400 to-indigo-400">Preparation Studio</span>
            </h1>

            <p className="text-sm sm:text-base text-[var(--text-secondary)] leading-relaxed">
              Curated for Indian Armed Forces Aspirants (NDA, CDS, AFCAT, TGC). Practice WAT, SRT, and TAT with authentic exam timing, non-repeating cycle rotation, and immersive audio cues.
            </p>
          </div>

          {/* Daily Streak & Ready Badge */}
          <div className="flex flex-col sm:flex-row lg:flex-col gap-3 w-full sm:w-auto">
            <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)] flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold">
                <Flame className="w-6 h-6 animate-pulse" />
              </div>
              <div>
                <div className="text-[11px] uppercase font-bold text-[var(--text-muted)]">Active Routine Streak</div>
                <div className="text-xl font-black text-[var(--text-primary)]">{streak} Days</div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)] flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <div className="text-[11px] uppercase font-bold text-[var(--text-muted)]">Candidate State</div>
                <div className="text-sm font-extrabold text-emerald-400">Battle Ready &bull; OLQ Focused</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Featured: Daily Task & Focus Drill Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Daily Task Card */}
        <div className="glass-card p-6 sm:p-8 flex flex-col justify-between border-sky-500/30 hover:border-sky-400 transition-all group">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-amber-500 to-orange-600 flex items-center justify-center text-white shadow-lg shadow-orange-500/20">
                <Flame className="w-6 h-6" />
              </div>
              <span className="text-[10px] font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                Recommended Routine
              </span>
            </div>

            <h2 className="text-xl font-black text-[var(--text-primary)]">Today's Daily Task Routine</h2>
            <p className="text-xs sm:text-sm text-[var(--text-secondary)] mt-2">
              Curated daily workout: <strong>2 TAT Pictures</strong>, <strong>15 WAT Words</strong>, and <strong>15 SRT Situations</strong>. Drawn with the 2-day non-repeater difference engine.
            </p>

            <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold text-[var(--text-muted)]">
              <span className="px-2.5 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">2 TAT Stories</span>
              <span className="px-2.5 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">15 WAT Words</span>
              <span className="px-2.5 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">15 SRT Situations</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--border-color)] flex items-center justify-between">
            <span className="text-xs text-[var(--text-muted)]">Estimated: ~22 Mins</span>
            <button
              onClick={() => {
                soundService.playClick();
                setActivePage('dailytask');
              }}
              className="btn-primary text-xs py-2 px-4 group-hover:scale-105"
            >
              <span>Launch Daily Routine</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Focus Page Card */}
        <div className="glass-card p-6 sm:p-8 flex flex-col justify-between border-amber-500/30 hover:border-amber-400 transition-all group">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-sky-500/20">
                <Clock className="w-6 h-6" />
              </div>
              <span className="text-[10px] font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
                Full-Screen Timer
              </span>
            </div>

            <h2 className="text-xl font-black text-[var(--text-primary)]">Officer Focus Drill Page</h2>
            <p className="text-xs sm:text-sm text-[var(--text-secondary)] mt-2">
              Deep work &amp; study countdown cockpit. Features full-screen mode, <strong>audio alarm reminder at last 5 minutes</strong>, and completion fanfare.
            </p>

            <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold text-[var(--text-muted)]">
              <span className="px-2.5 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">5-Min Warning Bell</span>
              <span className="px-2.5 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">Pomodoro &amp; Mock Presets</span>
              <span className="px-2.5 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">Scratchpad Notes</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--border-color)] flex items-center justify-between">
            <span className="text-xs text-[var(--text-muted)]">Customizable Duration</span>
            <button
              onClick={() => {
                soundService.playClick();
                setActivePage('focus');
              }}
              className="btn-primary text-xs py-2 px-4 bg-amber-600 hover:bg-amber-500 group-hover:scale-105"
            >
              <span>Open Focus Page</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Psychological Test Modules */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-black text-[var(--text-primary)]">Individual Psychological Batteries</h2>
            <p className="text-xs text-[var(--text-muted)]">Direct drills for specific written tests conducted on Day 2</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* WAT Drill */}
          <div 
            onClick={() => { soundService.playClick(); setActivePage('wat'); }}
            className="glass-card p-6 cursor-pointer hover:border-blue-400 transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold mb-4 group-hover:scale-110 transition-transform">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className="text-base font-extrabold text-[var(--text-primary)]">WAT: Word Association</h3>
            <p className="text-xs text-[var(--text-secondary)] mt-1.5 leading-relaxed">
              60 words at 15s cadence. Rapid spontaneous writing testing emotional stability and courage.
            </p>
            <div className="mt-4 flex items-center justify-between text-xs font-bold text-blue-400">
              <span>Start 15-Word / 60-Word Drill</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* SRT Drill */}
          <div 
            onClick={() => { soundService.playClick(); setActivePage('srt'); }}
            className="glass-card p-6 cursor-pointer hover:border-emerald-400 transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold mb-4 group-hover:scale-110 transition-transform">
              <Target className="w-5 h-5" />
            </div>
            <h3 className="text-base font-extrabold text-[var(--text-primary)]">SRT: Situation Reaction</h3>
            <p className="text-xs text-[var(--text-secondary)] mt-1.5 leading-relaxed">
              60 real-life crisis scenarios adhering strictly to Rule 1 (1-60 order) and Rule 2 (ending in '...').
            </p>
            <div className="mt-4 flex items-center justify-between text-xs font-bold text-emerald-400">
              <span>Start 30s Decision Drill</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* TAT Drill */}
          <div 
            onClick={() => { soundService.playClick(); setActivePage('tat'); }}
            className="glass-card p-6 cursor-pointer hover:border-indigo-400 transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold mb-4 group-hover:scale-110 transition-transform">
              <ImageIcon className="w-5 h-5" />
            </div>
            <h3 className="text-base font-extrabold text-[var(--text-primary)]">TAT: Thematic Apperception</h3>
            <p className="text-xs text-[var(--text-secondary)] mt-1.5 leading-relaxed">
              12 picture slides with 30s observation and 4m story writing, including Picture #12 blank slide.
            </p>
            <div className="mt-4 flex items-center justify-between text-xs font-bold text-indigo-400">
              <span>Launch 12-Picture Battery</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      </div>

      {/* 2-Day Rotation & Cycle Diagnostics */}
      {metrics && (
        <div className="glass-card p-6 border-[var(--border-color)]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <div>
              <h3 className="text-sm font-extrabold uppercase tracking-wider text-[var(--text-primary)]">
                Smart Rotation &amp; Non-Repeater Diagnostics
              </h3>
              <p className="text-xs text-[var(--text-muted)]">
                Excludes items seen over the last 2 days. When a pool is exhausted, it automatically shuffles once and restarts from the first.
              </p>
            </div>
            <span className="text-[11px] font-mono text-sky-400">Status: Active Rotation</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-3.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div className="text-xs font-bold text-[var(--text-muted)]">WAT Words Bank</div>
              <div className="text-lg font-black text-blue-400 mt-1">
                {metrics.wat.remainingInCycle} / {metrics.wat.total} Remaining in Cycle
              </div>
              <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">
                {metrics.wat.practicedLast2Days} words completed in last 2 days
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div className="text-xs font-bold text-[var(--text-muted)]">SRT Situations Bank</div>
              <div className="text-lg font-black text-emerald-400 mt-1">
                {metrics.srt.remainingInCycle} / {metrics.srt.total} Remaining in Cycle
              </div>
              <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">
                {metrics.srt.practicedLast2Days} situations completed in last 2 days
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div className="text-xs font-bold text-[var(--text-muted)]">TAT Scenes Bank</div>
              <div className="text-lg font-black text-indigo-400 mt-1">
                {metrics.tat.remainingInCycle} / {metrics.tat.total} Remaining in Cycle
              </div>
              <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">
                {metrics.tat.practicedLast2Days} scenes completed in last 2 days
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Windows Desktop App Download Banner */}
      <div className="glass-card p-6 sm:p-8 border-sky-500/20 bg-gradient-to-r from-sky-950/40 via-blue-950/20 to-slate-900/60 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div>
          <span className="text-[10px] uppercase font-extrabold px-2.5 py-0.5 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30">
            Windows Desktop Application
          </span>
          <h3 className="text-lg sm:text-xl font-black text-[var(--text-primary)] mt-1.5">
            Prefer Running 100% Offline on Windows PC?
          </h3>
          <p className="text-xs text-[var(--text-secondary)] mt-1 max-w-xl">
            Download the standalone Windows package (~72 MB) with the 1-click batch shortcut installer. No installation wizard required.
          </p>
        </div>

        <button
          onClick={() => {
            soundService.playClick();
            setActivePage('download');
          }}
          className="btn-primary whitespace-nowrap px-6 py-3"
        >
          <Download className="w-4 h-4" />
          <span>Download App &amp; Setup</span>
        </button>
      </div>

      {/* Footer / Credit */}
      <footer className="text-center py-6 text-xs text-[var(--text-muted)] space-y-1">
        <p>SSB PRACTICE STUDIO &bull; OFFICER ASSESSMENT</p>
        <p className="font-semibold text-sky-400">Developed by Lt. V. Elangovan</p>
        <p>Free &amp; Open Source for Indian Armed Forces Aspirants &bull; Army &bull; Navy &bull; Air Force &bull; Coast Guard</p>
      </footer>
    </div>
  );
}

