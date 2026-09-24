/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        senz: {
          bg: "#050a12",
          panel: "#0a1424",
          border: "#1a3a5c",
          cyan: "#00e5ff",
          green: "#00ff88",
          red: "#ff3355",
          muted: "#6b8cae",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Consolas", "monospace"],
        display: ["Orbitron", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(0, 229, 255, 0.35)",
        "glow-green": "0 0 16px rgba(0, 255, 136, 0.4)",
      },
    },
  },
  plugins: [],
};
