import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Flame, 
  Clock, 
  Zap, 
  Target, 
  Image as ImageIcon, 
  Download, 
  Volume2, 
  VolumeX, 
  Sun, 
  Moon,
  Menu,
  X
} from 'lucide-react';
import soundService from '../services/soundEffects';
import itemPoolService from '../services/itemPoolService';

export default function Navbar({ activePage, setActivePage, theme, toggleTheme }) {
  const [streak, setStreak] = useState(0);
  const [muted, setMuted] = useState(soundService.isMuted());
  const [volume, setVolume] = useState(soundService.getVolume());
  const [showVolSlider, setShowVolSlider] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    setStreak(itemPoolService.getStreak());
  }, [activePage]);

  const handleMuteToggle = () => {
    const next = !muted;
    setMuted(next);
    soundService.setMuted(next);
    if (!next) soundService.playClick();
  };

  const handleVolumeChange = (e) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    soundService.setVolume(val);
    if (muted) {
      setMuted(false);
      soundService.setMuted(false);
    }
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Shield },
    { id: 'dailytask', label: 'Daily Task', icon: Flame, badge: streak > 0 ? `${streak}d` : null },
    { id: 'focus', label: 'Focus Page', icon: Clock, highlight: true },
    { id: 'wat', label: 'WAT Practice', icon: Zap },
    { id: 'srt', label: 'SRT Drill', icon: Target },
    { id: 'tat', label: 'TAT Studio', icon: ImageIcon },
    { id: 'download', label: 'Download App', icon: Download },
  ];

  return (
    <header className="sticky top-0 z-50 backdrop-blur-xl border-b border-[var(--border-color)] bg-[var(--bg-card)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Developer Honor */}
          <div 
            onClick={() => { soundService.playClick(); setActivePage('dashboard'); }}
            className="flex items-center gap-3 cursor-pointer select-none group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 group-hover:scale-105 transition-transform">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold tracking-wider text-base text-[var(--text-primary)]">SSB STUDIO</span>
                <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">v2.0 React</span>
              </div>
              <div className="text-[11px] text-[var(--text-muted)] font-medium">
                Developed by <strong className="text-sky-400">Lt. V. Elangovan</strong>
              </div>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    soundService.playClick();
                    setActivePage(item.id);
                  }}
                  className={`relative flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-all ${
                    isActive 
                      ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm shadow-sky-500/10' 
                      : item.highlight 
                        ? 'text-amber-400 hover:bg-amber-500/10 hover:text-amber-300'
                        : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="px-1.5 py-0.2 rounded-full text-[10px] font-extrabold bg-amber-500 text-slate-950">
                      {item.badge}
                    </span>
                  )}
                  {item.highlight && !isActive && (
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                  )}
                </button>
              );
            })}
          </nav>

          {/* Audio Controls & Theme Switch */}
          <div className="flex items-center gap-2">
            {/* Audio Volume Popover */}
            <div className="relative">
              <button
                onClick={handleMuteToggle}
                onMouseEnter={() => setShowVolSlider(true)}
                title={muted ? "Unmute Sound Effects" : "Mute Sound Effects"}
                className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors"
              >
                {muted ? (
                  <VolumeX className="w-4 h-4 text-red-400" />
                ) : (
                  <Volume2 className="w-4 h-4 text-sky-400" />
                )}
              </button>

              {showVolSlider && (
                <div 
                  onMouseLeave={() => setShowVolSlider(false)}
                  className="absolute right-0 top-12 p-3 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl shadow-xl w-40 z-50 animate-pop-in"
                >
                  <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] mb-1">
                    <span>Sound Effects</span>
                    <span>{Math.round(volume * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={volume}
                    onChange={handleVolumeChange}
                    className="w-full accent-sky-400 cursor-pointer"
                  />
                </div>
              )}
            </div>

            {/* Theme Toggle Button */}
            <button
              onClick={() => {
                soundService.playClick();
                toggleTheme();
              }}
              title="Toggle Color Theme"
              className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors"
            >
              {theme === 'dark' ? (
                <Sun className="w-4 h-4 text-amber-400" />
              ) : (
                <Moon className="w-4 h-4 text-indigo-500" />
              )}
            </button>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-[var(--border-color)] bg-[var(--bg-secondary)] px-4 py-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  soundService.playClick();
                  setActivePage(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-semibold ${
                  isActive
                    ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-500 text-slate-950">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
}

