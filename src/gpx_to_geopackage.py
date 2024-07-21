import os
import geopandas as gpd
from shapely.geometry import LineString
import gpxpy




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





def create_geopackage(folder_path, output_file):

    files = os.listdir(folder_path)
    print(len(files),"files")

    traces = []
    for file in files:
        try:
            traces.extend(parse_gpx(os.path.join(folder_path, file)))
        except Exception as e:
            print("Error when reading file: "+file)
            print(e)

    print(len(traces),"traces loaded")

    gdf = gpd.GeoDataFrame(traces, crs="EPSG:4326")
    gdf.to_file(output_file, layer='gps_traces', driver='GPKG')


create_geopackage("/home/juju/geodata/GPS/traces", "/home/juju/geodata/GPS/traces.gpkg")
