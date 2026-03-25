import ee
import pandas as pd
import os
from aoi_utils import get_gidabo_basin

# Initialize Earth Engine
try:
    ee.Initialize(project='ee-my-israelzemedkungebre')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='ee-my-israelzemedkungebre')

print("Fetching boundary...")
aoi = get_gidabo_basin()

def process_landsat_5(image):
    """Calculates NDVI and BSI for Year 2000 data."""
    ndvi = image.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI_2000')
    bsi = image.expression('((B5 + B3) - (B4 + B1)) / ((B5 + B3) + (B4 + B1))', {
        'B5': image.select('SR_B5'), 'B3': image.select('SR_B3'),
        'B4': image.select('SR_B4'), 'B1': image.select('SR_B1')
    }).rename('BSI_2000')
    return image.addBands([ndvi, bsi])

def process_landsat_8(image):
    """Calculates NDVI and BSI for Year 2024 data."""
    ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI_2024')
    bsi = image.expression('((B6 + B4) - (B5 + B2)) / ((B6 + B4) + (B5 + B2))', {
        'B6': image.select('SR_B6'), 'B4': image.select('SR_B4'),
        'B5': image.select('SR_B5'), 'B2': image.select('SR_B2')
    }).rename('BSI_2024')
    return image.addBands([ndvi, bsi])

print("Processing imagery...")
# Fetching the Data
pre_degradation = (ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")
                  .filterBounds(aoi).filterDate('2000-01-01', '2001-12-31')
                  .map(process_landsat_5).median().clip(aoi))

current_state = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                 .filterBounds(aoi).filterDate('2023-01-01', '2024-12-31')
                 .map(process_landsat_8).median().clip(aoi))

# Combine the bands into one image
combined_image = pre_degradation.select(['NDVI_2000', 'BSI_2000']).addBands(current_state.select(['NDVI_2024', 'BSI_2024']))

# Sample 500 random points within the basin
print("Sampling random points...")
samples = combined_image.sample(
    region=aoi,
    scale=30,      # 30m resolution like Landsat
    numPixels=500, # Generate 500 rows of data
    seed=42,       # For reproducibility
    geometries=True # Include lat/lon
)

# Extract data to a Python format
print("Formatting data...")
def get_props(feature):
    coords = ee.Feature(feature).geometry().coordinates()
    prop = ee.Feature(feature).toDictionary()
    prop = prop.set('longitude', coords.get(0)).set('latitude', coords.get(1))
    return ee.Feature(None, prop)

sampled_data = samples.map(get_props).getInfo()

# Convert list of dictionaries to Pandas DataFrame
features = [f['properties'] for f in sampled_data['features']]
df = pd.DataFrame(features)

# Clean up and add some synthetic categorical data to make visualizations more interesting
df = df.dropna()

# Add a "Zone" category based on latitude to allow for group comparisons (like boxplots)
lat_min = df['latitude'].min()
lat_max = df['latitude'].max()
lat_third = (lat_max - lat_min) / 3

def assign_zone(lat):
    if lat < lat_min + lat_third:
        return 'Southern Zone'
    elif lat < lat_min + (2 * lat_third):
        return 'Central Zone'
    else:
        return 'Northern Zone'

df['Zone'] = df['latitude'].apply(assign_zone)

# Calculate change to use as a single variable
df['NDVI_Change'] = df['NDVI_2024'] - df['NDVI_2000']
df['Degradation_Status'] = df['NDVI_Change'].apply(lambda x: 'Degraded' if x < -0.05 else ('Improved' if x > 0.05 else 'Stable'))


# Save to data folder
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
os.makedirs(data_dir, exist_ok=True)
csv_path = os.path.join(data_dir, 'gidabo_degradation_samples.csv')
df.to_csv(csv_path, index=False)

print(f"Success! Saved sample dataset to {csv_path}")
print(f"Generated {len(df)} rows with columns: {', '.join(df.columns)}")
