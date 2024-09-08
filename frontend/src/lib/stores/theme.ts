import { writable } from 'svelte/store';
import { browser } from '$app/environment';

type ThemeType = 'light' | 'dark';

// Check if there's a saved theme preference in localStorage
const storedTheme = browser ? localStorage.getItem('theme') as ThemeType : null;
export const theme = writable<ThemeType>(storedTheme || 'light');

// Update localStorage and apply class when the theme changes
theme.subscribe((value) => {
  if (browser) {
    localStorage.setItem('theme', value);
    if (value === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }
});

export function toggleTheme(): void {
  theme.update(t => t === 'light' ? 'dark' : 'light');
}