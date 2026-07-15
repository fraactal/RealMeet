/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#102a43",
          900: "#102a43",
          700: "#334e68",
          500: "#627d98",
        },
        brand: {
          DEFAULT: "#0b5563",
          700: "#0b5563",
          600: "#0f6b78",
          500: "#168694",
          100: "#d9f0f2",
          50: "#edfafa",
        },
        success: {
          700: "#17633a",
          100: "#daf5e6",
        },
        warning: {
          700: "#8a5a00",
          100: "#fff1cc",
        },
        danger: {
          700: "#9f2a2a",
          100: "#fde2e2",
        },
        info: {
          700: "#1e5b8f",
          100: "#dceeff",
        },
        surface: {
          page: "#f6f3ee",
          subtle: "#f8faf9",
          card: "#ffffff",
        },
        accent: "#17633a",
        mist: "#edfafa",
      },
      borderRadius: {
        sm: "0.375rem",
        md: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(16, 42, 67, 0.08)",
        lift: "0 18px 45px rgba(16, 42, 67, 0.12)",
      },
    },
  },
  plugins: [],
};
