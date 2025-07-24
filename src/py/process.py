


# convert new file into GPX - remove duplicates
convert_to_gpx("/home/juju/geodata/GPS/strava_export_2025_07_16","/home/juju/geodata/GPS/traces")

# GPX to GPKG
#create_geopackage_segments_from_gpx("/home/juju/geodata/GPS/traces", "/home/juju/geodata/GPS/traces_segments.gpkg")

# generalisation
#simplify_traces_z("/home/juju/geodata/GPS/traces.gpkg", "/home/juju/geodata/GPS/traces_", z_min=3, z_max=15, out_epsg = "3857")
#simplify_traces_segments_z("/home/juju/geodata/GPS/traces_segments.gpkg", "/home/juju/geodata/GPS/traces_segments_", z_min=3, z_max=15, out_epsg = "3857")

# tiling
#tile(lambda z: "/home/juju/geodata/GPS/traces_"+str(z)+".gpkg", "/home/juju/geodata/GPS/tiled/", z_min=3, z_max=15, origin_x=-9000000, origin_y=-6000000)

