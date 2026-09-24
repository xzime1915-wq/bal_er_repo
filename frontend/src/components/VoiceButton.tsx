import { useCallback, useEffect, useRef, useState } from "react";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SpeechRecognitionType = any;

interface Props {
  enabled: boolean;
  listening: boolean;
  onEnable: () => void;
  onText: (text: string) => void;
  onServerListen: () => void;
}

export function VoiceButton({ enabled, listening, onEnable, onText, onServerListen }: Props) {
  const [browserListening, setBrowserListening] = useState(false);
  const recRef = useRef<SpeechRecognitionType | null>(null);

  const SpeechRecognition =
    (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionType }).SpeechRecognition ||
    (window as unknown as { webkitSpeechRecognition?: new () => SpeechRecognitionType })
      .webkitSpeechRecognition;

  const startBrowserListen = useCallback(() => {
    if (!SpeechRecognition) {
      onEnable();
      onServerListen();
      return;
    }
    onEnable();
    const rec = new SpeechRecognition();
    rec.lang = "bn-BD";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    recRef.current = rec;
    rec.onstart = () => setBrowserListening(true);
    rec.onend = () => setBrowserListening(false);
    rec.onerror = () => {
      setBrowserListening(false);
      onServerListen();
    };
    rec.onresult = (ev: { results: { [i: number]: { [j: number]: { transcript: string } } } }) => {
      const text = ev.results[0][0].transcript.trim();
      if (text) onText(text);
    };
    rec.start();
  }, [SpeechRecognition, onEnable, onServerListen, onText]);

  useEffect(() => {
    return () => {
      try {
        recRef.current?.stop();
      } catch {
        /* ignore */
      }
    };
  }, []);

  const active = listening || browserListening;

  return (
    <button
      type="button"
      onClick={startBrowserListen}
      className={`w-14 h-14 rounded-full border-2 flex items-center justify-center text-xl transition ${
        active
          ? "border-senz-green shadow-glow-green animate-pulse bg-senz-green/10"
          : enabled
            ? "border-senz-cyan text-senz-cyan hover:shadow-glow"
            : "border-senz-muted text-senz-muted hover:border-senz-cyan"
      }`}
      title="Click → bole din (chrome kholo, screenshot...)"
    >
      🎤
    </button>
  );
}
