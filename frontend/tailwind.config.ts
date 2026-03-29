import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#005bbf",
        "primary-container": "#1a73e8",
        "primary-fixed": "#d8e2ff",
        secondary: "#1b6d24",
        "secondary-container": "#a0f399",
        tertiary: "#006875",
        surface: "#f8f9fa",
        "surface-container-low": "#f3f4f5",
        "surface-container-lowest": "#ffffff",
        "surface-container-high": "#e7e8e9",
        "surface-container": "#edeeef",
        "on-surface": "#191c1d",
        "on-surface-variant": "#414754",
        outline: "#727785",
        "outline-variant": "#c1c6d6",
        error: "#ba1a1a",
        "error-container": "#ffdad6",
      },
      fontFamily: {
        headline: ["Manrope", "sans-serif"],
        body: ["Inter", "sans-serif"],
        label: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
