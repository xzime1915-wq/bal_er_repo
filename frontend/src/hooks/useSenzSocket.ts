import { useCallback, useEffect, useRef, useState } from "react";
import { speakText } from "../lib/speech";

const WS_URL = "ws://127.0.0.1:8765/ws";
const API_URL = "http://127.0.0.1:8765/api";
const THINKING_TIMEOUT_MS = 35000;

export interface ToolLog {
  name: string;
  duration_ms: number;
  status: string;
}

export interface SubAgent {
  id: string;
  label: string;
  task: string;
  status: string;
  progress: string;
  result: string;
}

export interface Headline {
  title: string;
  source: string;
}

export function useSenzSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const thinkingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onResponseRef = useRef<((reply: string, speakText?: string) => void) | null>(null);
  const greetedRef = useRef(false);
  const autoSpeakRef = useRef(false);

  const [connected, setConnected] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [toolLogs, setToolLogs] = useState<ToolLog[]>([]);
  const [headlines, setHeadlines] = useState<Headline[]>([]);
  const [diagram, setDiagram] = useState("flowchart LR\n  User --> SENZ\n  SENZ --> PC");
  const [subAgents, setSubAgents] = useState<SubAgent[]>([]);
  const [active, setActive] = useState(true);
  const [voiceOn, setVoiceOn] = useState(false);
  const [voiceListening, setVoiceListening] = useState(false);
  const [brainMode, setBrainMode] = useState("Brain: ...");

  const stopThinkingTimer = () => {
    if (thinkingTimer.current) {
      clearTimeout(thinkingTimer.current);
      thinkingTimer.current = null;
    }
  };

  const startThinkingTimer = () => {
    stopThinkingTimer();
    thinkingTimer.current = setTimeout(() => {
      setThinking(false);
      setMessages((m) => [
        ...m,
        { role: "system", content: "Timeout — abar try korun: chrome kholo" },
      ]);
    }, THINKING_TIMEOUT_MS);
  };

  const refreshHealth = useCallback(async () => {
    try {
      const r = await fetch(`${API_URL}/health`);
      const h = await r.json();
      if (h.ollama_online) setBrainMode(`Brain: Ollama (${h.ollama_model})`);
      else if (h.gemini_configured) setBrainMode("Brain: Local + Gemini (quota limited)");
      else setBrainMode("Brain: Local commands");
    } catch {
      setBrainMode("Brain: offline");
    }
  }, []);

  const loadState = useCallback(async () => {
    refreshHealth();
    try {
      const r = await fetch(`${API_URL}/state`);
      const data = await r.json();
      setHeadlines(data.headlines || []);
      if (data.diagram) setDiagram(data.diagram);
      setSubAgents(data.sub_agents || []);
      setActive(data.active !== false);
      if (data.chat?.length) {
        setMessages(
          data.chat.map((c: { role: string; content: string }) => ({
            role: c.role,
            content: c.content,
          }))
        );
      }
    } catch {
      /* backend not up */
    }
  }, [refreshHealth]);

  useEffect(() => {
    loadState();
    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;
      ws.onopen = () => {
        setConnected(true);
        if (!greetedRef.current) {
          greetedRef.current = true;
          const welcome =
            "Assalamualaikum! Ami SENZ — apnar PC assistant. LIVE TALK chapun, ba likhe bolun ki korbo.";
          setMessages((m) =>
            m.length ? m : [{ role: "assistant", content: welcome }]
          );
        }
      };
      ws.onclose = () => {
        setConnected(false);
        setThinking(false);
        stopThinkingTimer();
        setTimeout(connect, 3000);
      };
      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.type === "thinking") {
          setThinking(true);
          startThinkingTimer();
        }
        if (msg.type === "response") {
          stopThinkingTimer();
          setThinking(false);
          setVoiceListening(false);
          const reply = msg.reply as string;
          const spoken = (msg.speak_text as string) || reply;
          setMessages((m) => [...m, { role: "assistant", content: reply }]);
          setToolLogs(msg.tools || []);
          if (msg.headlines?.length) setHeadlines(msg.headlines);
          if (msg.diagram) setDiagram(msg.diagram);
          if (msg.sub_agents) setSubAgents(msg.sub_agents);
          onResponseRef.current?.(reply, spoken);
          if (autoSpeakRef.current && !onResponseRef.current) {
            void speakText(spoken);
          }
        }
        if (msg.type === "voice_on") setVoiceOn(true);
        if (msg.type === "voice_off") setVoiceOn(false);
        if (msg.type === "voice_listening") setVoiceListening(true);
        if (msg.type === "voice_heard") {
          setVoiceListening(false);
          setMessages((m) => [...m, { role: "user", content: msg.text }]);
        }
        if (msg.type === "voice_error") {
          setVoiceListening(false);
          setThinking(false);
          stopThinkingTimer();
          setMessages((m) => [...m, { role: "system", content: msg.message }]);
        }
        if (msg.type === "terminated") setActive(false);
        if (msg.type === "chat_cleared") setMessages([]);
      };
    };
    connect();
    return () => {
      stopThinkingTimer();
      wsRef.current?.close();
    };
  }, [loadState]);

  const send = useCallback((payload: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
      return true;
    }
    setMessages((m) => [...m, { role: "system", content: "Backend offline — start.bat chalan" }]);
    return false;
  }, []);

  const chat = useCallback(
    (text: string) => {
      setMessages((m) => [...m, { role: "user", content: text }]);
      send({ type: "chat", text });
    },
    [send]
  );

  const sendVoiceText = useCallback(
    (text: string) => {
      setMessages((m) => [...m, { role: "user", content: text }]);
      send({ type: "chat", text });
    },
    [send]
  );

  const enableVoice = useCallback(() => {
    autoSpeakRef.current = true;
    send({ type: "voice_enable" });
    setVoiceOn(true);
  }, [send]);

  const registerResponseHandler = useCallback(
    (fn: ((reply: string, speakText?: string) => void) | null) => {
      onResponseRef.current = fn;
    },
    []
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    send({ type: "clear_chat" });
  }, [send]);

  const terminate = useCallback(() => send({ type: "terminate" }), [send]);

  return {
    connected,
    thinking,
    messages,
    toolLogs,
    headlines,
    diagram,
    subAgents,
    active,
    voiceOn,
    voiceListening,
    chat,
    sendVoiceText,
    enableVoice,
    registerResponseHandler,
    terminate,
    clearChat,
    brainMode,
  };
}
