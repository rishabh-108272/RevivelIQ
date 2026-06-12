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
        // Microsoft Fluent-inspired colors
        microsoft: {
          blue: '#0078d4',       // Primary Cobalt Blue
          darkBlue: '#005a9e',
          lightBlue: '#eff6fc',
          gray: '#f3f2f1',       // Neutral light gray
          charcoal: '#201f1e',   // Dark mode gray
          darkCharcoal: '#11100f',
          white: '#ffffff',
          border: '#edebe9'
        },
        risk: {
          high: '#e81123',       // Attention red
          medium: '#ff8c00',     // Warning orange
          low: '#107c41',        // Success green
        }
      },
      fontFamily: {
        sans: ['Segoe UI', 'Segoe UI Web (West European)', '-apple-system', 'BlinkMacSystemFont', 'Roboto', 'Helvetica Neue', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
