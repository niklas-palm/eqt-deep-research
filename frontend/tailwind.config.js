/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // EQT branding colors
        eqt: {
          primary: "#FF4716", // EQT orange (more accurate based on website)
          dark: "#0C0D0C",    // Dark gray/near black
          light: "#FFFFFF",   // White background
          secondary: "#FF7A56", // Lighter orange for hover
          accent: "#E82F00",  // Darker orange for active states
          blue: "#253746",    // EQT blue (used for some headings)
          orange: {
            50: "#FFF5F2",    // Background tint
            100: "#FFE8E2",   // Light background
            200: "#FFD1C4",   // Borders
            600: "#FF4716",   // Primary orange
            700: "#E82F00"    // Darker orange
          },
          gray: {
            50: "#FAFAFA",
            100: "#F5F5F5",
            200: "#EEEEEE",
            300: "#E0E0E0",
            400: "#C4C4C4", 
            500: "#888888",
            600: "#6E6E6E",
            700: "#4D4D4D",
            800: "#282828",
            900: "#121212"
          }
        }
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      typography: {
        DEFAULT: {
          css: {
            a: {
              color: "#7c4dff",
              "&:hover": {
                color: "#6a3df3",
              },
            },
            code: {
              color: "#7c4dff",
              backgroundColor: "#f5f5f8",
              padding: "0.2em 0.4em",
              borderRadius: "0.25rem",
            },
          },
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate"), require("@tailwindcss/typography")],
}