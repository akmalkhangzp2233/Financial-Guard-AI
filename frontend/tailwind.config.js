/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ivory: "#F6F5FB",
        ink: "#211B26",
        indigo: { DEFAULT: "#5B4FE8", light: "#7B70F0" },
        coral: "#FF7A59",
        alert: "#E5484D",
        line: "#E5E1F0",
      },
      fontFamily: {
        display: ["Sora", "sans-serif"],
        body: ["Manrope", "sans-serif"],
        mono: ["Space Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
