# 01_data_extraction

Scripts for pulling surface reflectance data from Google Earth Engine and assembling the analysis dataset.

## Scripts (run in this order)

### 1. `aoi_utils.py`
Helper module — not run directly. Defines `get_gidabo_basin()`, which queries the WWF HydroSHEDS Level 12 basin dataset to return the Gidabo River Basin geometry as a GEE `Geometry` object. Imported by the other scripts in this folder.

### 2. `generate_csv_data.py`
**Run this first.** Authenticates to GEE, samples 500 random pixels within the Gidabo Basin boundary, computes NDVI, BSI, and SI for Landsat 5 (year 2000) and Landsat 8 (year 2024), and writes `data/gidabo_degradation_samples.csv`.

```bash
cd scripts/01_data_extraction
python generate_csv_data.py
```

Requires: GEE authentication (`earthengine authenticate`) and a valid GEE project ID in place of `ee-my-israelzemedkungebre`.

### 3. `extract_ethiopia_grid.py`
Optional grid-based extraction across all of Ethiopia (0.25° spacing). Used for exploratory country-wide context, not required for the main Gidabo analysis. Outputs JSON tiles to a local directory.

```bash
python extract_ethiopia_grid.py
```

## Output

`data/gidabo_degradation_samples.csv` — 500 rows × columns: `NDVI_2000`, `NDVI_2024`, `BSI_2000`, `BSI_2024`, `SI_2000`, `SI_2024`, `NDVI_Change`, `BSI_Change`, `SI_Change`, `Zone`, `lon`, `lat`.
