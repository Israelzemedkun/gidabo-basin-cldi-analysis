# Gidabo Basin Land Degradation Monitor

## Summary

This project investigates spectral characterization of land degradation in Ethiopia's Gidabo River Basin using Landsat 5 (2000) and Landsat 8 (2024) surface reflectance data. A Combined Land Degradation Index (CLDI) classifies 500 sampled pixels; a Random Forest classifier achieves 95% cross-validated accuracy. Label validity is partially supported by 94.9% consistency with ESA WorldCover 2021.

## Live Dashboard

Interactive app: https://gidabo-basin-cldi-analysis-7agztyjqthonaswefnezcf.streamlit.app/

Features: spatial degradation map, zone filters, CLDI distribution, degradation risk predictor, and CSV export.

## Interactive Tools

- **Streamlit Dashboard** (analysis results): https://gidabo-basin-cldi-analysis-7agztyjqthonaswefnezcf.streamlit.app/
- **Gidabo Monitor** (interactive RUSLE risk assessment for Ethiopia): https://gidabo-monitor-ko6e.vercel.app/

## Research Question

This project investigates whether land degradation status in the Gidabo River Basin, Ethiopia can be reliably characterized using multi-temporal Landsat surface reflectance indices (NDVI, BSI, SI) and classified using a machine learning approach, without requiring field-collected ground truth data.

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

**On label generation:** Labels are derived from CLDI thresholds applied to the same spectral indices used as classifier features. This creates a circular dependency: the Random Forest model is learning to replicate the CLDI formula, not to detect degradation independently. The 97% test accuracy and 95% cross-validated accuracy therefore reflect the model's ability to learn the index thresholds, not its ability to detect real-world degradation. The ESA WorldCover validation (94.9% consistency) provides partial independent support for label validity, but does not constitute true ground truth.

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

## Results

The classifier successfully learns to replicate CLDI-derived labels from raw spectral indices with high consistency (95% CV accuracy). Spatially, degraded pixels cluster in the Central Zone, consistent with published accounts of agricultural intensification in the Gidabo Basin (Aragaw et al. 2021). These findings should be interpreted as spectral change detection rather than field-validated degradation mapping.

## Limitations

- **Label circularity (primary limitation):** `Degradation_Status` labels are derived from CLDI thresholds applied to NDVI, BSI, and SI, which are also the classifier features. The model therefore learns the threshold function rather than an independent degradation signal. Future work should incorporate field-validated soil degradation measurements or independent land cover change data to train a genuinely predictive classifier.
- **No field validation:** Pixel-level CLDI scores have not been cross-checked against on-the-ground degradation assessments. ESA WorldCover 2021 provides a consistent but coarse independent check.
- **Single-season composites:** Both Landsat epochs use dry-season composites, which reduces cloud contamination but may not capture wet-season vegetation dynamics relevant to degradation.
- **Sample size:** 500 pixels represents a small fraction of the basin at 30 m resolution; spatial coverage is not exhaustive.
- **Salinity index sensitivity:** The SI formula (`sqrt(Green * Red)`) has moderate specificity for saline soils; it also responds to bare dry soil, which may inflate salinity signals in non-saline upland zones.

## Repository Structure

```
gidabo-basin-cldi-analysis/
  data/                    # Sampled pixel data with spectral indices and WorldCover labels
  figures/                 # All output figures from the analysis notebook
  models/                  # Trained Random Forest model (rf_model.pkl)
  notebooks/               # Analysis notebook (run after all scripts)
  scripts/
    01_data_extraction/    # GEE data extraction scripts (run first)
    02_processing/         # CLDI computation utilities
    03_modeling/           # Random Forest classifier training and evaluation
    04_validation/         # ESA WorldCover label validation
  app/                     # Streamlit dashboard
  react-app/               # Interactive React tool (Gidabo Monitor)
  GEE_SETUP.md             # Google Earth Engine setup instructions
  WORKFLOW.md              # Step-by-step analysis workflow
  requirements.txt         # Python dependencies
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

### 3. Configure Google Earth Engine

See `GEE_SETUP.md` for full instructions including account creation, project registration, authentication, and project ID replacement.

```bash
earthengine authenticate
python -c "import ee; ee.Initialize(project='YOUR_PROJECT_ID'); print('GEE OK')"
```

### 4. Run the pipeline

See `WORKFLOW.md` for the full step-by-step pipeline. Short version:

```bash
# Step 1 — extract data
cd scripts/01_data_extraction && python generate_csv_data.py

# Step 2 — train classifier
cd ../03_modeling && python ml_classifier.py

# Step 3 — validate labels
cd ../04_validation && python validate_labels.py

# Step 4 — run analysis notebook
cd ../.. && jupyter notebook notebooks/analysis.ipynb
```

---

*This project was developed as a capstone in Environmental Data Science.*
