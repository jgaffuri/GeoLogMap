import os
import geopandas as gpd
from shapely.geometry import LineString
import gpxpy
import pandas as pd
from lxml import etree
from fitparse import FitFile


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
    with open(file_path, 'rb') as tcx_file:
        content = tcx_file.read()
        content = content.strip()
        
        tree = etree.fromstring(content)
        xmlns = {'ns': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
        
        for activity in tree.findall('.//ns:Activity', namespaces=xmlns):
            for lap in activity.findall('ns:Lap', namespaces=xmlns):
                points = []
                times = []
                for track in lap.findall('ns:Track/ns:Trackpoint', namespaces=xmlns):
                    time = track.find('ns:Time', namespaces=xmlns).text
                    pos = track.find('ns:Position', namespaces=xmlns)
                    if pos is not None:
                        lat = float(pos.find('ns:LatitudeDegrees', namespaces=xmlns).text)
                        lon = float(pos.find('ns:LongitudeDegrees', namespaces=xmlns).text)
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





def parse_fit(file_path):
    traces = []
    fitfile = FitFile(file_path)
    points = []
    times = []
    for record in fitfile.get_messages('record'):
        # Get the data from the record
        lat = None
        lon = None
        time = None
        for record_data in record:
            if record_data.name == 'position_lat' and record_data.value is not None:
                lat = record_data.value * (180 / 2**31)  # Convert semicircles to degrees
            elif record_data.name == 'position_long' and record_data.value is not None:
                lon = record_data.value * (180 / 2**31)  # Convert semicircles to degrees
            elif record_data.name == 'timestamp' and record_data.value is not None:
                time = record_data.value
        
        if lat is not None and lon is not None and time is not None:
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




def create_geopackage(folder_path, output_file):

    files = os.listdir(folder_path)
    print(len(files),"files")

    traces = []
    for file in files:
        try:
            if file.endswith(".gpx"):
                traces.extend(parse_gpx(os.path.join(folder_path, file)))
            elif file.endswith(".tcx"):
                traces.extend(parse_tcx(os.path.join(folder_path, file)))
            elif file.endswith(".fit"):
                traces.extend(parse_fit(os.path.join(folder_path, file)))
        except Exception as e:
            print("Error when reading file: "+file)
            print(e)

    gdf = gpd.GeoDataFrame(traces, crs="EPSG:4326")
    gdf.to_file(output_file, layer='gps_traces', driver='GPKG')


create_geopackage("/home/juju/geodata/GPS/traces_gpx", "/home/juju/geodata/GPS/traces.gpkg")
