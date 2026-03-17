/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        buy:     '#22c55e',
        sell:    '#ef4444',
        neutral: '#f59e0b',
        card:    '#1e2a3b',
        surface: '#0f1923',
        border:  '#263548',
      },
    },
  },
  plugins: [],
}
