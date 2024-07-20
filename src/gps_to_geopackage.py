import os
import geopandas as gpd
from shapely.geometry import LineString
import gpxpy
import pandas as pd

def create_geopackage_from_gpx(folder_path, output_file):
    traces = []
    for file in os.listdir(folder_path):
        if not file.endswith(".gpx"): continue
        print(file)
        with open(os.path.join(folder_path, file), 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            for track in gpx.tracks:
                for segment in track.segments:
                    if len(segment.points) > 1:
                        points = [(point.longitude, point.latitude) for point in segment.points]
                        times = [point.time for point in segment.points]
                        line = LineString(points)
                        start_time = times[0]
                        end_time = times[-1]
                        traces.append({
                            'geometry': line,
                            'start_time': start_time,
                            'end_time': end_time
                        })

    gdf = gpd.GeoDataFrame(traces, crs="EPSG:4326")
    gdf.to_file(output_file, layer='gps_traces', driver='GPKG')



create_geopackage_from_gpx("/home/juju/geodata/GPS/traces_export_stava", "/home/juju/geodata/GPS/traces.gpkg")
