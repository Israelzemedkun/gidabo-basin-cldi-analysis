import React from 'react';
import { useTheme } from '../context/ThemeContext';

export default function ThemeToggle() {
  const { theme, cycleTheme } = useTheme();

  return (
    <button
      className="theme-toggle"
      onClick={cycleTheme}
      title={`Current theme: ${theme.label}. Click to change.`}
      aria-label={`Switch theme (currently ${theme.label})`}
    >
      <span className="theme-icon">{theme.icon}</span>
      <span className="theme-label">{theme.label}</span>
    </button>
  );
}
