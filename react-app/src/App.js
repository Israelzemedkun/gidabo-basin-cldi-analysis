import React, { useState, useEffect, useRef, useCallback } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, useTheme } from './context/ThemeContext';
import Navbar from './components/Navbar';
import Map from './components/Map';
import Panel from './components/Panel';
import About from './components/About';
import './App.css';

function MapPage() {
  const [gridPoints, setGridPoints] = useState(null);
  const [gridLoading, setGridLoading] = useState(true);

  const [selectedLocation, setSelectedLocation] = useState(null);
  const [riskLevel, setRiskLevel] = useState(null);

  const [comparisonMode, setComparisonMode] = useState(false);
  const [comparisonLocation, setComparisonLocation] = useState(null);
  const [comparisonRiskLevel, setComparisonRiskLevel] = useState(null);

  useEffect(() => {
    fetch('/data/ethiopia_grid.json')
      .then(r => r.json())
      .then(json => { setGridPoints(json.points); setGridLoading(false); })
      .catch(() => setGridLoading(false));
  }, []);

  // Use a ref so handleLocationSelect stays stable across comparisonMode changes
  const comparisonModeRef = useRef(comparisonMode);
  useEffect(() => { comparisonModeRef.current = comparisonMode; }, [comparisonMode]);

  const handleLocationSelect = useCallback((loc) => {
    if (comparisonModeRef.current) {
      setComparisonLocation(loc);
      setComparisonMode(false);
    } else {
      setSelectedLocation(loc);
      setComparisonLocation(null);
      setComparisonRiskLevel(null);
    }
  }, []);

  const handleComparisonSelect = useCallback((loc) => {
    setComparisonLocation(loc);
  }, []);

  function handleExitComparison() {
    setComparisonMode(false);
    setComparisonLocation(null);
    setComparisonRiskLevel(null);
  }

  // Resets all state — clears both polygon sets reactively via DrawControl's cleanup effects.
  const handleClearAll = useCallback(() => {
    setSelectedLocation(null);
    setRiskLevel(null);
    setComparisonLocation(null);
    setComparisonRiskLevel(null);
    setComparisonMode(false);
  }, []);

  // Called by DrawControl when the user deletes Location A's drawn polygon.
  const handleDeleteA = useCallback(() => {
    setSelectedLocation(null);
    setRiskLevel(null);
    setComparisonLocation(null);
    setComparisonRiskLevel(null);
    setComparisonMode(false);
  }, []);

  // Called by DrawControl when the user deletes Location B's drawn polygon.
  const handleDeleteB = useCallback(() => {
    setComparisonLocation(null);
    setComparisonRiskLevel(null);
    setComparisonMode(false);
  }, []);

  return (
    <div className="app-layout">
      <div className="map-side">
        <Map
          selectedLocation={selectedLocation}
          onLocationSelect={handleLocationSelect}
          onComparisonSelect={handleComparisonSelect}
          onDeleteA={handleDeleteA}
          onDeleteB={handleDeleteB}
          riskLevel={riskLevel}
          comparisonMode={comparisonMode}
          comparisonLocation={comparisonLocation}
          comparisonRiskLevel={comparisonRiskLevel}
          gridPoints={gridPoints}
        />
      </div>
      <div className="panel-side">
        <Panel
          location={selectedLocation}
          onRiskChange={setRiskLevel}
          gridPoints={gridPoints}
          gridLoading={gridLoading}
          comparisonMode={comparisonMode}
          comparisonLocation={comparisonLocation}
          onEnterComparisonMode={() => setComparisonMode(true)}
          onExitComparisonMode={handleExitComparison}
          onComparisonRiskChange={setComparisonRiskLevel}
          onClearAll={handleClearAll}
        />
      </div>
    </div>
  );
}

function ThemedApp() {
  const { themeName } = useTheme();

  return (
    <div id="app-root" className={`theme-${themeName}`}>
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<MapPage />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <ThemedApp />
    </ThemeProvider>
  );
}

export default App;
