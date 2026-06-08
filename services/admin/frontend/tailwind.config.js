/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        ocean: {
          900: '#0a1628',
          800: '#0f1932',
          700: '#1a2744',
          600: '#263b5e',
        }
      }
    }
  },
  plugins: [],
}
