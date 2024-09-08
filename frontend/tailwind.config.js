/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  darkMode: 'class', // Add this line
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#D9D9D9', // Light gray
          dark: '#1E1E1E'   // Dark gray
        },
        secondary: {
          DEFAULT: '#000000', // Black
          dark: '#FFFFFF'   // White
        },
        violet: '#3E06E0', // Lightening violet blue (same for both modes)
        brown: '#403732',  // Muted humble brown (same for both modes)
        white: '#FFFFFF',
        black: '#000000'
      },
      textColor: {
        DEFAULT: '#000000', // This sets the default text color to black
      },
    },
    fontFamily: {
      'sans': ['Helvetica Neue', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Arial', 'Noto Sans', 'sans-serif', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji'],
      'serif': ['Inria Serif', 'ui-serif', 'Georgia', 'Cambria', 'Times New Roman', 'Times', 'serif'],
      'mono': ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      'hangang': ['Seoul Hangang', 'sans-serif'],
    },
  },
  plugins: [],
}