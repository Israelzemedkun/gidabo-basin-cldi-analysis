import React, { createContext, useContext, useState, useEffect } from 'react';

export const themes = {
  dark: {
    name: 'dark',
    icon: '🌙',
    label: 'Dark',
    vars: {
      '--bg': '#1a1a2e',
      '--text': '#eeeeee',
      '--accent': '#e94560',
      '--card-bg': '#16213e',
      '--border': '#0f3460',
      '--nav-bg': '#0f3460',
      '--muted': '#aaaaaa',
      '--input-bg': '#0f3460',
    },
  },
  light: {
    name: 'light',
    icon: '☀️',
    label: 'Light',
    vars: {
      '--bg': '#f5f5f5',
      '--text': '#333333',
      '--accent': '#2d6a4f',
      '--card-bg': '#ffffff',
      '--border': '#dddddd',
      '--nav-bg': '#2d6a4f',
      '--muted': '#666666',
      '--input-bg': '#ffffff',
    },
  },
  earth: {
    name: 'earth',
    icon: '🌿',
    label: 'Earth',
    vars: {
      '--bg': '#2d1b00',
      '--text': '#f0e6d3',
      '--accent': '#8bc34a',
      '--card-bg': '#3d2500',
      '--border': '#5a3a10',
      '--nav-bg': '#1a0f00',
      '--muted': '#c4a882',
      '--input-bg': '#3d2500',
    },
  },
};

const THEME_ORDER = ['dark', 'light', 'earth'];

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [themeName, setThemeName] = useState(() => {
    return localStorage.getItem('gidabo-theme') || 'dark';
  });

  const theme = themes[themeName] || themes.dark;

  useEffect(() => {
    localStorage.setItem('gidabo-theme', themeName);
  }, [themeName]);

  function cycleTheme() {
    const idx = THEME_ORDER.indexOf(themeName);
    const next = THEME_ORDER[(idx + 1) % THEME_ORDER.length];
    setThemeName(next);
  }

  return (
    <ThemeContext.Provider value={{ theme, themeName, setThemeName, cycleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
