import React, { useState, useEffect, useRef } from 'react';

const R_OPTIONS = [
  { label: 'Very little (<400mm)', value: 25 },
  { label: 'Moderate (400–800mm)', value: 55 },
  { label: 'Heavy (800–1200mm)', value: 85 },
  { label: 'Very heavy (>1200mm)', value: 120 },
];

const K_OPTIONS = [
  { label: 'Sandy/gravelly (erodes slowly)', value: 0.10 },
  { label: 'Loamy/mixed', value: 0.25 },
  { label: 'Clay-loam', value: 0.35 },
  { label: 'Fine silty (erodes easily)', value: 0.45 },
];

const LS_OPTIONS = [
  { label: 'Flat (0–2%)', value: 0.5 },
  { label: 'Gentle slope (2–8%)', value: 2.0 },
  { label: 'Moderate slope (8–20%)', value: 6.0 },
  { label: 'Steep (>20%)', value: 15.0 },
];

const C_OPTIONS = [
  { label: 'Bare/almost bare (0–10%)', value: 0.45 },
  { label: 'Sparse cover (10–40%)', value: 0.20 },
  { label: 'Good cover (40–70%)', value: 0.08 },
  { label: 'Dense cover (>70%)', value: 0.02 },
];

const P_OPTIONS = [
  { label: 'None', value: 1.0 },
  { label: 'Some (contour farming)', value: 0.6 },
  { label: 'Good (terracing)', value: 0.35 },
  { label: 'Excellent (terracing + cover crops)', value: 0.15 },
];

const RECOMMENDATIONS = {
  low: [
    'Maintain vegetation cover on all fields',
    'Monitor land health annually',
    'Share conservation practices with neighbors',
  ],
  moderate: [
    'Add cover crops between growing seasons',
    'Avoid tilling on slopes',
    'Plant grass strips along field edges',
  ],
  high: [
    'Build terraces on slopes above 8%',
    'Immediately establish permanent vegetation cover',
    'Contact extension services for soil conservation support',
  ],
  severe: [
    'URGENT: Establish emergency vegetation cover now',
    'Stop cultivation on the steepest areas immediately',
    'Seek immediate support from the local agricultural bureau',
  ],
};

const RISK_CONFIG = {
  low:      { label: 'LOW RISK',  color: '#27ae60', icon: '🟢', bg: 'rgba(39,174,96,0.1)',  border: '#27ae60', recIcon: '✅' },
  moderate: { label: 'MODERATE',  color: '#f39c12', icon: '⚠️', bg: 'rgba(243,156,18,0.1)', border: '#f39c12', recIcon: '⚠️' },
  high:     { label: 'HIGH RISK', color: '#e74c3c', icon: '🔴', bg: 'rgba(231,76,60,0.1)',  border: '#e74c3c', recIcon: '🔧' },
  severe:   { label: 'SEVERE',    color: '#7b0000', icon: '🚨', bg: 'rgba(123,0,0,0.12)',   border: '#7b0000', recIcon: '🚨' },
};

function classifyRisk(A) {
  if (A < 5)  return 'low';
  if (A < 15) return 'moderate';
  if (A < 50) return 'high';
  return 'severe';
}

function rainfallToIdx(mm)  { return mm < 400 ? 0 : mm < 800 ? 1 : mm < 1200 ? 2 : 3; }
function slopeToIdx(deg)    { return deg < 2  ? 0 : deg < 8  ? 1 : deg < 20  ? 2 : 3; }
function ndviToIdx(ndvi)    { return ndvi < 0.1 ? 0 : ndvi < 0.4 ? 1 : ndvi < 0.7 ? 2 : 3; }
function soilKToIdx(soil_k) { return Math.max(0, Math.min(3, Math.round(soil_k) - 1)); }

function findNearestPoint(points, lat, lon) {
  let best = null, bestDist = Infinity;
  for (const pt of points) {
    const d = Math.sqrt((pt.lat - lat) ** 2 + (pt.lon - lon) ** 2);
    if (d < bestDist) { bestDist = d; best = pt; }
  }
  return { point: best, dist: bestDist };
}

function computeRUSLE(rI, kI, lsI, cI, pI) {
  return R_OPTIONS[rI].value * K_OPTIONS[kI].value * LS_OPTIONS[lsI].value *
         C_OPTIONS[cI].value * P_OPTIONS[pI].value;
}

// ─── Print helper ────────────────────────────────────────────────────────────
function openPrintView(location, rIdx, kIdx, lsIdx, cIdx, pIdx, A, riskLevel) {
  const risk = RISK_CONFIG[riskLevel];
  const recs = RECOMMENDATIONS[riskLevel];
  const locStr = `${location.lat.toFixed(4)}°N, ${location.lon.toFixed(4)}°E`;
  const date = new Date().toLocaleDateString();

  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Soil Erosion Assessment — ${locStr}</title>
  <style>
    body { font-family: Georgia, serif; max-width: 620px; margin: 40px auto; color: #222; line-height: 1.5; }
    h1 { font-size: 1.4rem; border-bottom: 2px solid #ccc; padding-bottom: 8px; margin-bottom: 4px; }
    .meta { font-size: 0.9rem; color: #555; margin-bottom: 16px; }
    .badge { font-size: 1.3rem; font-weight: bold; color: ${risk.color}; margin: 12px 0 4px; }
    .loss { font-size: 1rem; margin-bottom: 16px; }
    table { width: 100%; border-collapse: collapse; margin: 12px 0 20px; }
    td, th { border: 1px solid #ddd; padding: 7px 10px; text-align: left; font-size: 0.92rem; }
    th { background: #f5f5f5; font-weight: 600; }
    h2 { font-size: 1.05rem; margin: 16px 0 6px; }
    ul { padding-left: 1.4em; margin: 0; }
    li { margin-bottom: 6px; font-size: 0.92rem; }
    .footer { margin-top: 28px; font-size: 0.78rem; color: #999; border-top: 1px solid #eee; padding-top: 8px; }
    @media print { body { margin: 20px; } }
  </style>
</head>
<body>
  <h1>Soil Erosion Risk Assessment</h1>
  <div class="meta"><strong>Location:</strong> ${locStr} &nbsp;·&nbsp; <strong>Date:</strong> ${date}</div>
  <div class="badge">${risk.icon} ${risk.label}</div>
  <div class="loss">Estimated soil loss: <strong>${A.toFixed(1)} tonnes per hectare per year</strong></div>
  <h2>Input Values</h2>
  <table>
    <tr><th>Factor</th><th>Value selected</th></tr>
    <tr><td>Rainfall (R)</td><td>${R_OPTIONS[rIdx].label}</td></tr>
    <tr><td>Soil type (K)</td><td>${K_OPTIONS[kIdx].label}</td></tr>
    <tr><td>Slope (LS)</td><td>${LS_OPTIONS[lsIdx].label}</td></tr>
    <tr><td>Vegetation (C)</td><td>${C_OPTIONS[cIdx].label}</td></tr>
    <tr><td>Conservation (P)</td><td>${P_OPTIONS[pIdx].label}</td></tr>
  </table>
  <h2>Recommendations</h2>
  <ul>${recs.map(r => `<li>${r}</li>`).join('')}</ul>
  <div class="footer">Generated by Gidabo Monitor &nbsp;·&nbsp; RUSLE method</div>
</body>
</html>`;

  const win = window.open('', '_blank');
  if (!win) return;
  win.document.write(html);
  win.document.close();
  win.focus();
  setTimeout(() => win.print(), 300);
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function Panel({
  location,
  onRiskChange,
  gridPoints,
  gridLoading,
  comparisonMode,
  comparisonLocation,
  onEnterComparisonMode,
  onExitComparisonMode,
  onComparisonRiskChange,
  onClearAll,
}) {
  // Slider state for location A
  const [rIdx, setRIdx]   = useState(1);
  const [kIdx, setKIdx]   = useState(1);
  const [lsIdx, setLsIdx] = useState(1);
  const [cIdx, setCIdx]   = useState(2);
  const [pIdx, setPIdx]   = useState(0);

  // Satellite auto-population state
  const [autoIndices, setAutoIndices] = useState(null); // { rIdx, kIdx, lsIdx, cIdx }
  const [autoData, setAutoData]       = useState(null); // raw satellite values
  const [tooFar, setTooFar]           = useState(false);

  // Comparison B state
  const [compB, setCompB] = useState(null);

  const prevLocation     = useRef(null);
  const prevCompLocation = useRef(null);

  // Auto-populate A when location or gridPoints change
  useEffect(() => {
    if (!location || !gridPoints) return;

    const prev = prevLocation.current;
    if (prev && prev.lat === location.lat && prev.lon === location.lon) return;
    prevLocation.current = location;

    setTooFar(false);
    setAutoData(null);
    setAutoIndices(null);

    const src = location.polygonData
      ? {
          rainfall:     location.polygonData.rainfall,
          slope:        location.polygonData.slope,
          ndvi:         location.polygonData.ndvi,
          soil_k:       location.polygonData.soil_k,
          pointCount:   location.polygonData.pointCount,
          polygonCount: location.polygonData.polygonCount,
          dist: 0,
        }
      : (() => {
          const { point, dist } = findNearestPoint(gridPoints, location.lat, location.lon);
          return point ? { ...point, dist } : null;
        })();

    if (!src || src.dist > 1.0) {
      setTooFar(true);
      return;
    }

    const rI  = rainfallToIdx(src.rainfall);
    const lsI = slopeToIdx(src.slope);
    const cI  = ndviToIdx(src.ndvi);
    const kI  = soilKToIdx(src.soil_k);
    setRIdx(rI); setLsIdx(lsI); setCIdx(cI); setKIdx(kI);
    setAutoIndices({ rIdx: rI, kIdx: kI, lsIdx: lsI, cIdx: cI });
    setAutoData({
      rainfall:     src.rainfall,
      slope:        src.slope,
      ndvi:         src.ndvi,
      soil_k:       src.soil_k,
      pointCount:   src.pointCount ?? 1,
      polygonCount: src.polygonCount ?? null,
    });
  }, [location, gridPoints]);

  // Auto-populate B when comparisonLocation changes.
  // Handles both polygon-drawn locations (polygonData present) and single-click points.
  useEffect(() => {
    if (!comparisonLocation || !gridPoints) { setCompB(null); return; }

    const prev = prevCompLocation.current;
    if (prev && prev.lat === comparisonLocation.lat && prev.lon === comparisonLocation.lon) return;
    prevCompLocation.current = comparisonLocation;

    const src = comparisonLocation.polygonData
      ? { ...comparisonLocation.polygonData, dist: 0 }
      : (() => {
          const { point, dist } = findNearestPoint(gridPoints, comparisonLocation.lat, comparisonLocation.lon);
          return point ? { ...point, dist } : null;
        })();

    if (!src || src.dist > 1.0) { setCompB({ tooFar: true }); return; }

    const rI  = rainfallToIdx(src.rainfall);
    const lsI = slopeToIdx(src.slope);
    const cI  = ndviToIdx(src.ndvi);
    const kI  = soilKToIdx(src.soil_k);
    const Ab  = computeRUSLE(rI, kI, lsI, cI, 0);
    const rl  = classifyRisk(Ab);
    setCompB({ rIdx: rI, kIdx: kI, lsIdx: lsI, cIdx: cI, pIdx: 0, A: Ab, riskLevel: rl, tooFar: false });
  }, [comparisonLocation, gridPoints]);

  // Notify parent of B's risk for pin colour
  useEffect(() => {
    if (compB && !compB.tooFar) onComparisonRiskChange(compB.riskLevel);
  }, [compB, onComparisonRiskChange]);

  // RUSLE for A
  const R  = R_OPTIONS[rIdx].value;
  const K  = K_OPTIONS[kIdx].value;
  const LS = LS_OPTIONS[lsIdx].value;
  const C  = C_OPTIONS[cIdx].value;
  const P  = P_OPTIONS[pIdx].value;
  const A  = R * K * LS * C * P;
  const riskLevel = classifyRisk(A);
  const risk      = RISK_CONFIG[riskLevel];

  useEffect(() => {
    if (location) onRiskChange(riskLevel);
  }, [riskLevel, location, onRiskChange]);

  // Has farmer changed any slider away from satellite values?
  const hasChanged = autoIndices && (
    rIdx  !== autoIndices.rIdx  ||
    kIdx  !== autoIndices.kIdx  ||
    lsIdx !== autoIndices.lsIdx ||
    cIdx  !== autoIndices.cIdx
  );

  function resetToSatellite() {
    if (!autoIndices) return;
    setRIdx(autoIndices.rIdx);
    setKIdx(autoIndices.kIdx);
    setLsIdx(autoIndices.lsIdx);
    setCIdx(autoIndices.cIdx);
  }

  // ─── Placeholder ─────────────────────────────────────────────────────────
  if (!location) {
    return (
      <div className="panel-placeholder">
        <div className="panel-placeholder-icon">📍</div>
        <h2 className="panel-placeholder-title">Select a location on the map</h2>
        <p className="panel-placeholder-desc">
          Click anywhere in Ethiopia to begin your soil erosion risk assessment.
        </p>
        <div className="panel-instructions">
          <div className="panel-instruction-item">
            <span className="instruction-num">1</span>
            Click a point on the map
          </div>
          <div className="panel-instruction-item">
            <span className="instruction-num">2</span>
            Answer 5 simple questions about your land
          </div>
          <div className="panel-instruction-item">
            <span className="instruction-num">3</span>
            Get an instant risk assessment with recommendations
          </div>
        </div>
      </div>
    );
  }

  // ─── Comparison view (Improvement 5) ────────────────────────────────────
  if (comparisonLocation && compB && !compB.tooFar) {
    const riskB   = RISK_CONFIG[compB.riskLevel];
    const barPctA = Math.min((A / 100) * 100, 100);
    const barPctB = Math.min((compB.A / 100) * 100, 100);
    const higher  = A >= compB.A ? 'A' : 'B';
    const diffPct = compB.A > 0 ? Math.abs(((A - compB.A) / compB.A) * 100).toFixed(0) : null;

    return (
      <div className="panel-assessment">
        <div className="comparison-header">
          <span>📍 Comparison Mode</span>
          <button className="reset-btn" onClick={onExitComparisonMode}>✕ Clear comparison</button>
        </div>

        <div className="comparison-panel">
          {/* Column A */}
          <div className="comparison-col">
            <div className="comp-col-label comp-col-label--a">Location A</div>
            <div className="comp-coords">{location.lat.toFixed(3)}°N, {location.lon.toFixed(3)}°E</div>
            <div className="panel-result-badge" style={{ color: risk.color }}>{risk.icon} {risk.label}</div>
            <div className="comp-loss">{A.toFixed(1)} t/ha/yr</div>
            <div className="panel-result-bar-track comp-bar">
              <div className="panel-result-bar-fill" style={{ width: `${barPctA}%`, background: risk.color }} />
            </div>
            <div className="comp-rec">{risk.recIcon} {RECOMMENDATIONS[riskLevel][0]}</div>
          </div>

          {/* Column B */}
          <div className="comparison-col">
            <div className="comp-col-label comp-col-label--b">Location B</div>
            <div className="comp-coords">{comparisonLocation.lat.toFixed(3)}°N, {comparisonLocation.lon.toFixed(3)}°E</div>
            <div className="panel-result-badge" style={{ color: riskB.color }}>{riskB.icon} {riskB.label}</div>
            <div className="comp-loss">{compB.A.toFixed(1)} t/ha/yr</div>
            <div className="panel-result-bar-track comp-bar">
              <div className="panel-result-bar-fill" style={{ width: `${barPctB}%`, background: riskB.color }} />
            </div>
            <div className="comp-rec">{riskB.recIcon} {RECOMMENDATIONS[compB.riskLevel][0]}</div>
          </div>
        </div>

        {diffPct && (
          <div className="comparison-summary">
            Location {higher} has {diffPct}% higher erosion risk than Location {higher === 'A' ? 'B' : 'A'}
          </div>
        )}
      </div>
    );
  }

  // ─── Normal assessment view ───────────────────────────────────────────────
  const barPct = Math.min((A / 100) * 100, 100);

  return (
    <div className="panel-assessment">
      <div className="panel-location-bar">
        <span className="panel-location-icon">📍</span>
        <span>
          Selected: <strong>{location.lat.toFixed(4)}°N, {location.lon.toFixed(4)}°E</strong>
        </span>
      </div>

      {/* Auto-population status banner */}
      {gridLoading && (
        <div className="data-status data-status--loading">
          <span className="data-status-spinner" /> Loading location data...
        </div>
      )}
      {!gridLoading && tooFar && (
        <div className="data-status data-status--warning">
          ⚠ No data found near this location — using default values
        </div>
      )}
      {!gridLoading && autoData && !tooFar && (
        <div className="data-status data-status--loaded">
          <span className="data-status-dot" />
          {autoData.polygonCount
            ? `Assessment averaged across ${autoData.polygonCount} polygon${autoData.polygonCount !== 1 ? 's' : ''}, ${autoData.pointCount} satellite point${autoData.pointCount !== 1 ? 's' : ''}`
            : 'Data loaded for this location'}
          {autoData.polygonCount > 1 && (
            <div className="data-status-values" style={{ marginTop: '2px' }}>
              Location A: {autoData.polygonCount} fields selected
            </div>
          )}
          <div className="data-status-values">
            Rainfall: {Math.round(autoData.rainfall).toLocaleString()}mm &nbsp;|&nbsp;
            Slope: {autoData.slope.toFixed(1)}° &nbsp;|&nbsp;
            Vegetation: {autoData.ndvi.toFixed(2)} NDVI
          </div>
        </div>
      )}

      <div className="panel-form">
        {/* Q1 — Rainfall (R factor) */}
        <div className="panel-question">
          <label className="panel-q-label">How much rain falls on your land each year?</label>
          <input
            type="range" className="range-input panel-slider"
            min={0} max={3} step={1} value={rIdx}
            onChange={e => setRIdx(Number(e.target.value))}
          />
          <div className="slider-step-ticks">
            {R_OPTIONS.map((opt, i) => (
              <span key={i} className={i === rIdx ? 'tick-active' : ''}>{opt.label}</span>
            ))}
          </div>
          {autoData && (
            <div className="satellite-hint">Satellite: {Math.round(autoData.rainfall).toLocaleString()} mm/yr</div>
          )}
        </div>

        {/* Q2 — Soil type (K factor) */}
        <div className="panel-question">
          <label className="panel-q-label">What is your soil like?</label>
          <select className="panel-select" value={kIdx} onChange={e => setKIdx(Number(e.target.value))}>
            {K_OPTIONS.map((opt, i) => (
              <option key={i} value={i}>{opt.label}</option>
            ))}
          </select>
          {autoData
            ? <div className="satellite-hint">Satellite soil class: K={K_OPTIONS[autoIndices.kIdx].value.toFixed(2)}</div>
            : null
          }
        </div>

        {/* Q3 — Slope (LS factor) */}
        <div className="panel-question">
          <label className="panel-q-label">How steep is your land?</label>
          <select className="panel-select" value={lsIdx} onChange={e => setLsIdx(Number(e.target.value))}>
            {LS_OPTIONS.map((opt, i) => (
              <option key={i} value={i}>{opt.label}</option>
            ))}
          </select>
          {autoData && (
            <div className="satellite-hint">Satellite: {autoData.slope.toFixed(1)}°</div>
          )}
        </div>

        {/* Q4 — Cover (C factor) — Improvement 7: NDVI in active label */}
        <div className="panel-question">
          <label className="panel-q-label">
            How much of your soil is covered by plants, crops, or mulch?
          </label>
          <input
            type="range" className="range-input panel-slider"
            min={0} max={3} step={1} value={cIdx}
            onChange={e => setCIdx(Number(e.target.value))}
          />
          <div className="slider-step-ticks">
            {C_OPTIONS.map((opt, i) => {
              const isActive = i === cIdx;
              const label =
                isActive && autoData
                  ? `${opt.label.split(' (')[0]} (NDVI: ${autoData.ndvi.toFixed(2)})`
                  : opt.label;
              return (
                <span key={i} className={isActive ? 'tick-active' : ''}>{label}</span>
              );
            })}
          </div>
          {autoData && (
            <div className="satellite-hint">Satellite NDVI: {autoData.ndvi.toFixed(2)}</div>
          )}
        </div>

        {/* Q5 — Conservation (P factor) */}
        <div className="panel-question">
          <label className="panel-q-label">Do you use any soil conservation practices?</label>
          <select className="panel-select" value={pIdx} onChange={e => setPIdx(Number(e.target.value))}>
            {P_OPTIONS.map((opt, i) => (
              <option key={i} value={i}>{opt.label}</option>
            ))}
          </select>
          <div className="satellite-hint">Satellite data not available — based on your knowledge</div>
        </div>
      </div>

      {/* Improvement 4 — Reset to satellite values */}
      {hasChanged && (
        <button className="reset-btn" onClick={resetToSatellite}>
          ↺ Reset to satellite values
        </button>
      )}

      {/* Risk result */}
      <div className="panel-result" style={{ borderColor: risk.border, background: risk.bg }}>
        <div className="panel-result-badge" style={{ color: risk.color }}>
          {risk.icon} {risk.label}
        </div>
        <div className="panel-result-loss">
          Estimated soil loss:{' '}
          <strong>{A.toFixed(1)} tonnes per hectare per year</strong>
        </div>
        <div className="panel-result-bar-wrap">
          <div className="panel-result-bar-track">
            <div className="panel-result-bar-fill" style={{ width: `${barPct}%`, background: risk.color }} />
          </div>
        </div>
        <div className="panel-result-bar-labels">
          <span>0</span><span>25</span><span>50</span><span>75</span><span>100+</span>
        </div>
        <div className="panel-result-bar-unit">t/ha/yr</div>
      </div>

      {/* Recommendations */}
      <div className="panel-recs">
        <div className="rec-heading">Recommendations</div>
        <div className="rec-list">
          {RECOMMENDATIONS[riskLevel].map((rec, i) => (
            <div key={i} className="rec-item">
              <span className="rec-icon">{risk.recIcon}</span>
              <span>{rec}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Compare / print / clear-all actions */}
      <div className="panel-actions">
        {!comparisonLocation && !comparisonMode && (
          <button className="action-btn action-btn--compare" onClick={onEnterComparisonMode}>
            📍 Compare with another location
          </button>
        )}
        {comparisonMode && (
          <div className="data-status data-status--loading" style={{ marginTop: 0 }}>
            <span className="data-status-spinner" /> Click the map to place a comparison pin...
          </div>
        )}

        {/* Print button */}
        <button
          className="action-btn action-btn--print"
          onClick={() => openPrintView(location, rIdx, kIdx, lsIdx, cIdx, pIdx, A, riskLevel)}
        >
          🖨 Save Assessment
        </button>

        {/* Clear all / Start over */}
        <button className="action-btn action-btn--clear" onClick={onClearAll}>
          ✕ Clear all / Start over
        </button>
      </div>
    </div>
  );
}
