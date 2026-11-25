import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#D71920",
          dark: "#B5121B",
          tint: "#FEF2F2",
        },
        surface: {
          white: "#FFFFFF",
          bg: "#F8F8F8",
          muted: "#F3F4F6",
        },
        ink: {
          primary: "#222222",
          secondary: "#6B7280",
        },
        line: {
          DEFAULT: "#E5E7EB",
        },
        status: {
          success: "#16A34A",
          warning: "#F59E0B",
          error: "#DC2626",
        },
      },
      fontFamily: {
        sans: ["Poppins", "system-ui", "-apple-system", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 3px rgba(16, 24, 40, 0.06), 0 1px 2px rgba(16, 24, 40, 0.04)",
        "card-hover": "0 4px 12px rgba(16, 24, 40, 0.08)",
        dropdown: "0 10px 24px rgba(16, 24, 40, 0.10)",
        modal: "0 20px 40px rgba(16, 24, 40, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;
