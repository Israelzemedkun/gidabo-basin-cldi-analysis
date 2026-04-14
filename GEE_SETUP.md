# Google Earth Engine Setup

This analysis retrieves Landsat surface reflectance data and ESA WorldCover tiles from Google Earth Engine (GEE) via the Python API. Complete the steps below before running any script in `scripts/01_data_extraction/` or `scripts/04_validation/`.

---

## 1. Create a Google Earth Engine account

1. Go to [https://earthengine.google.com](https://earthengine.google.com) and click **Get Started**
2. Sign in with a Google account
3. Select **Use without a Cloud project** for personal/academic use, or register a Google Cloud project if you need higher quotas

GEE access for non-commercial academic research is free.

---

## 2. Register a GEE Cloud project

The Python API (v0.1.370+) requires a Cloud project ID:

1. Go to [https://code.earthengine.google.com/register](https://code.earthengine.google.com/register)
2. Create or select a Google Cloud project
3. Enable the Earth Engine API for that project in the [Cloud Console](https://console.cloud.google.com/apis/library/earthengine.googleapis.com)
4. Note your **project ID** (e.g. `ee-yourname-projectname`) — you will need it below

---

## 3. Authenticate the Earth Engine Python client

In a terminal with your project's virtual environment activated:

```bash
earthengine authenticate
```

This opens a browser window. Sign in with the Google account registered for GEE and grant the requested permissions. Credentials are stored locally at `~/.config/earthengine/credentials`.

To verify authentication succeeded:

```bash
python -c "import ee; ee.Initialize(project='YOUR_PROJECT_ID'); print('GEE OK')"
```

Replace `YOUR_PROJECT_ID` with the project ID from Step 2. If you see `GEE OK`, you are ready to run the scripts.

---

## 4. Update the project ID in each script

All scripts that call `ee.Initialize()` are currently configured with the original developer's project ID:

```
ee-my-israelzemedkungebre
```

You must replace every occurrence with your own project ID before running. Affected files:

| File | Line |
|---|---|
| `scripts/01_data_extraction/generate_csv_data.py` | `ee.Initialize(project='ee-my-israelzemedkungebre')` |
| `scripts/01_data_extraction/extract_ethiopia_grid.py` | `ee.Initialize(project='ee-my-israelzemedkungebre')` |

To find all occurrences across the repo:

```bash
grep -r "ee-my-israelzemedkungebre" .
```

Replace with your project ID in each file. Example (Linux/macOS):

```bash
find . -name "*.py" -exec sed -i "s/ee-my-israelzemedkungebre/YOUR_PROJECT_ID/g" {} +
```

---

## 5. Required GEE datasets

The following public datasets must be accessible from your GEE project. All are freely available to any registered GEE user:

| Dataset | GEE Asset ID | Used in |
|---|---|---|
| Landsat 5 TM Surface Reflectance C2 T1 | `LANDSAT/LT05/C02/T1_L2` | `generate_csv_data.py` |
| Landsat 8 OLI Surface Reflectance C2 T1 | `LANDSAT/LC08/C02/T1_L2` | `generate_csv_data.py` |
| ESA WorldCover 2021 v200 | `ESA/WorldCover/v200` | `validate_labels.py` |
| CHIRPS Daily Precipitation | `UCSB-CHG/CHIRPS/DAILY` | `cldi_processor.py` (optional context) |
| SRTM Digital Elevation Model | `USGS/SRTMGL1_003` | exploratory only |
| OpenLandMap Soil Texture | `OpenLandMap/SOL/SOL_TEXTURE-CLASS_USDA-TT_M/v02` | exploratory only |

To verify access to a specific dataset:

```python
import ee
ee.Initialize(project='YOUR_PROJECT_ID')
img = ee.Image('USGS/SRTMGL1_003')
print(img.getInfo()['id'])  # should print the asset ID
```

---

## 6. Python package requirements

The GEE Python client and all other dependencies are listed in `requirements.txt`. Install them with:

```bash
pip install -r requirements.txt
```

The key GEE package is `earthengine-api`. The scripts were developed and tested with version `0.1.370+`.
