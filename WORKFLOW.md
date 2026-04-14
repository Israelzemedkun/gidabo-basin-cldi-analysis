# Analysis Workflow

Full pipeline for reproducing the Gidabo Basin land degradation analysis. Steps must be run in order; each step's output is required by the next.

---

## Step 1 — Data Extraction (`scripts/01_data_extraction/`)

**Prerequisite:** GEE authentication and a valid project ID. See `GEE_SETUP.md`.

```bash
cd scripts/01_data_extraction
python generate_csv_data.py
```

What happens:
- Connects to Google Earth Engine using the `ee-my-israelzemedkungebre` project (replace with your own)
- Retrieves the Gidabo River Basin boundary from WWF HydroSHEDS Level 12 (`aoi_utils.py`)
- Composites Landsat 5 TM Surface Reflectance (1999–2001 dry seasons) and Landsat 8 OLI Surface Reflectance (2023–2024 dry seasons)
- Computes NDVI, BSI, and SI for both epochs at each of 500 randomly sampled pixel centroids
- Writes `data/gidabo_degradation_samples.csv` (~500 rows)

Runtime: 3–10 minutes depending on GEE queue.

---

## Step 2 — Processing (`scripts/02_processing/`)

No standalone execution required for the main pipeline. `cldi_processor.py` is a utility module imported by the analysis notebook and the classifier. It computes:

```
CLDI = 0.5 * (1 - NDVI_norm) + 0.3 * BSI_norm + 0.2 * SI_norm
```

and assigns `Degradation_Status` labels based on CLDI thresholds (> 0.5 → Degraded, < 0.3 → Improved, otherwise Stable).

To test the module in isolation:
```bash
cd scripts/02_processing
python cldi_processor.py
```

---

## Step 3 — Modeling (`scripts/03_modeling/`)

```bash
cd scripts/03_modeling
python ml_classifier.py
```

What happens:
- Loads `data/gidabo_degradation_samples.csv`
- Normalises spectral index columns with `MinMaxScaler`
- Applies CLDI thresholds to generate `Degradation_Status` labels
- Trains `RandomForestClassifier(n_estimators=100, random_state=42)` on 80% of pixels
- Evaluates on 20% held-out test set (accuracy, classification report, confusion matrix)
- Runs 5-fold stratified cross-validation
- Saves trained model to `models/rf_model.pkl`

Expected output: ~97% test accuracy, ~95% CV accuracy.

**Methodological note:** High accuracy reflects the model learning CLDI threshold logic from its own input features, not independent degradation detection. See README.md — Limitations.

---

## Step 4 — Validation (`scripts/04_validation/`)

```bash
cd scripts/04_validation
python validate_labels.py
```

What happens:
- Loads pixel centroids from `data/gidabo_degradation_samples.csv`
- Samples ESA WorldCover 2021 land cover class for each centroid via GEE (`ESA/WorldCover/v200`)
- Compares WorldCover classes to CLDI-derived `Degradation_Status` labels
- Writes consistency statistics to `data/label_validation_report.txt`

Expected output: ~94.9% consistency between WorldCover classes and CLDI labels.

---

## Step 5 — Analysis Notebook (`notebooks/`)

```bash
cd ../..
jupyter notebook notebooks/analysis.ipynb
```

Run all cells in order. The notebook:
1. Loads `data/gidabo_degradation_samples.csv`
2. Recomputes CLDI and labels (for transparency — does not depend on `ml_classifier.py` output)
3. Produces all figures, saved to `figures/fig_*.png`
4. Loads `models/rf_model.pkl` for evaluation visualisations
5. Loads `data/label_validation_report.txt` for the WorldCover validation table

All figures are written to `figures/`. The notebook is the primary output artifact for the analysis.

---

## Dependency graph

```
GEE_SETUP.md
    └── 01_data_extraction/generate_csv_data.py
            └── data/gidabo_degradation_samples.csv
                    ├── 02_processing/cldi_processor.py (utility, no standalone output)
                    ├── 03_modeling/ml_classifier.py → models/rf_model.pkl
                    ├── 04_validation/validate_labels.py → data/label_validation_report.txt
                    └── notebooks/analysis.ipynb → figures/fig_*.png
```
