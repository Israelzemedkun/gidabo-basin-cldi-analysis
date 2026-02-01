import ee
ee.Authenticate()

# Initialize Earth Engine
ee.Initialize()

def calculate_indices(image):
    """
    Calculates NDVI and BSI for Landsat 8/9 imagery.
    """
    # Normalized Difference Vegetation Index (NDVI)
    ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI')
    
    # Bare Soil Index (BSI)
    # Formula: ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))
    bsi = image.expression(
        '((SWIR1 + RED) - (NIR + BLUE)) / ((SWIR1 + RED) + (NIR + BLUE))', {
            'SWIR1': image.select('B6'),
            'RED': image.select('B4'),
            'NIR': image.select('B5'),
            'BLUE': image.select('B2')
        }).rename('BSI')
    
    return image.addBands([ndvi, bsi])

print("Starter script initialized: Ready for Gidabo Basin processing.")
