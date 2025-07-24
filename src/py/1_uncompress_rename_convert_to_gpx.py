import os
import gpxpy
import gpxpy.gpx
import pandas as pd
from lxml import etree
from fitparse import FitFile, FitParseError
import shutil
import gzip


def uncompress_gz_files(folder_path):
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"The folder {folder_path} does not exist.")
    
    files = os.listdir(folder_path)
    gz_files = [file for file in files if file.endswith('.gz')]
    
    for gz_file in gz_files:
        gz_file_path = os.path.join(folder_path, gz_file)
        uncompressed_file_path = os.path.join(folder_path, gz_file[:-3])

        with gzip.open(gz_file_path, 'rb') as f_in:
            with open(uncompressed_file_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        os.remove(gz_file_path)
        print(f"Uncompressed and deleted {gz_file_path}")


def get_start_time_from_gpx(file_path):
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        for track in gpx.tracks:
            for segment in track.segments:
                if len(segment.points) > 0:
                    return segment.points[0].time
    return None

def get_start_time_from_tcx(file_path):
    with open(file_path, 'rb') as tcx_file:
        content = tcx_file.read().strip()
        tree = etree.fromstring(content)
        xmlns = {'ns': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
        time_element = tree.find('.//ns:Track/ns:Trackpoint/ns:Time', namespaces=xmlns)
        if time_element is not None:
            return pd.to_datetime(time_element.text)
    return None

def get_start_time_from_fit(file_path):
    try:
        fitfile = FitFile(file_path)
        for record in fitfile.get_messages('record'):
            for record_data in record:
                if record_data.name == 'timestamp' and record_data.value is not None:
                    return pd.to_datetime(record_data.value)
    except FitParseError as e:
        print(f"Error parsing FIT file {file_path}: {e}")
    return None





def rename_files_in_folder(folder_path):
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        start_time = None

        if file.endswith(".gpx"):
            start_time = get_start_time_from_gpx(file_path)
        elif file.endswith(".tcx"):
            start_time = get_start_time_from_tcx(file_path)
        elif file.endswith(".fit"):
            start_time = get_start_time_from_fit(file_path)

        if start_time:
            new_file_name = start_time.strftime(f"%Y-%m-%d_%H-%M-%S.{file.split('.')[-1]}")
            new_file_path = os.path.join(folder_path, new_file_name)
            shutil.move(file_path, new_file_path)
            #print(f"Renamed {file} to {new_file_name}")



def convert_tcx_to_gpx(tcx_file_path):
    with open(tcx_file_path, 'rb') as tcx_file:
        content = tcx_file.read().strip()
        tree = etree.fromstring(content)
        xmlns = {'ns': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
        
        gpx = gpxpy.gpx.GPX()
        for activity in tree.findall('.//ns:Activity', namespaces=xmlns):
            for lap in activity.findall('ns:Lap', namespaces=xmlns):
                track = gpxpy.gpx.GPXTrack()
                gpx.tracks.append(track)
                segment = gpxpy.gpx.GPXTrackSegment()
                track.segments.append(segment)
                
                for trackpoint in lap.findall('ns:Track/ns:Trackpoint', namespaces=xmlns):
                    time = trackpoint.find('ns:Time', namespaces=xmlns).text
                    pos = trackpoint.find('ns:Position', namespaces=xmlns)
                    if pos is not None:
                        lat = float(pos.find('ns:LatitudeDegrees', namespaces=xmlns).text)
                        lon = float(pos.find('ns:LongitudeDegrees', namespaces=xmlns).text)
                        point = gpxpy.gpx.GPXTrackPoint(latitude=lat, longitude=lon, time=pd.to_datetime(time))
                        segment.points.append(point)
    
    return gpx

def convert_fit_to_gpx(fit_file_path):
    fitfile = FitFile(fit_file_path)
    gpx = gpxpy.gpx.GPX()
    segment = gpxpy.gpx.GPXTrackSegment()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    track.segments.append(segment)

    for record in fitfile.get_messages('record'):
        lat = None
        lon = None
        time = None
        for record_data in record:
            if record_data.name == 'position_lat' and record_data.value is not None:
                lat = record_data.value * (180 / 2**31)  # Convert semicircles to degrees
            elif record_data.name == 'position_long' and record_data.value is not None:
                lon = record_data.value * (180 / 2**31)  # Convert semicircles to degrees
            elif record_data.name == 'timestamp' and record_data.value is not None:
                time = pd.to_datetime(record_data.value)

        if lat is not None and lon is not None and time is not None:
            point = gpxpy.gpx.GPXTrackPoint(latitude=lat, longitude=lon, time=time)
            segment.points.append(point)
    
    return gpx



def convert_to_gpx(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for file in os.listdir(input_folder):
        try:
            input_file_path = os.path.join(input_folder, file)
            start_time = None
            gpx = None

            if file.endswith(".gpx"):
                start_time = get_start_time_from_gpx(input_file_path)
                with open(input_file_path, 'r') as gpx_file:
                    gpx = gpxpy.parse(gpx_file)
            elif file.endswith(".tcx"):
                start_time = get_start_time_from_tcx(input_file_path)
                gpx = convert_tcx_to_gpx(input_file_path)
            elif file.endswith(".fit"):
                start_time = get_start_time_from_fit(input_file_path)
                gpx = convert_fit_to_gpx(input_file_path)

            if start_time and gpx:
                new_file_name = start_time.strftime("%Y-%m-%d_%H-%M-%S.gpx")
                new_file_path = os.path.join(output_folder, new_file_name)
                with open(new_file_path, 'w') as new_gpx_file:
                    new_gpx_file.write(gpx.to_xml())
                #print(f"Processed {file} and saved as {new_file_name}")

        except Exception as e:
            print("Error when dealing with file: "+file)
            print(e)

