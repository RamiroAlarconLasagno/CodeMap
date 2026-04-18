// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Cascadia Code', 'monospace'],
      },
      colors: {
        // Verde acento CodeMap
        accent: {
          DEFAULT: '#1D9E75',
          hover:   '#0F6E56',
          light:   '#E1F5EE',
          border:  '#5DCAA5',
        },
      },
      fontSize: {
        // Tamanios finos para UI densa de codigo
        '2xs': ['10px', { lineHeight: '14px' }],
        'xs':  ['11px', { lineHeight: '16px' }],
        'sm':  ['12px', { lineHeight: '18px' }],
      },
    },
  },
  plugins: [],
}