import { useCallback, useEffect, useRef, useState } from "react";
import { speakText, stopSpeaking } from "../lib/speech";

type SR = SpeechRecognition & { continuous?: boolean };

function getSpeechRecognition(): (new () => SR) | null {
  const w = window as unknown as {
    SpeechRecognition?: new () => SR;
    webkitSpeechRecognition?: new () => SR;
  };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

interface Options {
  connected: boolean;
  thinking: boolean;
  onTranscript: (text: string) => void;
  onEnableVoice: () => void;
}

export function useLiveTalk({ connected, thinking, onTranscript, onEnableVoice }: Options) {
  const [liveTalk, setLiveTalk] = useState(false);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const recRef = useRef<SR | null>(null);
  const liveRef = useRef(false);
  const busyRef = useRef(false);

  const stopListen = useCallback(() => {
    try {
      recRef.current?.stop();
    } catch {
      /* ignore */
    }
    setListening(false);
  }, []);

  const startListen = useCallback(() => {
    const SRClass = getSpeechRecognition();
    if (!SRClass || !liveRef.current || busyRef.current) return;

    stopListen();
    const rec = new SRClass();
    rec.lang = "bn-BD";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.continuous = false;
    recRef.current = rec;

    rec.onstart = () => setListening(true);
    rec.onend = () => {
      setListening(false);
      if (liveRef.current && !busyRef.current) {
        setTimeout(() => startListen(), 400);
      }
    };
    rec.onerror = (ev: Event & { error?: string }) => {
      setListening(false);
      if (ev.error === "not-allowed") {
        liveRef.current = false;
        setLiveTalk(false);
      }
    };
    rec.onresult = (ev: { results: { [i: number]: { [j: number]: { transcript: string } } } }) => {
      const text = ev.results[0][0].transcript.trim();
      if (text.length > 1) {
        busyRef.current = true;
        stopListen();
        onTranscript(text);
      }
    };

    try {
      rec.start();
    } catch {
      setListening(false);
    }
  }, [onTranscript, stopListen]);

  const speakAndContinue = useCallback(
    async (text: string) => {
      busyRef.current = true;
      stopListen();
      setSpeaking(true);
      await speakText(text);
      setSpeaking(false);
      busyRef.current = false;
      if (liveRef.current && !thinking) {
        startListen();
      }
    },
    [startListen, stopListen, thinking]
  );

  const startLiveTalk = useCallback(async () => {
    onEnableVoice();
    liveRef.current = true;
    setLiveTalk(true);
    busyRef.current = true;
    await speakText("Assalamualaikum. Ami SENZ. Bolun, ki korbo apnar jonno?");
    busyRef.current = false;
    startListen();
  }, [onEnableVoice, startListen]);

  const stopLiveTalk = useCallback(() => {
    liveRef.current = false;
    setLiveTalk(false);
    busyRef.current = false;
    stopListen();
    stopSpeaking();
  }, [stopListen]);

  useEffect(() => {
    if (!connected && liveTalk) stopLiveTalk();
  }, [connected, liveTalk, stopLiveTalk]);

  const onResponseDone = useCallback(
    (spoken: string) => {
      if (!liveRef.current) return;
      void speakAndContinue(spoken || "Thik ache.");
    },
    [speakAndContinue]
  );

  return {
    liveTalk,
    listening,
    speaking,
    startLiveTalk,
    stopLiveTalk,
    onResponseDone,
    speakAndContinue,
  };
}
