# Gidabo Basin Land Degradation Monitor

## Summary

This project monitors land degradation in Ethiopia's Gidabo River Basin using Landsat 5 (2000) and Landsat 8 (2024) surface reflectance data. A Combined Land Degradation Index integrating vegetation, bare soil, and salinity signals classifies 500 sampled pixels. A Random Forest classifier achieves 95% cross-validated accuracy, with 94.9% of degradation labels independently confirmed by ESA WorldCover 2021.

## Live Dashboard

Interactive app: https://gidabo-basin-cldi-analysis-7agztyjqthonaswefnezcf.streamlit.app/

Features: spatial degradation map, zone filters, CLDI distribution, degradation risk predictor, and CSV export.

## Background

The Gidabo River Basin, located in the Ethiopian Rift Valley south of Lake Abijata-Shalla, drains approximately 3,500 sq km of highland and rift-floor terrain. It supports a dense smallholder farming population relying primarily on rain-fed cereal cultivation, coffee agroforestry, and irrigated horticulture along the valley floor. Over the past two decades, expanding cropland, woodland clearance, and population-driven overgrazing have accelerated soil exposure and surface salinisation in the lower rift, while upper catchment forests have come under increasing charcoal and timber pressure. Reliable, spatially explicit monitoring of land degradation is essential for targeting soil and water conservation investments, advising farmers on the most at-risk parcels, and tracking the effectiveness of restoration programmes over time.

## Research Questions

1. **Where is land degradation most severe?** Can Landsat-derived spectral indices (NDVI, BSI, SI) identify spatial hotspots of active degradation across the Gidabo Basin between 2000 and 2024?
2. **How has the degradation trajectory changed over 24 years?** Do composite CLDI values indicate a net increase in degraded area, and which zones (Northern highlands, Central mid-slope, Southern rift floor) show the strongest change signals?
3. **Can a machine-learning classifier reliably distinguish degradation states?** Does a Random Forest model trained on multi-index features generalise well enough to support operational land monitoring at 30 m resolution?

## Combined Land Degradation Index (CLDI)

```
CLDI = 0.5 * (1 - NDVI_norm) + 0.3 * BSI_norm + 0.2 * SI_norm
```

| Component | Weight | Justification |
|-----------|--------|---------------|
| NDVI (inverted) | 0.5 | Vegetation loss is the primary detectable degradation signal at 30 m in the Ethiopian Rift context. Reduced NDVI precedes and accompanies all other degradation pathways (Aragaw et al., 2021). |
| BSI | 0.3 | Bare soil exposure follows vegetation removal and is directly measurable from SWIR and visible bands. It is the second most spatially extensive indicator across the basin. |
| SI | 0.2 | Soil salinity is spectrally detectable in the lower rift floor but is geographically localised; a lower weight prevents it from dominating the index in non-saline highland zones. |

All index values are normalised to [0, 1] using MinMaxScaler before combining. Classification thresholds: CLDI > 0.5 = **Degraded**, CLDI < 0.3 = **Improved**, otherwise **Stable**.

## Data Sources

- **Landsat 5 TM** (year 2000): USGS Collection 2 Tier 1 Surface Reflectance - `LANDSAT/LT05/C02/T1_L2` via Google Earth Engine
- **Landsat 8 OLI** (2023-2024): USGS Collection 2 Tier 1 Surface Reflectance - `LANDSAT/LC08/C02/T1_L2` via Google Earth Engine
- All bands use the `SR_` prefix (Surface Reflectance). No TOA or proxy bands are used.
- Spectral indices:
  - **NDVI** - `(NIR - Red) / (NIR + Red)`
  - **BSI** - `((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))`
  - **SI** - `sqrt(Green * Red)`

## Machine Learning Methodology

- **Algorithm:** Random Forest classifier (`n_estimators=100`, `random_state=42`)
- **Split:** 80% training / 20% test, stratified by class
- **Features:** `NDVI_2000`, `NDVI_2024`, `BSI_2000`, `BSI_2024`, `SI_2000`, `SI_2024`, `NDVI_Change`, `SI_Change`
- **Target:** `Degradation_Status` (Degraded / Stable / Improved) derived from CLDI thresholds
- **Evaluation:** Accuracy, classification report (precision, recall, F1), confusion matrix
- **Saved model:** `models/rf_model.pkl`

## Repository Structure

```
gidabo-basin-cldi-analysis/
    data/
        gidabo_degradation_samples.csv   # 500 sampled pixels with all indices
    models/
        rf_model.pkl                     # Trained Random Forest model
    notebooks/
        analysis.ipynb                   # Full analytical pipeline and visualisations
    scripts/
        aoi_utils.py                     # Basin boundary helper
        generate_csv_data.py             # GEE data extraction and CSV generation
        ml_classifier.py                 # Model training and evaluation
        cldi_processor.py                # CLDI computation utilities
    requirements.txt
```

## Setup and Run Instructions

### 1. Clone and create environment

```bash
git clone <repo-url>
cd gidabo-basin-cldi-analysis
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Authenticate Google Earth Engine

```bash
earthengine authenticate
```

Update the project ID in `scripts/generate_csv_data.py` to match your GEE project.

### 4. Generate the dataset

```bash
cd scripts
python generate_csv_data.py
```

This samples 500 Landsat pixels across the basin and writes `data/gidabo_degradation_samples.csv` with NDVI, BSI, SI, and change columns for both epochs.

### 5. Train the classifier

```bash
python ml_classifier.py
```

Outputs accuracy, classification report, and confusion matrix to the console, then saves the model to `models/rf_model.pkl`.

### 6. Run the analysis notebook

```bash
cd ..
jupyter notebook notebooks/analysis.ipynb
```

Execute all cells in order to reproduce all figures and findings.

---

*This project was developed as a capstone in Environmental Data Science.*
