import { useEffect, useRef, useState } from "react";
import { useSenzSocket } from "./hooks/useSenzSocket";
import { useLiveTalk } from "./hooks/useLiveTalk";
import { VisualHub } from "./components/VisualHub";

function Panel({ title, children, className = "" }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`panel flex flex-col min-h-0 ${className}`}>
      <div className="panel-title">{title}</div>
      <div className="flex-1 overflow-auto p-2 min-h-0">{children}</div>
    </div>
  );
}

export default function App() {
  const {
    connected,
    thinking,
    messages,
    toolLogs,
    headlines,
    diagram,
    subAgents,
    active,
    chat,
    sendVoiceText,
    enableVoice,
    registerResponseHandler,
    terminate,
    clearChat,
    brainMode,
  } = useSenzSocket();

  const live = useLiveTalk({
    connected,
    thinking,
    onTranscript: sendVoiceText,
    onEnableVoice: enableVoice,
  });

  const liveTalkRef = useRef(false);
  liveTalkRef.current = live.liveTalk;

  const onResponseDoneRef = useRef(live.onResponseDone);
  onResponseDoneRef.current = live.onResponseDone;

  useEffect(() => {
    registerResponseHandler((_reply, spoken) => {
      if (liveTalkRef.current && spoken) {
        onResponseDoneRef.current(spoken);
      }
    });
    return () => registerResponseHandler(null);
  }, [registerResponseHandler]);

  const [input, setInput] = useState("");
  const [tab, setTab] = useState<"chats" | "logs" | "notes" | "tasks">("chats");
  const chatEnd = useRef<HTMLDivElement>(null);

  const statusLabel = live.speaking
    ? "SENZ BOLCHE..."
    : live.listening
      ? "APNI BOLUN..."
      : thinking
        ? "BIABCHONA..."
        : live.liveTalk
          ? "LIVE TALK ON"
          : "SYSTEM ACTIVE";

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    chat(input.trim());
    setInput("");
  };

  return (
    <div className="h-screen w-screen grid grid-rows-[auto_1fr] bg-[radial-gradient(ellipse_at_top,#0a1a2e_0%,#050a12_70%)] p-2 gap-2">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-1 border-b border-senz-border/40">
        <h1 className="font-display text-2xl font-bold tracking-[0.35em] text-senz-cyan glow-text">SENZ</h1>
        <div className="flex items-center gap-4 text-[10px] uppercase tracking-widest text-senz-muted">
          <span className={connected ? "text-senz-green" : "text-senz-red"}>
            {connected ? "● Link Online" : "○ Backend Offline"}
          </span>
          <span>{active ? "SYSTEM ACTIVE" : "STANDBY"}</span>
          <span className="text-senz-cyan/80 normal-case tracking-normal">{brainMode}</span>
        </div>
      </header>

      <div className="grid grid-cols-12 grid-rows-6 gap-2 min-h-0">
        {/* Left column */}
        <div className="col-span-2 row-span-6 flex flex-col gap-2">
          <Panel title="Media Link">
            <div className="text-[10px] text-senz-muted space-y-2">
              <div className="flex gap-2">
                <span className="px-2 py-1 border border-senz-border rounded">📷</span>
                <span className="px-2 py-1 border border-senz-border rounded">🎤</span>
              </div>
              <p
                className={
                  live.listening
                    ? "text-senz-green animate-pulse font-bold"
                    : live.speaking
                      ? "text-senz-cyan animate-pulse"
                      : live.liveTalk
                        ? "text-senz-green"
                        : "text-senz-red"
                }
              >
                {live.listening
                  ? "🎤 SHUNCHI — bolen"
                  : live.speaking
                    ? "🔊 SENZ bolche"
                    : live.liveTalk
                      ? "LIVE — kotha bolun"
                      : "LIVE TALK off"}
              </p>
            </div>
          </Panel>
          <Panel title="Sat-Link Feed" className="flex-[2]">
            <div className="h-full flex flex-col items-center justify-center text-senz-muted text-[10px] gap-2">
              <div className="w-20 h-20 rounded-full border border-senz-cyan/40 shadow-glow flex items-center justify-center text-2xl">
                🌐
              </div>
              <span>Global Data Stream</span>
              <span className="text-senz-cyan/60">Phase 2 — live feeds</span>
            </div>
          </Panel>
          <Panel title="Today Headlines" className="flex-1">
            <ul className="text-[10px] space-y-2">
              {headlines.length ? (
                headlines.map((h, i) => (
                  <li key={i} className="border-l-2 border-senz-green pl-2">
                    <span className="text-senz-green">{h.source}</span>
                    <p className="text-white/90 mt-0.5">{h.title}</p>
                  </li>
                ))
              ) : (
                <li className="text-senz-muted">Ask: &quot;ajker news dao&quot;</li>
              )}
            </ul>
          </Panel>
        </div>

        {/* Center */}
        <div className="col-span-5 row-span-6 flex flex-col gap-2">
          <div className="grid grid-cols-4 gap-2 h-24">
            {[
              { label: "Memory", color: "text-senz-green border-senz-green/50" },
              { label: "Soul", color: "text-white border-white/30" },
              { label: "Skills", color: "text-senz-cyan border-senz-cyan/50" },
              { label: "Settings", color: "text-senz-red border-senz-red/50" },
            ].map((m) => (
              <button
                key={m.label}
                className={`panel text-xs font-display tracking-wider ${m.color} hover:shadow-glow transition`}
              >
                {m.label}
              </button>
            ))}
          </div>

          <div className="panel flex-1 flex flex-col items-center justify-center relative overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,229,255,0.08)_0%,transparent_60%)]" />
            <div className="sphere-pulse w-40 h-40 rounded-full border border-senz-cyan/30 shadow-glow flex items-center justify-center relative">
              <div className="w-32 h-32 rounded-full bg-gradient-to-br from-senz-cyan/20 to-transparent border border-senz-cyan/20" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-2 h-2 bg-senz-cyan rounded-full shadow-glow animate-ping" />
              </div>
            </div>
            <p className="mt-4 font-display text-sm tracking-[0.25em] text-senz-cyan glow-text text-center px-4">
              {statusLabel}
            </p>
            <div className="flex flex-col items-center gap-3 mt-4">
              {!live.liveTalk ? (
                <button
                  type="button"
                  onClick={() => void live.startLiveTalk()}
                  disabled={!connected}
                  className="px-8 py-3 bg-senz-green/20 border-2 border-senz-green text-senz-green font-display text-xs tracking-[0.2em] hover:shadow-glow-green disabled:opacity-40"
                >
                  LIVE TALK
                </button>
              ) : (
                <button
                  type="button"
                  onClick={live.stopLiveTalk}
                  className="px-8 py-3 bg-senz-cyan/20 border-2 border-senz-cyan text-senz-cyan font-display text-xs tracking-[0.2em]"
                >
                  STOP TALK
                </button>
              )}
              <p className="text-[9px] text-senz-muted text-center max-w-xs">
                LIVE TALK = SENZ shune + jawab debe (speaker on rakhben)
              </p>
              <button
                onClick={terminate}
                className="px-6 py-2 bg-senz-red/20 border border-senz-red text-senz-red text-[10px] uppercase tracking-widest"
              >
                Terminate
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 h-44 min-h-0">
            <VisualHub diagram={diagram} />
            <Panel title="Sub-Agents">
              <div className="text-[10px]">
                <p className="text-senz-cyan mb-2">{subAgents.filter((s) => s.status === "running").length} active</p>
                {subAgents.length ? (
                  subAgents.map((s) => (
                    <div key={s.id} className="mb-2 p-2 border border-senz-border/40 rounded">
                      <div className="flex justify-between">
                        <span className="text-senz-green">{s.label}</span>
                        <span className={s.status === "done" ? "text-senz-green" : "text-senz-cyan"}>{s.status}</span>
                      </div>
                      <p className="text-senz-muted mt-1 truncate">{s.task}</p>
                      {s.progress && <p className="text-senz-cyan/70">{s.progress}</p>}
                    </div>
                  ))
                ) : (
                  <p className="text-senz-muted">Delegate: &quot;daraz e trending khujo background e&quot;</p>
                )}
              </div>
            </Panel>
          </div>
        </div>

        {/* Right — Chat */}
        <div className="col-span-5 row-span-6 flex flex-col gap-2 min-h-0">
          <div className="panel flex-1 flex flex-col min-h-0">
            <div className="flex border-b border-senz-border/40 text-[10px] uppercase tracking-widest items-center">
              {(["chats", "logs", "notes", "tasks"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`flex-1 py-2 ${tab === t ? "text-senz-cyan border-b-2 border-senz-cyan" : "text-senz-muted"}`}
                >
                  {t}
                </button>
              ))}
              {tab === "chats" && (
                <button
                  type="button"
                  onClick={clearChat}
                  className="px-2 py-1 mr-2 text-senz-muted hover:text-senz-red text-[9px]"
                  title="Purono error messages muche felbe"
                >
                  Clear
                </button>
              )}
            </div>

            <div className="flex-1 overflow-auto p-3 text-[11px] leading-relaxed min-h-0">
              {tab === "chats" && (
                <>
                  {messages.length === 0 && (
                    <p className="text-senz-muted">
                      Assalamualaikum — ami <span className="text-senz-cyan">SENZ</span>. Bolun ki korbo?
                      <br />
                      <br />
                      LIVE TALK chapun → bolen &quot;chrome kholo&quot; / &quot;kemon acho&quot;
                    </p>
                  )}
                  {messages.map((m, i) => (
                    <div
                      key={i}
                      className={`mb-3 ${m.role === "user" ? "text-senz-cyan" : m.role === "system" ? "text-senz-green" : "text-white/85"}`}
                    >
                      <span className="text-[9px] uppercase text-senz-muted mr-2">{m.role}</span>
                      <span className="whitespace-pre-wrap">{m.content}</span>
                    </div>
                  ))}
                  {thinking && <p className="text-senz-cyan animate-pulse">SENZ thinking...</p>}
                  <div ref={chatEnd} />
                </>
              )}
              {tab === "logs" && (
                <ul className="space-y-1 font-mono text-[10px]">
                  {toolLogs.map((t, i) => (
                    <li key={i} className="flex justify-between border-b border-senz-border/20 py-1">
                      <span className="text-senz-green">{t.name}</span>
                      <span className="text-senz-muted">{t.duration_ms}ms</span>
                    </li>
                  ))}
                  {!toolLogs.length && <li className="text-senz-muted">Module logs appear here</li>}
                </ul>
              )}
              {tab === "notes" && <p className="text-senz-muted">Say: &quot;note save koro: ...&quot;</p>}
              {tab === "tasks" && (
                <ul className="space-y-2">
                  {subAgents.map((s) => (
                    <li key={s.id} className="border-l-2 border-senz-cyan pl-2">
                      [{s.status}] {s.label}: {s.task.slice(0, 80)}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <form onSubmit={submit} className="p-2 border-t border-senz-border/40 flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type instruction..."
                className="flex-1 bg-black/40 border border-senz-border rounded px-3 py-2 text-xs focus:outline-none focus:border-senz-cyan"
                disabled={!connected}
              />
              <button
                type="submit"
                disabled={!connected || thinking}
                className="px-4 py-2 bg-senz-cyan/20 border border-senz-cyan text-senz-cyan text-xs uppercase disabled:opacity-40"
              >
                Send
              </button>
            </form>
            <p className="text-[9px] text-center text-senz-muted pb-2">
              {connected ? "● Live Session Ready" : "Start backend: npm run backend"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
