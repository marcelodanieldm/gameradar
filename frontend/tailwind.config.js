/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme colors
        dark: {
          bg: {
            primary: '#0a0a0a',
            secondary: '#141414',
            tertiary: '#1a1a1a',
            hover: '#252525',
          },
          text: {
            primary: '#ffffff',
            secondary: '#a3a3a3',
            tertiary: '#737373',
          },
          border: {
            primary: '#262626',
            secondary: '#333333',
          },
          accent: {
            primary: '#3b82f6',
            secondary: '#8b5cf6',
            success: '#10b981',
            warning: '#f59e0b',
            danger: '#ef4444',
          }
        },
        // Region-specific accent colors
        region: {
          korea: '#FF6B6B',
          china: '#FFC759',
          india: '#FF9933',
          vietnam: '#DA251D',
          thailand: '#0033A0',
          japan: '#BC002D',
        }
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
        // Region-specific fonts
        korean: ['Noto Sans KR', 'sans-serif'],
        chinese: ['Noto Sans SC', 'sans-serif'],
        hindi: ['Noto Sans Devanagari', 'sans-serif'],
        vietnamese: ['Noto Sans', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      gridTemplateColumns: {
        '15': 'repeat(15, minmax(0, 1fr))',
      }
    },
  },
  plugins: [],
}
