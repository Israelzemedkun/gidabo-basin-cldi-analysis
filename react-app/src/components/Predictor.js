import React, { useState, useMemo } from 'react';

const ZONES = [
  { value: 'northern', label: 'Northern Highlands' },
  { value: 'central', label: 'Central Mid-Slope' },
  { value: 'southern', label: 'Southern Rift Floor' },
];

const RECOMMENDATIONS = {
  Degraded: [
    { icon: '🪨', text: 'Consider terracing on slopes to slow soil erosion' },
    { icon: '🐄', text: 'Reduce grazing pressure — give land time to recover' },
    { icon: '🌱', text: 'Plant cover crops to protect bare soil between seasons' },
  ],
  Stable: [
    { icon: '✅', text: 'Maintain your current land management practices' },
    { icon: '👁', text: 'Monitor vegetation cover annually to catch early changes' },
    { icon: '🚫', text: 'Avoid clearing new land areas for now' },
  ],
  Improved: [
    { icon: '🌿', text: 'Continue your current conservation practices — they are working' },
    { icon: '📝', text: 'Document what you are doing so you can repeat it next season' },
    { icon: '🤝', text: 'Share your practices with neighboring farmers' },
  ],
};

function computeCLDI(ndviSlider, bsiSlider, siSlider) {
  const ndvi_norm = ndviSlider / 100;
  const bsi_norm = bsiSlider / 100;
  const si_norm = siSlider / 100;
  return 0.5 * (1 - ndvi_norm) + 0.3 * bsi_norm + 0.2 * si_norm;
}

function getStatus(cldi) {
  if (cldi > 0.5) return 'Degraded';
  if (cldi < 0.3) return 'Improved';
  return 'Stable';
}

const STATUS_CONFIG = {
  Degraded: {
    icon: '🔴',
    headline: 'HIGH RISK — Active Degradation',
    message:
      'Your land shows signs of active degradation. Vegetation is low, bare soil is visible, and conditions are worsening. Action is recommended.',
    color: '#e74c3c',
    bg: 'rgba(231,76,60,0.12)',
  },
  Stable: {
    icon: '🟡',
    headline: 'MODERATE — Land is Stable',
    message:
      'Your land is holding steady. There are no strong signs of degradation right now, but it is worth keeping an eye on things.',
    color: '#f39c12',
    bg: 'rgba(243,156,18,0.12)',
  },
  Improved: {
    icon: '🟢',
    headline: 'LOW RISK — Land is Recovering',
    message:
      'Your land shows signs of recovery. Vegetation appears to be increasing and soil conditions are improving.',
    color: '#27ae60',
    bg: 'rgba(39,174,96,0.12)',
  },
};

function SliderInput({ id, label, sublabel, min, max, value, onChange, unit, leftLabel, rightLabel }) {
  return (
    <div className="slider-group">
      <label htmlFor={id} className="slider-label">
        {label}
        {sublabel && <span className="slider-sublabel">{sublabel}</span>}
      </label>
      <div className="slider-row">
        <span className="slider-edge-label">{leftLabel}</span>
        <input
          id={id}
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="range-input"
        />
        <span className="slider-edge-label">{rightLabel}</span>
      </div>
      <div className="slider-value">
        Current value: <strong>{value}{unit}</strong>
      </div>
    </div>
  );
}

export default function Predictor() {
  const [ndvi, setNdvi] = useState(40);
  const [bsi, setBsi] = useState(50);
  const [si, setSi] = useState(30);
  const [zone, setZone] = useState('central');
  const [assessed, setAssessed] = useState(false);

  const cldi = useMemo(() => computeCLDI(ndvi, bsi, si), [ndvi, bsi, si]);
  const status = useMemo(() => getStatus(cldi), [cldi]);
  const config = STATUS_CONFIG[status];

  function handleAssess() {
    setAssessed(true);
    setTimeout(() => {
      document.getElementById('predictor-result')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
  }

  return (
    <div className="predictor-page">
      <div className="predictor-container">
        <div className="predictor-header">
          <h1 className="predictor-title">Land Degradation Risk Assessment</h1>
          <p className="predictor-subtitle">
            Answer questions about your land to assess degradation risk
          </p>
        </div>

        <div className="predictor-card">
          <h2 className="section-heading">About Your Land</h2>

          <SliderInput
            id="ndvi"
            label="How green and vegetated is your land?"
            sublabel="Think about the amount of grass, shrubs, and trees you see"
            min={0}
            max={100}
            value={ndvi}
            onChange={setNdvi}
            unit="%"
            leftLabel="Bare / no plants"
            rightLabel="Very green"
          />

          <SliderInput
            id="bsi"
            label="How much bare soil is visible?"
            sublabel="Bare soil with no plant cover, exposed by erosion or clearing"
            min={0}
            max={100}
            value={bsi}
            onChange={setBsi}
            unit="%"
            leftLabel="None visible"
            rightLabel="Lots of bare soil"
          />

          <SliderInput
            id="si"
            label="Does your soil have a whitish or salty crust?"
            sublabel="A pale, crusty surface that water beads off — common in dry lowland areas"
            min={0}
            max={100}
            value={si}
            onChange={setSi}
            unit="%"
            leftLabel="No crust at all"
            rightLabel="Heavy white crust"
          />

          <div className="slider-group">
            <label htmlFor="zone" className="slider-label">
              Which zone is your land in?
            </label>
            <select
              id="zone"
              className="zone-select"
              value={zone}
              onChange={(e) => setZone(e.target.value)}
            >
              {ZONES.map((z) => (
                <option key={z.value} value={z.value}>{z.label}</option>
              ))}
            </select>
          </div>

          <button className="assess-btn" onClick={handleAssess}>
            Assess My Land →
          </button>
        </div>

        {assessed && (
          <div id="predictor-result" className="result-section">
            <div
              className="result-card"
              style={{ borderColor: config.color, background: config.bg }}
            >
              <div className="result-icon">{config.icon}</div>
              <div className="result-text">
                <h2 className="result-headline" style={{ color: config.color }}>
                  {config.headline}
                </h2>
                <p className="result-message">{config.message}</p>
              </div>
            </div>

            <div className="score-section">
              <div className="score-label">
                Degradation Score (CLDI)
                <span className="score-hint"> — higher means more degraded</span>
              </div>
              <div className="score-bar-wrap">
                <div className="score-bar-track">
                  <div
                    className="score-bar-fill"
                    style={{
                      width: `${Math.round(cldi * 100)}%`,
                      background: config.color,
                    }}
                  />
                </div>
                <span className="score-number" style={{ color: config.color }}>
                  {cldi.toFixed(2)}
                </span>
              </div>
              <div className="score-ticks">
                <span>0 — Excellent</span>
                <span>0.5 — Warning</span>
                <span>1 — Severe</span>
              </div>
            </div>

            <div className="recommendations-section">
              <h3 className="rec-heading">Recommended Actions for Your Land</h3>
              <div className="rec-list">
                {RECOMMENDATIONS[status].map((rec, i) => (
                  <div key={i} className="rec-item">
                    <span className="rec-icon">{rec.icon}</span>
                    <span>{rec.text}</span>
                  </div>
                ))}
              </div>
            </div>

            <button
              className="reassess-btn"
              onClick={() => {
                setAssessed(false);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            >
              ← Adjust and Reassess
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
