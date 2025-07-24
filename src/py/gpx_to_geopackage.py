import os
import geopandas as gpd
from shapely.geometry import LineString
from shapely.ops import transform
import pyproj
import gpxpy
from datetime import datetime
import math
#from geopy.distance import geodesic

date_format = "%Y-%m-%d %H:%M:%S"

'''
def haversine_distance(point1, point2):
    """Calculate the Haversine distance between two (lat, lon) points."""
    return geodesic(point1, point2).meters
'''

#TODO do not use ?
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




def create_geopackage_from_gpx(folder_path, output_file, out_epsg = "3857"):

    id = 1

    files = os.listdir(folder_path)
    print(len(files),"files")

    # TODO use gdf.to_crs instead ?
    projector = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:"+out_epsg, always_xy=True).transform

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
                        line = transform(projector, line)
                        traces.append({
                            'geometry': line,
                            'identifier': str(id),
                            'length_m': length_m,
                            'duration_s': duration_s,
                            "speed_kmh": round(length_m/duration_s * 3.6),
                            'start_time': start_time,
                            'end_time': end_time
                        })
                        id += 1

        except Exception as e:
            print("Error when reading file: "+file)
            print(e)

    print(len(traces),"traces loaded")

    gdf = gpd.GeoDataFrame(traces, crs="EPSG:"+out_epsg)
    gdf.to_file(output_file, layer='gps_traces', driver='GPKG')



def create_geopackage_segments_from_gpx(folder_path, output_file, out_epsg="3857"):
    """Convert GPX files in a folder to a GeoPackage containing segments with attributes."""

    segments_data = []
    id = 1

    files = os.listdir(folder_path)
    print(len(files),"files")

    # Iterate over all GPX files in the folder
    for file in files:
        if not file.endswith(".gpx"): continue

        gpx_path = os.path.join(folder_path, file)
        print(file)

        try:

            # Parse the GPX file
            with open(gpx_path, 'r') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
                
                # Iterate over all tracks and segments in the GPX file
                for track in gpx.tracks:
                    for segment in track.segments:
                        points = segment.points
                        if len(points) <= 1: continue

                        p0 = points[0]
                        for i in range(1,len(points)):
                            p1 = points[i]

                            #make segment p0,p1
                            t0 = p0.time
                            t1 = p1.time
                            start_time = str(t0).replace("+00:00","")
                            end_time = str(t1).replace("+00:00","")
                            duration_s = (datetime.strptime(end_time, date_format)-datetime.strptime(start_time, date_format)).total_seconds()
                            length_m = haversine([p0.latitude, p0.longitude],[p1.latitude, p1.longitude])
                            speed = 3.6 * length_m / duration_s if duration_s > 0 else 0
                            line = LineString([(point.longitude, point.latitude) for point in [p0,p1]])

                            # Store segment data
                            segments_data.append({
                                'geometry': line,
                                'identifier': str(id),
                                'start_time': str(start_time).replace("+00:00",""),
                                'end_time': str(end_time).replace("+00:00",""),
                                'duration_s': round(duration_s),
                                'length_m': round(length_m),
                                'speed': round(speed)
                            })
                            id+=1

                            p0 = p1

                        #points = [(point.longitude, point.latitude) for point in segment.points]
                        #times = [point.time for point in segment.points]

                        # Extract coordinates and times
                        #coords = [(point.longitude, point.latitude) for point in points]
                        #times = [point.time for point in points]
                        
                        # Calculate segment attributes
                        #length_m = sum(haversine_distance(coords[i], coords[i+1]) for i in range(len(coords)-1))
                        #speed = (length_m / 1000) / (duration_s / 3600) if duration_s > 0 else 0

                        # Create a LineString geometry
                        #line = LineString(coords)
                        
        except Exception as e:
            print("Error when reading file: "+file)
            print(e)

    print(len(segments_data),"segments loaded")

    gdf = gpd.GeoDataFrame(segments_data, crs="EPSG:4326")
    gdf = gdf.to_crs(epsg=int(out_epsg))
    gdf.to_file(output_file, layer='gps_segments', driver='GPKG')



