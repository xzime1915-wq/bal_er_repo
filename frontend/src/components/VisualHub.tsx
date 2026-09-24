import { useEffect, useRef } from "react";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  themeVariables: {
    primaryColor: "#0a2840",
    primaryTextColor: "#00e5ff",
    lineColor: "#00ff88",
    fontFamily: "JetBrains Mono",
  },
});

export function VisualHub({ diagram }: { diagram: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const id = `mermaid-${Date.now()}`;
    mermaid
      .render(id, diagram)
      .then(({ svg }) => {
        if (ref.current) ref.current.innerHTML = svg;
      })
      .catch(() => {
        if (ref.current) ref.current.textContent = diagram;
      });
  }, [diagram]);

  return (
    <div className="panel h-full flex flex-col min-h-0">
      <div className="panel-title">Visual Hub</div>
      <div ref={ref} className="flex-1 overflow-auto p-2 text-xs flex items-center justify-center [&_svg]:max-w-full" />
    </div>
  );
}
