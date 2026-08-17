/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0e14",
        surface: "#121722",
        "surface-raised": "#1a2130",
        border: "#242d40",
        "border-muted": "#1b2230",
        primary: {
          DEFAULT: "#2563eb",
          hover: "#1d4ed8",
          muted: "rgba(37, 99, 235, 0.15)",
        },
        success: {
          DEFAULT: "#10b981",
          muted: "rgba(16, 185, 129, 0.15)",
        },
        danger: {
          DEFAULT: "#ef4444",
          hover: "#dc2626",
          muted: "rgba(239, 68, 68, 0.15)",
        },
        warning: {
          DEFAULT: "#f59e0b",
          muted: "rgba(245, 158, 11, 0.15)",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
}
