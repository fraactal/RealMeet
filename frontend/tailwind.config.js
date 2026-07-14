/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        brand: "#0f4c5c",
        accent: "#198754",
        mist: "#ecf5f7",
      },
    },
  },
  plugins: [],
};
