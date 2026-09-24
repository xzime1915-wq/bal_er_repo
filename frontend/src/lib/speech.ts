/** Browser/Electron TTS — SENZ speaks back to you */

function cleanForSpeech(text: string): string {
  return text
    .replace(/\[ok\][^\n]*/g, "")
    .replace(/https?:\/\/\S+/g, "")
    .split("\n")[0]
    .trim()
    .slice(0, 280);
}

function pickVoice(): SpeechSynthesisVoice | undefined {
  const voices = window.speechSynthesis.getVoices();
  return (
    voices.find((v) => v.lang.startsWith("en") && /google|natural/i.test(v.name)) ||
    voices.find((v) => v.lang.startsWith("en")) ||
    voices[0]
  );
}

export function speakText(text: string): Promise<void> {
  const clean = cleanForSpeech(text);
  if (!clean || !("speechSynthesis" in window)) {
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(clean);
    u.rate = 1.02;
    u.pitch = 1;
    const voice = pickVoice();
    if (voice) u.voice = voice;
    u.onend = () => resolve();
    u.onerror = () => resolve();
    window.speechSynthesis.speak(u);
  });
}

export function stopSpeaking(): void {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

// Preload voices (Electron/Chrome)
if (typeof window !== "undefined" && "speechSynthesis" in window) {
  window.speechSynthesis.getVoices();
  window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices();
  };
}
