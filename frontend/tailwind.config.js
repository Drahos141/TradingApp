/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        buy:        '#22c55e',
        sell:       '#ef4444',
        neutral:    '#f59e0b',
        // Sci-fi dark theme
        card:       '#0d1b2a',
        surface:    '#060d14',
        border:     '#0e2a3f',
        'neon-green':  '#00ff88',
        'neon-cyan':   '#00e5ff',
        'neon-purple': '#bf00ff',
        'cyber-blue':  '#0066ff',
      },
      boxShadow: {
        'neon-green':  '0 0 8px #00ff88, 0 0 20px rgba(0,255,136,0.3)',
        'neon-cyan':   '0 0 8px #00e5ff, 0 0 20px rgba(0,229,255,0.3)',
        'neon-purple': '0 0 8px #bf00ff, 0 0 20px rgba(191,0,255,0.3)',
        'neon-red':    '0 0 8px #ef4444, 0 0 20px rgba(239,68,68,0.3)',
        'cyber':       'inset 0 0 30px rgba(0,229,255,0.03), 0 0 0 1px rgba(0,229,255,0.1)',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', '"Cascadia Code"', 'Consolas', 'monospace'],
      },
      animation: {
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'scan': 'scan 4s linear infinite',
        'flicker': 'flicker 3s ease-in-out infinite',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
        'scan': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        'flicker': {
          '0%, 95%, 100%': { opacity: '1' },
          '96%': { opacity: '0.8' },
          '97%': { opacity: '1' },
          '98%': { opacity: '0.6' },
          '99%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

