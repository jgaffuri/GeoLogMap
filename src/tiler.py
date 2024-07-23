import os
import fiona
from shapely.geometry import box #, shape, mapping
#from shapely.ops import transform
#from shapely import wkt
import geopandas as gpd
import json
import math
#import numpy as np

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import loadFeatures, spatialIndex


def resolutionise_tile(xmin, ymin, geometry, resolution):
    if geometry.is_empty:
        return geometry

#np.round(coords).astype(int)
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


def round_coords_to_int(geom):
    """Recursively round coordinates of a geometry to integers."""
    if isinstance(geom, dict):
        if 'coordinates' in geom:
            geom['coordinates'] = round_coords_to_int(geom['coordinates'])
        else:
            for key in geom:
                geom[key] = round_coords_to_int(geom[key])
    elif isinstance(geom, list):
        geom = [round_coords_to_int(sub_geom) for sub_geom in geom]
    elif isinstance(geom, float):
        geom = int(round(geom))
    return geom

def save_geojson_with_int_coords(gdf, output_geojson_path):
    """Save a GeoDataFrame to a GeoJSON file with integer coordinates."""
    geojson_dict = json.loads(gdf.to_json())
    
    for feature in geojson_dict['features']:
        feature['geometry'] = round_coords_to_int(feature['geometry'])
    
    with open(output_geojson_path, 'w') as f:
        json.dump(geojson_dict, f, separators=(',', ':'))





def tile(input_gpkg_path, output_folder, tile_size, resolution, origin_x = 0, origin_y = 0):
    # create output folder
    os.makedirs(output_folder, exist_ok=True)

    # data bounding box
    src = fiona.open(input_gpkg_path)
    minx, miny, maxx, maxy = src.bounds

    # tile
    mintx = int((minx-origin_x)/tile_size)
    maxtx = int((maxx-origin_x)/tile_size) +1
    minty = int((miny-origin_y)/tile_size)
    maxty = int((maxy-origin_y)/tile_size) +1

    # load data
    print("Load data from", input_gpkg_path)
    fs = loadFeatures(input_gpkg_path)
    print(len(fs))

    # make spatial index
    sindex = spatialIndex(fs)

    # load into a GeoDataFrame
    #gdf = gpd.read_file(input_gpkg_path)
    #print(len(gdf))

    for ti in range(mintx, maxtx):
        for tj in range(minty, maxty):

            # tile bounds
            tile_minx = origin_x + ti * tile_size
            tile_maxx = origin_x + (ti + 1) * tile_size
            tile_miny = origin_y + tj * tile_size
            tile_maxy = origin_y + (tj + 1) * tile_size
            tile_bounds = box(tile_minx, tile_miny, tile_maxx, tile_maxy)

            #get intersecting traces using index
            traces = sindex.intersection(tile_bounds)
            print(len(traces))

            # clip input to tile bounds
            #clipped_gdf = gdf[gdf.intersects(tile_bounds)].copy()
            #clipped_gdf['geometry'] = clipped_gdf['geometry'].intersection(tile_bounds)

            # skip if empty
            if(len(traces)==0): continue
            #if(len(clipped_gdf)==0): continue

            # round coordinates
            #clipped_gdf['geometry'] = clipped_gdf['geometry'].apply(lambda geom: resolutionise_tile(tile_minx, tile_miny, geom, resolution))

            # output file
            #output_file = os.path.join(output_folder, f"{ti}/{tj}.geojson")
            #os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # save
            #save_geojson_with_int_coords(clipped_gdf, output_file)
            #clipped_gdf.to_file(output_file, driver="GeoJSON")


    with open(os.path.join(output_folder, "metadata.json"), 'w') as json_file:
        # 
        metadata = {
            "origin_x" : origin_x,
            "origin_y" : origin_y,
            "tile_size" : tile_size,
            "resolution" : resolution
        }

        json.dump(metadata, json_file, indent=3)



#
tile("/home/juju/geodata/GPS/traces_3857.gpkg", "/home/juju/geodata/GPS/tiles_100km/", 100000, 1000, -1600000, 4100000)
