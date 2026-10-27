/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#060A11",
          900: "#0B0F19",
          850: "#0F172A",
          800: "#141E33",
          700: "#1E293B",
          600: "#334155",
        },
        teal: {
          400: "#2DD4BF",
          500: "#14B8A6",
          600: "#0D9488",
        },
        emerald: {
          400: "#34D399",
          500: "#10B981",
          600: "#059669",
        },
        cyan: {
          400: "#22D3EE",
          500: "#06B6D4",
        },
        amber: {
          400: "#FBBF24",
          500: "#F59E0B",
          600: "#D97706",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
