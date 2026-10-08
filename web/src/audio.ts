import type { PaletteNote, Tone } from "./types";

let context: AudioContext | null = null;
let active: AudioNode[] = [];

function ctx() { context ??= new AudioContext(); return context; }
export function stopAudio() { active.forEach((node) => { try { (node as OscillatorNode).stop?.(); } catch {} }); active = []; }

export function playTone(tone: Tone) {
  if (!tone.available || !tone.frequency_hz) return;
  stopAudio();
  const audio = ctx();
  const now = audio.currentTime;
  const master = audio.createGain();
  const pan = audio.createStereoPanner(); pan.pan.value = tone.stereo_pan ?? 0;
  master.gain.setValueAtTime(0.0001, now);
  master.gain.exponentialRampToValueAtTime(Math.max(0.02, (tone.velocity ?? .5) * .28), now + (tone.attack ?? .1));
  master.gain.exponentialRampToValueAtTime(0.0001, now + (tone.release ?? 1.2) + (tone.attack ?? .1));
  master.connect(pan).connect(audio.destination);
  const harmonics = 1 + Math.round((tone.harmonic_richness ?? 0) * 3);
  for (let harmonic = 1; harmonic <= harmonics; harmonic++) {
    const oscillator = audio.createOscillator();
    const gain = audio.createGain(); gain.gain.value = 1 / (harmonic * harmonics);
    oscillator.type = harmonic === 1 ? "sine" : "triangle";
    oscillator.frequency.value = tone.frequency_hz * harmonic;
    oscillator.connect(gain).connect(master); oscillator.start(now); oscillator.stop(now + (tone.release ?? 1.2) + .4);
    active.push(oscillator);
  }
}

export function playArpeggio(notes: PaletteNote[]) {
  stopAudio(); const audio = ctx(); let cursor = audio.currentTime;
  for (const note of notes) {
    const oscillator = audio.createOscillator(); const gain = audio.createGain();
    oscillator.type = "sine"; oscillator.frequency.value = note.frequency_hz;
    gain.gain.setValueAtTime(.0001, cursor); gain.gain.exponentialRampToValueAtTime(note.velocity * .22, cursor + .04);
    gain.gain.exponentialRampToValueAtTime(.0001, cursor + note.duration_seconds);
    oscillator.connect(gain).connect(audio.destination); oscillator.start(cursor); oscillator.stop(cursor + note.duration_seconds + .05);
    active.push(oscillator); cursor += note.duration_seconds;
  }
}
