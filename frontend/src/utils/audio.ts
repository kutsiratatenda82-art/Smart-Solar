/**
 * Professional Alert Sound Engine
 * Classic beep-beep-beep pattern like a security system or smoke detector.
 * Clean sine tones with precise timing and proper gain staging.
 */
class SirenEngine {
  private audioCtx: AudioContext | null = null;
  private isPlaying = false;
  private generation = 0;
  private loopTimer: number | null = null;

  // Beep configuration
  private readonly BEEP_FREQ = 2400;       // Hz — classic alert frequency
  private readonly BEEP_DURATION = 0.15;   // seconds each beep lasts
  private readonly BEEP_GAP = 0.1;         // seconds of silence between beeps
  private readonly BEEPS_PER_GROUP = 3;    // 3 beeps per group
  private readonly GROUP_PAUSE = 1.0;      // seconds of silence between groups

  public init() {
    if (!this.audioCtx) {
      this.audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  public start() {
    if (this.isPlaying) return;
    this.init();
    if (!this.audioCtx) return;

    this.generation++;
    this.isPlaying = true;

    this.scheduleLoop();
  }

  private scheduleLoop() {
    if (!this.isPlaying) return;

    this.playBeepGroup();

    // Total duration of one group: (beep + gap) * count + extra pause
    const groupDurationMs =
      (this.BEEP_DURATION + this.BEEP_GAP) * this.BEEPS_PER_GROUP * 1000 +
      this.GROUP_PAUSE * 1000;

    this.loopTimer = window.setTimeout(() => {
      if (this.isPlaying) this.scheduleLoop();
    }, groupDurationMs);
  }

  private playBeepGroup() {
    if (!this.audioCtx || this.audioCtx.state === 'closed') return;

    const now = this.audioCtx.currentTime;

    for (let i = 0; i < this.BEEPS_PER_GROUP; i++) {
      const beepStart = now + i * (this.BEEP_DURATION + this.BEEP_GAP);
      this.playBeep(beepStart);
    }
  }

  private playBeep(startTime: number) {
    if (!this.audioCtx) return;

    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(this.BEEP_FREQ, startTime);

    // Clean envelope: quick fade-in, sustain, quick fade-out (no clicks)
    gain.gain.setValueAtTime(0, startTime);
    gain.gain.linearRampToValueAtTime(0.6, startTime + 0.01);
    gain.gain.setValueAtTime(0.6, startTime + this.BEEP_DURATION - 0.01);
    gain.gain.linearRampToValueAtTime(0, startTime + this.BEEP_DURATION);

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);

    osc.start(startTime);
    osc.stop(startTime + this.BEEP_DURATION + 0.01);

    // Auto-cleanup after the beep finishes
    osc.onended = () => {
      osc.disconnect();
      gain.disconnect();
    };
  }

  public stop() {
    if (!this.isPlaying) return;

    this.isPlaying = false;
    this.generation++;

    if (this.loopTimer !== null) {
      window.clearTimeout(this.loopTimer);
      this.loopTimer = null;
    }

    // Don't close audioCtx — keep it unlocked for future alerts
  }
}

export const siren = new SirenEngine();
