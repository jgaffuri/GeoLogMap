
from uncompress_rename_convert_to_gpx import uncompress_gz_files, convert_to_gpx
from gpx_to_geopackage import create_geopackage_from_gpx, create_geopackage_segments_from_gpx
from generalisation import simplify_traces_z
from tiler import tile

folder = "/home/juju/geodata/GPS/"
new_data_folder = "/home/juju/geodata/GPS/strava_export_2025_07_24/"
gpx_folder = folder + "traces/"

# convert new file into GPX - remove duplicates
#uncompress_gz_files(new_data_folder)
#convert_to_gpx(new_data_folder, gpx_folder)

# GPX to GPKG
create_geopackage_from_gpx(gpx_folder, folder + "traces.gpkg")
#create_geopackage_segments_from_gpx(gpx_folder, folder + "traces_segments.gpkg")

# generalisation
simplify_traces_z(folder + "traces.gpkg", folder + "traces_", z_min=3, z_max=15, out_epsg = "3857")
#simplify_traces_segments_z(folder + "traces_segments.gpkg", folder + "traces_segments_", z_min=3, z_max=15, out_epsg = "3857")

# tiling
tile(lambda z: folder + "traces_"+str(z)+".gpkg", folder + "tiled/", z_min=3, z_max=15, origin_x=-9000000, origin_y=-6000000)
