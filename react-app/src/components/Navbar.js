import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand">
          <span className="brand-icon">🌍</span>
          <span className="brand-text">Gidabo Monitor</span>
        </div>

        <button
          className="nav-hamburger"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          <span></span><span></span><span></span>
        </button>

        <div className={`nav-links${menuOpen ? ' open' : ''}`}>
          <NavLink
            to="/"
            end
            className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
            onClick={() => setMenuOpen(false)}
          >
            🗺 Map
          </NavLink>
          <NavLink
            to="/about"
            className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
            onClick={() => setMenuOpen(false)}
          >
            ℹ About
          </NavLink>
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}
