import os
import fiona
from shapely.geometry import box, shape
from shapely.ops import transform
import geopandas as gpd

def tile_geopackage(input_gpkg_path, output_folder, tile_size):
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Open the input GeoPackage file
    with fiona.open(input_gpkg_path) as src:
        # Get the bounding box of the entire layer
        minx, miny, maxx, maxy = src.bounds

        # Generate tiles
        nbx = int((maxx - minx) / tile_size) + 1
        nby = int((maxy - miny) / tile_size) + 1

        # Read the entire GeoPackage into a GeoDataFrame
        gdf = gpd.read_file(input_gpkg_path)

        for i in range(nbx):
            for j in range(nby):
                # Define the bounds of the current tile
                tile_minx = minx + i * tile_size
                tile_miny = miny + j * tile_size
                tile_maxx = minx + (i + 1) * tile_size
                tile_maxy = miny + (j + 1) * tile_size
                tile_bounds = box(tile_minx, tile_miny, tile_maxx, tile_maxy)

                # Clip the input data to the current tile bounds
                clipped_gdf = gdf[gdf.intersects(tile_bounds)].copy()
                clipped_gdf['geometry'] = clipped_gdf['geometry'].intersection(tile_bounds)

                # Define the output file path
                output_file = os.path.join(output_folder, f"{i}/{j}.geojson")
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # Save the clipped GeoDataFrame to a GeoJSON file
                clipped_gdf.to_file(output_file, driver="GeoJSON")

# Example usage
input_gpkg_path = 'path/to/your/input.gpkg'
output_folder = 'path/to/output/folder'
tile_size = 1000  # Tile size in meters
tile_geopackage(input_gpkg_path, output_folder, tile_size)
