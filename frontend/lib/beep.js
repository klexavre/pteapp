/**
 * playBeep()
 * ----------
 * Generates a short beep tone using the Web Audio API - no audio asset
 * file needed. Used to signal "start speaking now" before auto-recording
 * begins, matching the familiar PTE-style beep cue.
 */
export function playBeep({ frequency = 880, durationMs = 200, volume = 0.3 } = {}) {
  return new Promise((resolve) => {
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioContextClass();
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();

      oscillator.type = "sine";
      oscillator.frequency.value = frequency;
      gainNode.gain.value = volume;

      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);

      oscillator.start();
      setTimeout(() => {
        oscillator.stop();
        ctx.close();
        resolve();
      }, durationMs);
    } catch (err) {
      console.error("Beep playback failed:", err);
      resolve();
    }
  });
}
