import os
import geopandas as gpd
from shapely.geometry import LineString
import gpxpy
import pandas as pd
from lxml import etree


def parse_gpx(file_path):
    traces = []
    with open(file_path, 'r') as gpx_file:
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
    return traces


def parse_tcx(file_path):
    traces = []
    with open(file_path, 'r') as tcx_file:
        tree = etree.parse(tcx_file)
        root = tree.getroot()
        xmlns = {'ns': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
        
        for activity in root.findall('ns:Activities/ns:Activity', xmlns):
            for lap in activity.findall('ns:Lap', xmlns):
                points = []
                times = []
                for track in lap.findall('ns:Track/ns:Trackpoint', xmlns):
                    time = track.find('ns:Time', xmlns).text
                    pos = track.find('ns:Position', xmlns)
                    if pos is not None:
                        lat = float(pos.find('ns:LatitudeDegrees', xmlns).text)
                        lon = float(pos.find('ns:LongitudeDegrees', xmlns).text)
                        points.append((lon, lat))
                        times.append(pd.to_datetime(time))
                if len(points) > 1:
                    line = LineString(points)
                    start_time = times[0]
                    end_time = times[-1]
                    traces.append({
                        'geometry': line,
                        'start_time': start_time,
                        'end_time': end_time
                    })
    return traces

def create_geopackage_from_gpx_tcx(folder_path, output_file):
    traces = []
    for file in os.listdir(folder_path):
        if file.endswith(".gpx"):
            traces.extend(parse_gpx(os.path.join(folder_path, file)))
        elif file.endswith(".tcx"):
            traces.extend(parse_tcx(os.path.join(folder_path, file)))

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(traces, crs="EPSG:4326")
    
    # Write the GeoDataFrame to a GeoPackage
    gdf.to_file(output_file, layer='gps_traces', driver='GPKG')


create_geopackage_from_gpx_tcx("/home/juju/geodata/GPS/traces_export_stava", "/home/juju/geodata/GPS/traces.gpkg")
