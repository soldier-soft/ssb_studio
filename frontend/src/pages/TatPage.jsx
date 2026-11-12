import React, { useState, useEffect } from 'react';
import { Image as ImageIcon, Play, RotateCcw, CheckCircle2, ChevronRight, Eye, PenTool } from 'lucide-react';
import soundService from '../services/soundEffects';
import itemPoolService from '../services/itemPoolService';

export default function TatPage() {
  const [scenes, setScenes] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [subPhase, setSubPhase] = useState('view'); // 'view' (30s) or 'write' (240s)
  const [timeRemaining, setTimeRemaining] = useState(30);
  const [isRunning, setIsRunning] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [stories, setStories] = useState({});

  const loadScenes = () => {
    const list = itemPoolService.getItems('tat', 12);
    setScenes(list);
    setCurrentIndex(0);
    setSubPhase('view');
    setTimeRemaining(30);
    setIsRunning(false);
    setIsCompleted(false);
    setStories({});
  };

  useEffect(() => {
    loadScenes();
  }, []);

  // Dual phase timer
  useEffect(() => {
    let interval = null;
    if (isRunning && !isCompleted && scenes.length > 0) {
      interval = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            if (subPhase === 'view') {
              soundService.playSlideAdvance();
              setSubPhase('write');
              return 240; // 4 minutes
            } else {
              soundService.playSlideAdvance();
              if (currentIndex + 1 < scenes.length) {
                setCurrentIndex((i) => i + 1);
                setSubPhase('view');
                return 30; // 30s view
              } else {
                setIsRunning(false);
                setIsCompleted(true);
                soundService.playCompletionAlarm();
                return 0;
              }
            }
          }
          if (prev === 6 && subPhase === 'view') {
            soundService.playHurryWarning();
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning, currentIndex, subPhase, scenes, isCompleted]);

  const currentScene = scenes[currentIndex];

  const handleNextSlide = () => {
    soundService.playSlideAdvance();
    if (currentIndex + 1 < scenes.length) {
      setCurrentIndex((i) => i + 1);
      setSubPhase('view');
      setTimeRemaining(30);
    } else {
      setIsRunning(false);
      setIsCompleted(true);
      soundService.playCompletionAlarm();
    }
  };

  return (
    <div className="max-w-4xl mx-auto my-8 px-4">
      <div className="glass-card p-6 sm:p-10 animate-slide-up space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse" />
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-indigo-400">
                Thematic Apperception Test (TAT)
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-[var(--text-primary)] mt-1">
              12 PICTURES &bull; 30S VIEW + 4M WRITE
            </h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-[10px] font-bold uppercase text-[var(--text-muted)]">
                {subPhase === 'view' ? 'VIEWING PHASE' : 'WRITING PHASE'}
              </div>
              <div className={`font-mono text-3xl font-black ${
                timeRemaining <= 10 && subPhase === 'view' ? 'text-amber-400 animate-pulse' : 'text-indigo-400'
              }`}>
                {Math.floor(timeRemaining / 60)}:{String(timeRemaining % 60).padStart(2, '0')}
              </div>
            </div>
          </div>
        </div>

        {/* Not Started */}
        {!isRunning && !isCompleted && (
          <div className="py-12 text-center space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto shadow-lg shadow-indigo-500/20">
              <ImageIcon className="w-8 h-8" />
            </div>
            <div className="max-w-md mx-auto">
              <h2 className="text-lg font-bold text-[var(--text-primary)]">Ready for 12-Picture TAT Battery?</h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                30 seconds viewing per picture followed by 4 minutes story writing. Slide #12 is the official Blank Slide.
              </p>
            </div>
            <button
              onClick={() => {
                soundService.playCountdown(0);
                setIsRunning(true);
              }}
              className="btn-primary px-8 py-3.5 text-base bg-indigo-600 hover:bg-indigo-500"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Begin TAT Battery</span>
            </button>
          </div>
        )}

        {/* Active Test */}
        {isRunning && currentScene && (
          <div className="space-y-6">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-mono">
              <span>PICTURE {currentIndex + 1} OF 12</span>
              <span>{currentScene.isBlank ? 'BLANK SLIDE #12' : currentScene.title}</span>
            </div>

            {/* Picture Canvas / Graphic Box */}
            <div className={`relative aspect-video rounded-2xl border border-[var(--border-color)] overflow-hidden flex flex-col items-center justify-center p-8 text-center transition-all ${
              currentScene.isBlank 
                ? 'bg-slate-900 border-dashed border-2 border-slate-700' 
                : 'bg-gradient-to-tr from-slate-950 via-slate-900 to-indigo-950'
            }`}>
              {currentScene.isBlank ? (
                <div>
                  <div className="text-2xl font-black text-slate-300">BLANK SLIDE #12</div>
                  <p className="text-xs text-slate-500 mt-2 max-w-md">
                    Bring into your mind any picture of your choice. Outline a constructive, positive story with a strong character.
                  </p>
                </div>
              ) : (
                <div>
                  <div className="w-16 h-16 rounded-full bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center mx-auto mb-4">
                    <ImageIcon className="w-8 h-8 text-indigo-400" />
                  </div>
                  <h3 className="text-xl font-extrabold text-[var(--text-primary)]">{currentScene.title}</h3>
                  <p className="text-sm text-[var(--text-secondary)] mt-2 max-w-lg mx-auto">{currentScene.desc}</p>
                </div>
              )}

              {/* Sub-phase overlay banner */}
              <div className="absolute top-4 right-4 flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-slate-950/80 border border-indigo-500/30 text-indigo-300 backdrop-blur-md">
                {subPhase === 'view' ? <Eye className="w-3.5 h-3.5 text-amber-400" /> : <PenTool className="w-3.5 h-3.5 text-emerald-400" />}
                <span>{subPhase === 'view' ? 'Observe Picture (30s)' : 'Write Story (4m)'}</span>
              </div>
            </div>

            {/* Story Editor */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-[var(--text-secondary)]">
                  Candidate Story Submission
                </label>
                <span className="text-xs text-[var(--text-muted)] font-mono">
                  {stories[currentScene.id]?.split(/\s+/).filter(Boolean).length || 0} words
                </span>
              </div>
              <textarea
                rows={6}
                disabled={subPhase === 'view'}
                placeholder={subPhase === 'view' ? "Observing picture details... Story writing unlocks after 30s." : "Describe: 1. What led to the situation, 2. What is happening now, 3. Thoughts & feelings, 4. Final resolution."}
                value={stories[currentScene.id] || ''}
                onChange={(e) => setStories({ ...stories, [currentScene.id]: e.target.value })}
                className="w-full p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)] text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-indigo-400 font-sans resize-none"
              />
              <div className="flex justify-end mt-2">
                <button onClick={handleNextSlide} className="btn-secondary text-xs py-2 px-5">
                  <span>Advance Slide &rarr;</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Completed */}
        {isCompleted && (
          <div className="space-y-6 text-center animate-slide-up">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
            <h2 className="text-2xl font-black text-[var(--text-primary)]">12-PICTURE TAT BATTERY COMPLETE!</h2>
            <p className="text-xs text-[var(--text-secondary)]">
              All 12 stories successfully captured. Excellent practice session!
            </p>
            <div className="pt-4 flex justify-center">
              <button onClick={loadScenes} className="btn-primary bg-indigo-600 hover:bg-indigo-500">
                <RotateCcw className="w-4 h-4" />
                <span>Practice Another TAT Series</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

