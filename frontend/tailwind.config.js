/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563EB',
        'primary-dark': '#1D4ED8',
        'primary-light': '#DBEAFE',
        surface: '#FFFFFF',
        background: '#F8FAFC',
        border: '#E2E8F0',
        text: '#1E293B',
        'text-muted': '#64748B',
        success: '#16A34A',
        'success-light': '#DCFCE7',
        warning: '#D97706',
        'warning-light': '#FEF3C7',
        danger: '#DC2626',
        'danger-light': '#FEE2E2',
        sidebar: '#FFFFFF',
      },
      fontFamily: {
        sans: ['Inter', 'Hind Siliguri', 'system-ui', 'sans-serif'],
        bangla: ['Hind Siliguri', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px -1px rgba(0,0,0,0.1)',
        sidebar: '1px 0 0 0 #E2E8F0',
      },
    },
  },
  plugins: [],
}
