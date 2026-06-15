/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Required for @apply border-border in globals.css
        border: "rgba(148, 163, 184, 0.18)", // Silver/slate border
        input:  "rgba(148, 163, 184, 0.18)",
        ring:   "#22d3ee", // Cyan ring
        // Sherlock AI accent — professional mission-control cyan
        steel: {
          50:  "#ecfeff",
          100: "#cffafe",
          200: "#a5f3fc",
          300: "#67e8f9",
          400: "#22d3ee",
          500: "#06b6d4",
          600: "#0891b2",
          700: "#0e7490",
          800: "#155e75",
          900: "#164e63",
          950: "#083344",
        },
        forge: {
          50:  "#fff7ed",
          100: "#ffedd5",
          200: "#fed7aa",
          300: "#fdba74",
          400: "#fb923c",
          500: "#f97316",
          600: "#ea580c",
          700: "#c2410c",
          800: "#9a3412",
          900: "#7c2d12",
        },
        // Professional deep slate-navy surfaces
        surface: {
          DEFAULT: "#0a0f1c", // Deep slate-navy base
          50:  "#162033",
          100: "#111a2b",
          200: "#0d1424",
          300: "#0a0f1c",
          400: "#070b15",
        },
        card: {
          DEFAULT: "#0f1626",
          hover:   "#151d30",
          border:  "rgba(148, 197, 255, 0.16)", // Cool subtle border
        },
        muted: {
          DEFAULT: "#6b7280",
          foreground: "#9ca3af",
        },
        accent: {
          blue:   "#3b82f6",
          green:  "#10b981",
          amber:  "#f59e0b",
          red:    "#ef4444",
          purple: "#6366f1",
          cyan:   "#06b6d4",
        },
      },
      fontFamily: {
        sans:  ["Inter", "system-ui", "sans-serif"],
        mono:  ["JetBrains Mono", "Fira Code", "monospace"],
        display: ["Inter", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "gradient-steel": "linear-gradient(135deg, #0e7490 0%, #0a0f1c 55%, #070b15 100%)",
        "gradient-card":  "linear-gradient(145deg, #111a2b 0%, #0d1424 100%)",
        "gradient-glow":  "radial-gradient(ellipse at top, #22d3ee20 0%, transparent 60%)",
      },
      animation: {
        "pulse-slow":  "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-up":    "slideUp 0.3s ease-out",
        "fade-in":     "fadeIn 0.4s ease-out",
        "glow":        "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        slideUp:  { from: { opacity: 0, transform: "translateY(10px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        fadeIn:   { from: { opacity: 0 }, to: { opacity: 1 } },
        glow:     { from: { boxShadow: "0 0 5px #9f123940" }, to: { boxShadow: "0 0 20px #9f123960" } },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
