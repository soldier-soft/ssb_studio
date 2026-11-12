/**
 * Procedural Web Audio API sound effects engine for SSB Practice Studio.
 * Zero external audio files required — 100% reliable offline.
 * Developed by Lt. V. Elangovan
 */

class SoundEffectsService {
  constructor() {
    this.ctx = null;
    this.muted = localStorage.getItem('ssb_audio_muted') === 'true';
    this.volume = parseFloat(localStorage.getItem('ssb_audio_volume') || '0.7');
  }

  _initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
  }

  setMuted(muted) {
    this.muted = !!muted;
    localStorage.setItem('ssb_audio_muted', this.muted ? 'true' : 'false');
  }

  isMuted() {
    return this.muted;
  }

  setVolume(vol) {
    this.volume = Math.max(0, Math.min(1, vol));
    localStorage.setItem('ssb_audio_volume', String(this.volume));
  }

  getVolume() {
    return this.volume;
  }

  playTone(freq, duration = 0.15, type = 'sine', peakGain = 0.2, startDelay = 0) {
    if (this.muted || this.volume <= 0) return;
    try {
      this._initContext();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime + startDelay);

      const effectiveGain = peakGain * this.volume;
      const startTime = this.ctx.currentTime + startDelay;
      const endTime = startTime + duration;

      gain.gain.setValueAtTime(0.001, startTime);
      gain.gain.exponentialRampToValueAtTime(effectiveGain, startTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, endTime);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(startTime);
      osc.stop(endTime);
    } catch (e) {
      console.warn('Audio tone play failed:', e);
    }
  }

  // Button click tick
  playClick() {
    this.playTone(800, 0.04, 'triangle', 0.1);
  }

  // 3-2-1 countdown tick
  playCountdown(count) {
    if (count > 0) {
      this.playTone(520, 0.08, 'sine', 0.2);
    } else {
      // Go!
      this.playTone(880, 0.25, 'triangle', 0.3);
    }
  }

  // Hurry-up pulse for last 5 seconds of test slide
  playHurryWarning() {
    this.playTone(660, 0.06, 'sawtooth', 0.12);
  }

  // Slide advance notification
  playSlideAdvance() {
    this.playTone(440, 0.06, 'sine', 0.15);
    this.playTone(660, 0.08, 'sine', 0.15, 0.07);
  }

  /**
   * 5-Minute Reminder Alarm for Focus Page.
   * Plays a pleasant 3-tone chime reminder and announces "5 minutes remaining".
   */
  playFocusFiveMinAlarm() {
    if (this.muted) return;
    // Chime chords: E5 (659Hz), G#5 (830Hz), B5 (987Hz), E6 (1318Hz)
    this.playTone(659, 0.3, 'sine', 0.3, 0.0);
    this.playTone(830, 0.35, 'sine', 0.3, 0.2);
    this.playTone(987, 0.4, 'sine', 0.35, 0.4);
    this.playTone(1318, 0.6, 'triangle', 0.4, 0.6);

    // Optional voice announcement if speech synthesis is available
    if ('speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance("Five minutes remaining. Wrap up your notes.");
        utter.rate = 1.0;
        utter.pitch = 1.0;
        utter.volume = this.volume;
        window.speechSynthesis.speak(utter);
      } catch (e) {}
    }
  }

  /**
   * Final Completion Fanfare for Focus & Tests.
   */
  playCompletionAlarm() {
    if (this.muted) return;
    // Military Bugle Fanfare: C4 (261), G4 (392), C5 (523), E5 (659), G5 (784)
    const notes = [
      { f: 392, d: 0.18, t: 0.0 },
      { f: 523, d: 0.18, t: 0.18 },
      { f: 659, d: 0.22, t: 0.36 },
      { f: 784, d: 0.45, t: 0.58 },
    ];
    notes.forEach((n) => {
      this.playTone(n.f, n.d, 'triangle', 0.35, n.t);
    });

    if ('speechSynthesis' in window) {
      try {
        const utter = new SpeechSynthesisUtterance("Session complete. Excellent work, officer.");
        utter.rate = 1.0;
        utter.pitch = 1.0;
        utter.volume = this.volume;
        window.speechSynthesis.speak(utter);
      } catch (e) {}
    }
  }
}

export const soundService = new SoundEffectsService();
export default soundService;

