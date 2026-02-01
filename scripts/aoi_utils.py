import ee

def get_gidabo_basin():
    """
    Returns the geometry of the Gidabo River Basin 
    using the WWF HydroSHEDS dataset.
    """
    # Level 12 provides the finest detail for sub-basins
    basins = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_12")
    
    # Coordinates for the heart of the Gidabo watershed (~6.6N, 38.2E)
    target_point = ee.Geometry.Point([38.2, 6.6])
    
    # Filter the collection to find the basin containing this point
    basin = basins.filterBounds(target_point).first()
    
    return basin.geometry()

if __name__ == "__main__":
    # Test block to ensure it works when run directly
    try:
        ee.Initialize()
        geom = get_gidabo_basin()
        print("Success: Gidabo Basin geometry retrieved.")
    except Exception as e:
        print(f"Error: {e}. Did you run 'earthengine authenticate'?")