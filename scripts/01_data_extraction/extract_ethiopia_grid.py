import ee
import json
import time
import math
import os
from datetime import datetime

# Initialize GEE
try:
    ee.Initialize(project='ee-my-israelzemedkungebre')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='ee-my-israelzemedkungebre')

# Grid parameters - Ethiopia bounding box
LAT_MIN, LAT_MAX = 3.4, 15.0
LON_MIN, LON_MAX = 33.0, 48.0
STEP = 0.25  # 0.25 degree spacing (~28km) - faster than 0.1
BATCH_SIZE = 50

# Build grid points
lats = [round(LAT_MIN + i * STEP, 2) for i in range(int((LAT_MAX - LAT_MIN) / STEP) + 1)]
lons = [round(LON_MIN + i * STEP, 2) for i in range(int((LON_MAX - LON_MIN) / STEP) + 1)]
all_points = [(lat, lon) for lat in lats for lon in lons]
total = len(all_points)
print(f"Total grid points: {total}")

# GEE datasets
chirps = (ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
          .filterDate('2015-01-01', '2024-12-31')
          .select('precipitation')
          .sum()
          .divide(10)
          .rename('rainfall'))

srtm = ee.Image('USGS/SRTMGL1_003')
slope = ee.Terrain.slope(srtm).rename('slope')

def mask_l8(image):
    qa = image.select('QA_PIXEL')
    mask = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
    return image.updateMask(mask)

landsat = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
           .filterDate('2020-01-01', '2024-12-31')
           .map(mask_l8))

ndvi = (landsat.map(lambda img: img
        .normalizedDifference(['SR_B5', 'SR_B4'])
        .rename('ndvi'))
        .mean())

soil = (ee.Image('OpenLandMap/SOL/SOL_TEXTURE-CLASS_USDA-TT_M/v02')
        .select('b0')
        .rename('soil_class'))

combined = chirps.addBands(slope).addBands(ndvi).addBands(soil)

# RUSLE factor computation
def compute_rusle(rainfall, slope_deg, ndvi_val, soil_class):
    R = round(0.0483 * (rainfall ** 1.61), 2) if rainfall else None
    if slope_deg is None:
        LS = None
    elif slope_deg < 2: LS = 0.5
    elif slope_deg < 5: LS = 1.5
    elif slope_deg < 10: LS = 3.5
    elif slope_deg < 20: LS = 7.0
    else: LS = 15.0
    if ndvi_val is None:
        C = None
    elif ndvi_val > 0.6: C = 0.02
    elif ndvi_val > 0.4: C = 0.08
    elif ndvi_val > 0.2: C = 0.20
    else: C = 0.45
    if soil_class is None:
        K = None
    elif soil_class <= 3: K = 0.10
    elif soil_class <= 6: K = 0.25
    elif soil_class <= 9: K = 0.35
    else: K = 0.40
    return R, LS, C, K

def sample_batch(points):
    features = [ee.Feature(ee.Geometry.Point([lon, lat]), {'lat': lat, 'lon': lon})
                for lat, lon in points]
    fc = ee.FeatureCollection(features)
    sampled = combined.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=1000
    )
    return sampled.getInfo()

# Process in batches
results = []
start_time = time.time()
processed = 0

for i in range(0, total, BATCH_SIZE):
    batch = all_points[i:i + BATCH_SIZE]
    for attempt in range(3):
        try:
            data = sample_batch(batch)
            for feat in data['features']:
                props = feat['properties']
                rainfall = props.get('rainfall')
                slope_val = props.get('slope')
                ndvi_val = props.get('ndvi')
                soil_val = props.get('soil_class')
                if rainfall is None or slope_val is None:
                    continue
                R, LS, C, K = compute_rusle(rainfall, slope_val, ndvi_val, soil_val)
                results.append({
                    'lat': round(props['lat'], 2),
                    'lon': round(props['lon'], 2),
                    'rainfall': round(rainfall, 1) if rainfall else None,
                    'slope': round(slope_val, 2) if slope_val else None,
                    'ndvi': round(ndvi_val, 3) if ndvi_val else None,
                    'soil_k': soil_val,
                    'R': R, 'LS': LS, 'C': C, 'K': K
                })
            break
        except Exception as e:
            wait = 15 * (attempt + 1)
            print(f"  Retry {attempt+1}/3 after {wait}s: {e}")
            time.sleep(wait)
    processed += len(batch)
    if processed % 50 == 0 or i == 0:
        elapsed = time.time() - start_time
        eta = (elapsed / processed) * (total - processed) if processed > 0 else 0
        print(f"[{processed}/{total}] points processed | {len(results)} valid | elapsed: {elapsed:.0f}s | ETA: {eta:.0f}s")
    time.sleep(0.3)

# Save output
out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'gidabo-monitor', 'public', 'data'))
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'ethiopia_grid.json')

output = {
    'metadata': {
        'resolution_deg': STEP,
        'bbox': [LAT_MIN, LON_MIN, LAT_MAX, LON_MAX],
        'sources': 'CHIRPS 2015-2024, SRTM, Landsat 8 2020-2024, OpenLandMap',
        'generated': str(datetime.now().year),
        'total_points': len(results)
    },
    'points': results
}

with open(out_path, 'w') as f:
    json.dump(output, f, separators=(',', ':'))

print(f"\nDone! {len(results)} points saved to {out_path}")
print(f"File size: {os.path.getsize(out_path) / 1024:.1f} KB")
