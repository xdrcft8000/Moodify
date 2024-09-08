interface ThemeColors {
    primary: string;
    secondary: string;
    violet: string;
    brown: string;
    white: string;
    black: string;
  }
  
  interface ThemeConfig {
    light: ThemeColors;
    dark: ThemeColors;
  }
  export const themeColors: ThemeConfig = {
    light: {
      primary: '#D9D9D9',  // Light gray
      secondary: '#000000', // Black
      violet: '#3E06E0', // Lightening violet blue
      brown: '#403732', // Muted humble brown
      white: '#FFFFFF',
      black: '#000000',
    },
    dark: {
      primary: '#1E1E1E',  // Dark gray
      secondary: '#FFFFFF', // White
      violet: '#3E06E0', // Lightening violet blue
      brown: '#403732', // Muted humble brown
      white: '#FFFFFF',
      black: '#000000',
    }
  };