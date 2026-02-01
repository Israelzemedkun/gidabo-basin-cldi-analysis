import ee
from aoi_utils import get_gidabo_basin

# Initialize with your Project ID
ee.Initialize(project='ee-my-israelzemedkungebre')

aoi = get_gidabo_basin()

def process_landsat_5(image):
    """Calculates NDVI and BSI for Year 2000 data."""
    ndvi = image.normalizedDifference(['B4', 'B3']).rename('NDVI_2000')
    bsi = image.expression('((B5 + B3) - (B4 + B1)) / ((B5 + B3) + (B4 + B1))', {
        'B5': image.select('B5'), 'B3': image.select('B3'),
        'B4': image.select('B4'), 'B1': image.select('B1')
    }).rename('BSI_2000')
    return image.addBands([ndvi, bsi])

def process_landsat_8(image):
    """Calculates NDVI and BSI for Year 2024 data."""
    ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI_2024')
    bsi = image.expression('((B6 + B4) - (B5 + B2)) / ((B6 + B4) + (B5 + B2))', {
        'B6': image.select('B6'), 'B4': image.select('B4'),
        'B5': image.select('B5'), 'B2': image.select('B2')
    }).rename('BSI_2024')
    return image.addBands([ndvi, bsi])

# Fetching the Data
pre_degradation = (ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")
                  .filterBounds(aoi).filterDate('2000-01-01', '2001-12-31')
                  .map(process_landsat_5).median().clip(aoi))

current_state = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                 .filterBounds(aoi).filterDate('2023-01-01', '2024-12-31')
                 .map(process_landsat_8).median().clip(aoi))

# Calculate Change (Simple Difference)
# A negative NDVI change or positive BSI change = Potential Degradation
ndvi_change = current_state.select('NDVI_2024').subtract(pre_degradation.select('NDVI_2000')).rename('NDVI_Trend')

print("Trend Analysis Ready. 25-year comparison generated.")

# Add this to the end of scripts/trend_analysis.py
task = ee.batch.Export.image.toDrive(
    image=ndvi_change,
    description='Gidabo_NDVI_Trend_2000_2024',
    scale=30,
    region=aoi,
    fileFormat='GeoTIFF'
)
task.start()
print("Export task started! Check your Google Drive in a few minutes.")