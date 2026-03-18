import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        renfe: {
          red: '#d1205c',
          redHover: '#a03078',
          purple: '#4a2b7f',
          plum: '#6d2d82',
        },
      },
      backgroundImage: {
        renfeHeader:
          'linear-gradient(90deg, #d1205c 0%, #a03078 35%, #6d2d82 65%, #4a2b7f 100%)',
      },
    },
  },
  plugins: [],
} satisfies Config

