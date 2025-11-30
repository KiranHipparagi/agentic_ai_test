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
        pwc: {
          orange: "#D04A02",
          darkOrange: "#A83C02",
          gray: "#53565A",
          lightGray: "#E6E6E6",
          darkGray: "#2C2C2C",
        },
      },
    },
  },
  plugins: [],
};
export default config;
