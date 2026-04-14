import ee
from aoi_utils import get_gidabo_basin

# Initialize Earth Engine
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

def get_cldi_indices(image):
    """
    Computes indices for Landsat 8/9 Surface Reflectance.
    """
    # 1. NDVI (Vegetation Health)
    ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI')
    
    # 2. BSI (Bare Soil Index)
    bsi = image.expression(
        '((B6 + B4) - (B5 + B2)) / ((B6 + B4) + (B5 + B2))', {
            'B6': image.select('B6'), # SWIR 1
            'B4': image.select('B4'), # Red
            'B5': image.select('B5'), # NIR
            'B2': image.select('B2')  # Blue
        }).rename('BSI')
    
    # 3. SI (Salinity Index) - Using Green and Red bands
    si = image.expression(
        'sqrt(B3 * B4)', {
            'B3': image.select('B3'), # Green
            'B4': image.select('B4')  # Red
        }).rename('SI')
    
    return image.addBands([ndvi, bsi, si])

# Execution logic
aoi = get_gidabo_basin()

# Load 2024 Landsat 8 Data for the Gidabo Basin
collection = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
              .filterBounds(aoi)
              .filterDate('2024-01-01', '2024-12-31')
              .filter(ee.Filter.lt('CLOUD_COVER', 20))
              .map(get_cldi_indices))

# Create a median composite
composite = collection.median().clip(aoi)

print("CLDI Composite for 2024 generated successfully for the Gidabo Basin.")
