import os
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import transform
import pyproj
import gpxpy
from datetime import datetime
import math


def haversine(coord1, coord2):
    """Calculate the Haversine distance between two points in meters."""
    # Radius of the Earth in meters
    R = 6371000
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    
    # Compute differences
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance

def linestring_length_haversine(linestring):
    """Calculate the length of a Shapely LineString in meters using the Haversine formula."""
    total_length = 0
    coords = list(linestring.coords)
    
    for i in range(len(coords) - 1):
        total_length += haversine(coords[i], coords[i + 1])
    
    return total_length



def transform_geometry(geometry, source_crs, target_crs):
    """
    Transforms a Shapely geometry from the source CRS to the target CRS.

    Parameters:
    - geometry: Shapely geometry object (e.g., Point, LineString, Polygon)
    - source_crs: The EPSG code or proj string of the source CRS
    - target_crs: The EPSG code or proj string of the target CRS

    Returns:
    - Transformed geometry object in the target CRS
    """
    # Create a transformer object
    transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)

    # Define a transformation function using the transformer
    def transform_function(x, y):
        return transformer.transform(x, y)
    
    # Transform the geometry
    transformed_geometry = transform(transform_function, geometry)
    return transformed_geometry




def create_geopackage_from_gpx(folder_path, output_file):

    id = 1
    date_format = "%Y-%m-%d %H:%M:%S"

    files = os.listdir(folder_path)
    print(len(files),"files")

    traces = []
    for file in files:
        try:
            file_path = os.path.join(folder_path, file)
            with open(file_path, 'r') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
                for track in gpx.tracks:
                    for segment in track.segments:
                        if len(segment.points) <= 1: continue
                        points = [(point.longitude, point.latitude) for point in segment.points]
                        times = [point.time for point in segment.points]
                        line = LineString(points)
                        start_time = str(times[0]).replace("+00:00","")
                        end_time = str(times[-1]).replace("+00:00","")
                        length_m = round(linestring_length_haversine(line))
                        duration_s = round((datetime.strptime(end_time, date_format)-datetime.strptime(start_time, date_format)).total_seconds())
                        line = transform_geometry(line, "EPSG:4326", "EPSG:3857")
                        traces.append({
                            'geometry': line,
                            'identifier': str(id),
                            'length_m': length_m,
                            'duration_s': duration_s,
                            "speed_kmh": round(length_m/duration_s * 3.6)
                            'start_time': start_time,
                            'end_time': end_time
                        })
                        id += 1

        except Exception as e:
            print("Error when reading file: "+file)
            print(e)

    print(len(traces),"traces loaded")

    gdf = gpd.GeoDataFrame(traces, crs="EPSG:4326")
    gdf.to_file(output_file, layer='gps_traces', driver='GPKG')


create_geopackage_from_gpx("/home/juju/geodata/GPS/traces", "/home/juju/geodata/GPS/traces.gpkg")
