import type { Config } from 'tailwindcss'

// The single source of truth for the design system. Components reference token
// names (bg-brand-500, text-ink-muted, bg-critical-soft, ...), never raw hex.
// Brand blue #3D79BB is extracted from the official Tata Steel logo SVG.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Brand blue scale, derived from #3D79BB.
        brand: {
          50: '#EFF4FA',
          100: '#DFE9F4',
          200: '#C1D4E9',
          300: '#93B3D6',
          400: '#6093C6',
          500: '#3D79BB',
          600: '#356AA3',
          700: '#2D5A8A',
          800: '#244870',
          900: '#1B3654',
        },
        // Surfaces and canvas.
        canvas: '#F7F9FB',
        surface: '#FFFFFF',
        // Hairline borders.
        hairline: '#EAEEF3',
        line: '#DCE2EA',
        // Slate text scale.
        ink: {
          DEFAULT: '#1D2939',
          heading: '#101828',
          secondary: '#475467',
          muted: '#667085',
          subtle: '#94A3B8',
        },
        // Semantic severity scale (solid / soft bg / fg text / ring border).
        critical: { DEFAULT: '#D92D20', soft: '#FEECEB', fg: '#B42318', ring: '#FDA29B' },
        high: { DEFAULT: '#F79009', soft: '#FEF3E7', fg: '#B54708', ring: '#FEC84B' },
        medium: { DEFAULT: '#3D79BB', soft: '#EFF4FA', fg: '#2D5A8A', ring: '#C1D4E9' },
        healthy: { DEFAULT: '#16A34A', soft: '#E9F6EF', fg: '#067647', ring: '#A6E0BE' },
        idle: { DEFAULT: '#667085', soft: '#F2F4F7', fg: '#475467', ring: '#DCE2EA' },
      },
      fontFamily: {
        sans: ['Helvetica Neue', 'Arial', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 2px 0 rgb(16 24 40 / 0.04), 0 1px 3px 0 rgb(16 24 40 / 0.06)',
        pop: '0 4px 12px -2px rgb(16 24 40 / 0.10), 0 2px 6px -2px rgb(16 24 40 / 0.06)',
      },
    },
  },
  plugins: [],
} satisfies Config
