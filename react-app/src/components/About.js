import React from 'react';

function Section({ title, children }) {
  return (
    <section className="about-section">
      <h2 className="about-section-title">{title}</h2>
      <div className="about-section-body">{children}</div>
    </section>
  );
}

export default function About() {
  return (
    <div className="about-page">
      <div className="about-container">
        <div className="about-hero">
          <h1 className="about-title">About Gidabo Monitor</h1>
          <p className="about-lead">
            An open-source land degradation risk assessment tool for Ethiopia
          </p>
        </div>

        <Section title="What this tool does">
          <p>
            Gidabo Monitor helps farmers, extension workers, and land managers assess soil erosion risk anywhere in Ethiopia. Draw your fields on the map, and the tool automatically retrieves satellite-derived rainfall, slope, vegetation cover, and soil data for your location. The risk assessment uses the Revised Universal Soil Loss Equation (RUSLE), a globally validated model calibrated for Ethiopian conditions.
          </p>
        </Section>

        <Section title="How it works">
          <ul className="about-list">
            <li>Click or draw polygons on the map to select your land</li>
            <li>
              Satellite data auto-populates from CHIRPS rainfall (2015–2024), SRTM terrain,
              Landsat 8 NDVI (2020–2024), and OpenLandMap soil data
            </li>
            <li>Adjust any value based on your local knowledge</li>
            <li>
              Get instant RUSLE-based erosion risk:{' '}
              <strong>Low / Moderate / High / Severe</strong>
            </li>
            <li>Compare two locations side by side</li>
            <li>Save and print your assessment</li>
          </ul>
        </Section>

        <Section title="Methodology">
          <p>
            Risk is calculated using RUSLE:{' '}
            <strong>A = R × K × LS × C × P</strong>, where <strong>R</strong> is rainfall
            erosivity (Hurni 1985 Ethiopian formula: R = 0.0483 × rainfall<sup>1.61</sup>),{' '}
            <strong>K</strong> is soil erodibility, <strong>LS</strong> is slope
            length-steepness, <strong>C</strong> is cover management, and <strong>P</strong> is
            conservation practice factor. Risk thresholds follow Ethiopian Rift Valley studies:{' '}
            Low &lt;5 t/ha/yr, Moderate 5–15, High 15–50, Severe &gt;50 (Jothimani et al. 2022;
            average Gidabo watershed soil loss: 44.2 t/ha/yr).
          </p>
        </Section>

        <Section title="Data sources">
          <ul className="about-list">
            <li>
              <strong>CHIRPS Daily Precipitation 2015–2024</strong> — UCSB Climate Hazards Group
            </li>
            <li>
              <strong>SRTM Digital Elevation Model 30m</strong> — USGS
            </li>
            <li>
              <strong>Landsat 8 OLI Surface Reflectance 2020–2024</strong> — USGS Collection 2
            </li>
            <li>
              <strong>OpenLandMap Soil Texture Class</strong> — USDA system
            </li>
            <li>All data accessed via Google Earth Engine</li>
          </ul>
        </Section>

        <Section title="Links">
          <div className="about-links">
            <a
              className="about-link-card"
              href="https://github.com/Israelzemedkun/gidabo-basin-cldi-analysis"
              target="_blank"
              rel="noopener noreferrer"
            >
              <span className="link-icon">💻</span>
              <div>
                <div className="link-title">GitHub Repository</div>
                <div className="link-desc">Capstone analysis — source code and notebooks</div>
              </div>
            </a>
            <a
              className="about-link-card"
              href="https://gidabo-basin-cldi-analysis-7agztyjqthonaswefnezcf.streamlit.app/"
              target="_blank"
              rel="noopener noreferrer"
            >
              <span className="link-icon">📊</span>
              <div>
                <div className="link-title">Streamlit Dashboard</div>
                <div className="link-desc">Full interactive data science dashboard with model details</div>
              </div>
            </a>
          </div>
        </Section>

        <Section title="Author">
          <div className="about-author-card">
            <div className="author-avatar">🎓</div>
            <div>
              <div className="author-name">Israel Zemedkun Gebre</div>
              <div className="author-role">
                Capstone Project — Environmental Data Science
              </div>
              <p className="author-desc">
                This tool was developed as part of a capstone in Environmental Data Science.
              </p>
              <p className="author-desc">
                Built with React, Leaflet, leaflet-draw, and Google Earth Engine.
              </p>
            </div>
          </div>
        </Section>
      </div>
    </div>
  );
}
