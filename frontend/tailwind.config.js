/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gov: {
          dark: '#0A192F',       // Deep Navy for dark background
          navy: '#0F2942',       // Classic APCFSS Navy (Primary)
          blue: '#1E40AF',       // Royal Blue (Buttons & Focus)
          light: '#F8FAFC',      // Slate background
          border: '#E2E8F0',     // Soft borders
          accent: '#0056B3',     // secondary
          gold: '#B45309',       // warning / premium text
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)',
        premium: '0 4px 6px -1px rgba(15, 41, 66, 0.05), 0 2px 4px -1px rgba(15, 41, 66, 0.03)',
      }
    },
  },
  plugins: [],
}
