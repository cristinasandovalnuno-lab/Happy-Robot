/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          50: '#ffffff',
          100: '#f8f9fb',
          200: '#f1f3f7',
          300: '#e5e8ee',
          400: '#d1d5de',
          500: '#9ca3b4',
          600: '#6b7280',
          700: '#4b5563',
          800: '#1f2937',
          900: '#111827',
        },
        brand: {
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
        },
        accent: {
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#f43f5e',
          sky: '#0ea5e9',
          violet: '#8b5cf6',
          teal: '#14b8a6',
        },
      },
      fontFamily: {
        display: ['Outfit', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)',
        'card-hover': '0 4px 12px 0 rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.04)',
        glow: '0 0 20px -5px rgb(99 102 241 / 0.15)',
      },
    },
  },
  plugins: [],
}