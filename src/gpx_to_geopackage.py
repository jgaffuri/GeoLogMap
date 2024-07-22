import os
import geopandas as gpd
from shapely.geometry import LineString
import gpxpy


def create_geopackage_from_gpx(folder_path, output_file):

    id = 1
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
                        start_time = times[0]
                        end_time = times[-1]
                        traces.append({
                            'geometry': line,
                            'id_': str(id),
                            'start_time': str(start_time).replace("+00:00",""),
                            'end_time': str(end_time).replace("+00:00","")
                        })
                        id += 1

                        #print(str(start_time).replace("+00:00",""))
                        #print(str(end_time).replace("+00:00",""))

        except Exception as e:
            print("Error when reading file: "+file)
            print(e)

    print(len(traces),"traces loaded")

    gdf = gpd.GeoDataFrame(traces, crs="EPSG:4326")
    gdf.to_file(output_file, layer='gps_traces', driver='GPKG')


create_geopackage_from_gpx("/home/juju/geodata/GPS/traces", "/home/juju/geodata/GPS/traces.gpkg")
