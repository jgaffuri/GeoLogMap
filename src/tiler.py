import os
import fiona
from shapely.geometry import box, shape, mapping
from shapely.ops import transform
from shapely import wkt
import geopandas as gpd
import json
import math


def resolutionise_tile(xmin, ymin, geometry, resolution):
    if geometry.is_empty:
        return geometry

    def _reso_x(x):
        return int(math.floor((x-xmin)/resolution))
    def _reso_y(y):
        return int(math.floor((y-ymin)/resolution))

    def _resos(coords):
        return tuple([_reso_x(coords[0]), _reso_y(coords[1])])

    if geometry.geom_type == 'Point':
        return type(geometry)(*map(_resos, [geometry.coords[0]]))
    elif geometry.geom_type in ['LineString', 'LinearRing']:
        return type(geometry)(list(map(_resos, geometry.coords)))
    elif geometry.geom_type == 'Polygon':
        exterior = list(map(_resos, geometry.exterior.coords))
        interiors = [list(map(_resos, ring.coords)) for ring in geometry.interiors]
        return type(geometry)(exterior, interiors)
    elif geometry.geom_type == 'MultiPoint':
        return type(geometry)([type(geometry.geoms[0])(list(map(_resos, geom.coords))) for geom in geometry.geoms])
    elif geometry.geom_type == 'MultiLineString':
        return type(geometry)([type(geometry.geoms[0])(list(map(_resos, geom.coords))) for geom in geometry.geoms])
    elif geometry.geom_type == 'MultiPolygon':
        return type(geometry)([
            type(geometry.geoms[0])(
                list(map(_resos, geom.exterior.coords)),
                [list(map(_resos, ring.coords)) for ring in geom.interiors]
            )
            for geom in geometry.geoms
        ])
    else:
        raise ValueError("Unhandled geometry type: {}".format(geometry.geom_type))






def tile(input_gpkg_path, output_folder, tile_size, resolution, origin_x = 0, origin_y = 0):
    # create output folder
    os.makedirs(output_folder, exist_ok=True)

    # Open the input GeoPackage file
    with fiona.open(input_gpkg_path) as src:

        # data bounding box
        minx, miny, maxx, maxy = src.bounds

        # tile
        mintx = int((minx-origin_x)/tile_size)
        maxtx = int((maxx-origin_x)/tile_size) +1
        minty = int((miny-origin_y)/tile_size)
        maxty = int((maxy-origin_y)/tile_size) +1

        # load into a GeoDataFrame
        print("Load data from", input_gpkg_path)
        gdf = gpd.read_file(input_gpkg_path)
        print(len(gdf))

        for ti in range(mintx, maxtx):
            for tj in range(minty, maxty):

                # tile bounds
                tile_minx = origin_x + ti * tile_size
                tile_maxx = origin_x + (ti + 1) * tile_size
                tile_miny = origin_y + tj * tile_size
                tile_maxy = origin_y + (tj + 1) * tile_size
                tile_bounds = box(tile_minx, tile_miny, tile_maxx, tile_maxy)

                # clip input to tile bounds
                clipped_gdf = gdf[gdf.intersects(tile_bounds)].copy()
                clipped_gdf['geometry'] = clipped_gdf['geometry'].intersection(tile_bounds)

                # skip if empty
                if(len(clipped_gdf)==0): continue

                # round coordinates
                clipped_gdf['geometry'] = clipped_gdf['geometry'].apply(lambda geom: resolutionise_tile(tile_minx, tile_miny, geom, resolution))

                # output file
                output_file = os.path.join(output_folder, f"{ti}/{tj}.geojson")
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # save
                clipped_gdf.to_file(output_file, driver="GeoJSON")


    with open(os.path.join(output_folder, "metadata.json"), 'w') as json_file:
        # 
        metadata = {
            "origin_x" : origin_x,
            "origin_y" : origin_y,
            "tile_size" : tile_size
        }

        json.dump(metadata, json_file, indent=3)



#
tile("/home/juju/geodata/GPS/traces_3857.gpkg", "/home/juju/geodata/GPS/tiles_100km/", 100000, 1000, -1600000, 4100000)
