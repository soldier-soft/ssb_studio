import React, { useState } from 'react';
import { Download, Terminal, Shield, Check, Copy, AlertTriangle, ExternalLink } from 'lucide-react';
import soundService from '../services/soundEffects';

export default function DownloadPage() {
  const [copied, setCopied] = useState(false);

  const copyCommand = () => {
    soundService.playClick();
    const cmd = "irm https://soldier-soft.github.io/ssb_studio/install.ps1 | iex";
    navigator.clipboard.writeText(cmd).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="max-w-5xl mx-auto my-8 px-4 sm:px-6 space-y-8 animate-slide-up">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <span className="px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-sky-500/10 text-sky-400 border border-sky-500/20">
          Windows 10 &amp; 11 Distribution
        </span>
        <h1 className="text-3xl font-black text-[var(--text-primary)]">
          Download SSB Practice Studio
        </h1>
        <p className="text-sm text-[var(--text-secondary)]">
          Run completely offline on your desktop. No account or internet connection needed.
        </p>
      </div>

      {/* 3 Step Quick Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6">
          <div className="text-3xl font-black text-sky-400 font-mono mb-2">01</div>
          <h3 className="text-base font-bold text-[var(--text-primary)]">Download ZIP Archive</h3>
          <p className="text-xs text-[var(--text-secondary)] mt-2">
            Download <code>SSB_Practice_Studio_Windows.zip</code> (~72 MB) containing the precompiled application and resources.
          </p>
        </div>

        <div className="glass-card p-6">
          <div className="text-3xl font-black text-sky-400 font-mono mb-2">02</div>
          <h3 className="text-base font-bold text-[var(--text-primary)]">Extract the Archive</h3>
          <p className="text-xs text-[var(--text-secondary)] mt-2">
            Right-click the ZIP and choose <strong>"Extract All..."</strong> to any directory such as <code>C:\SSB_Studio</code> or your Downloads folder.
          </p>
        </div>

        <div className="glass-card p-6">
          <div className="text-3xl font-black text-sky-400 font-mono mb-2">03</div>
          <h3 className="text-base font-bold text-[var(--text-primary)]">1-Click Desktop Setup</h3>
          <p className="text-xs text-[var(--text-secondary)] mt-2">
            Double-click <code>Setup_And_Create_Desktop_Shortcut.bat</code>. It creates your desktop icon with the official emblem and launches the app!
          </p>
        </div>
      </div>

      {/* Methods Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Method 1: Direct Download */}
        <div className="glass-card p-6 sm:p-8 flex flex-col justify-between border-sky-500/30">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center font-bold">
                <Download className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-black text-[var(--text-primary)]">Direct Windows ZIP</h3>
                <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">Recommended &bull; 72 MB</span>
              </div>
            </div>

            <p className="text-xs sm:text-sm text-[var(--text-secondary)] leading-relaxed">
              Complete standalone package with all psychological modules, 60-item banks, and the automatic desktop shortcut generator.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--border-color)] space-y-3">
            <a
              href="download/SSB_Practice_Studio_Windows.zip"
              download="SSB_Practice_Studio_Windows.zip"
              className="btn-primary w-full text-center py-3.5"
            >
              <Download className="w-4 h-4" />
              <span>Download ZIP Package (72 MB)</span>
            </a>

            <div className="text-center text-[11px] text-[var(--text-muted)]">
              Mirror: <a href="https://raw.githubusercontent.com/soldier-soft/ssb_studio/main/docs/download/SSB_Practice_Studio_Windows.zip" target="_blank" rel="noopener" className="text-sky-400 underline">GitHub Raw Direct Link</a>
            </div>
          </div>
        </div>

        {/* Method 2: PowerShell 1-Liner */}
        <div className="glass-card p-6 sm:p-8 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold">
                <Terminal className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-black text-[var(--text-primary)]">PowerShell 1-Liner</h3>
                <span className="text-[10px] text-purple-400 font-bold uppercase tracking-wider">Automated Install</span>
              </div>
            </div>

            <p className="text-xs sm:text-sm text-[var(--text-secondary)] leading-relaxed">
              Open PowerShell on Windows and paste this command. It downloads, extracts, creates the Desktop shortcut, and launches the application automatically:
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--border-color)] space-y-3">
            <div className="p-3 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-color)] font-mono text-xs text-sky-400 break-all select-all">
              irm https://soldier-soft.github.io/ssb_studio/install.ps1 | iex
            </div>

            <button
              onClick={copyCommand}
              className="btn-secondary w-full py-2.5 text-xs font-bold"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              <span>{copied ? 'Command Copied to Clipboard!' : 'Copy PowerShell Command'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Windows SmartScreen Banner */}
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-[var(--text-secondary)] leading-relaxed">
          <strong className="text-amber-400">Windows SmartScreen Note:</strong> Because this is an open-source indie executable, Windows SmartScreen may show a prompt: <em>"Windows protected your PC"</em>. Simply click <strong>"More info"</strong> and then click <strong>"Run anyway"</strong>. SSB Practice Studio is 100% offline, privacy-safe, and contains zero trackers.
        </div>
      </div>

      {/* Developer Honor Card */}
      <div className="glass-card p-6 sm:p-8 flex flex-col sm:flex-row items-center gap-6 border-sky-500/30">
        <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-sky-600 to-blue-700 flex items-center justify-center text-3xl shadow-lg shadow-sky-500/30 flex-shrink-0">
          👨‍✈️
        </div>
        <div className="space-y-1 text-center sm:text-left">
          <div className="text-xs uppercase font-extrabold text-sky-400 tracking-wider">
            Lead Developer &amp; Defense Mentor
          </div>
          <h2 className="text-xl font-black text-[var(--text-primary)]">
            Lt. V. Elangovan
          </h2>
          <p className="text-xs text-[var(--text-secondary)] leading-relaxed max-w-2xl">
            Created SSB Practice Studio to provide a realistic, distraction-free environment for young officers preparing for Services Selection Board interviews across the Indian Army, Navy, Air Force, and Coast Guard.
          </p>
        </div>
      </div>
    </div>
  );
}

