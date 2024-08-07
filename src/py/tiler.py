import os
import fiona
from shapely.geometry import box, mapping, LineString, MultiLineString, GeometryCollection

from shapely.ops import linemerge
import json
import math
from rtree import index


import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import load_features


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
    #elif geometry.geom_type == 'GeometryCollection':
    #    return type(geometry)([resolutionise_tile(xmin, ymin, geom, resolution) for geom in geometry.geoms])
    else:
        print(geometry)
        raise ValueError("Unhandled geometry type: {}".format(geometry.geom_type))


def extract_linear_components_as_lines(geometry):
    """
    Extracts and returns the linear components (LineString or MultiLineString) from a Shapely geometry.

    Parameters:
    - geometry: A Shapely geometry object which could be a mixture of Points and LineStrings.

    Returns:
    - A LineString if there's only one linear component, or a MultiLineString if there are multiple.
    """
    linear_components = []

    # Handle different geometry types
    if isinstance(geometry, LineString):
        linear_components.append(geometry)
    elif isinstance(geometry, MultiLineString):
        linear_components.extend(geometry.geoms)
    elif isinstance(geometry, GeometryCollection):
        for geom in geometry.geoms:
            if isinstance(geom, (LineString, MultiLineString)):
                linear_components.append(geom)

    # Return a single LineString or MultiLineString
    if len(linear_components) == 0:
        return None  # No linear components found
    elif len(linear_components) == 1:
        return linear_components[0]  # Return the single LineString or MultiLineString directly
    else:
        return MultiLineString(linear_components)  # Combine into a MultiLineString

# Example usage:
# mixed_g



def round_geojson_coordinates(geojson):
    if geojson['type'] == 'Point':
        geojson['coordinates'] = [int(round(coord)) for coord in geojson['coordinates']] 
    elif geojson['type'] == 'LineString':
        geojson['coordinates'] = [[int(round(x)), int(round(y))] for x, y in geojson['coordinates']]
    elif geojson['type'] == 'Polygon':
        geojson['coordinates'] = [[[int(round(x)), int(round(y))] for x, y in ring] for ring in geojson['coordinates']]
    elif geojson['type'] == 'MultiPoint':
        geojson['coordinates'] = [[int(round(x)), int(round(y))] for x, y in geojson['coordinates']]
    elif geojson['type'] == 'MultiLineString':
        geojson['coordinates'] = [[[int(round(x)), int(round(y))] for x, y in line] for line in geojson['coordinates']]
    elif geojson['type'] == 'MultiPolygon':
        geojson['coordinates'] = [[[[int(round(x)), int(round(y))] for x, y in ring] for ring in polygon] for polygon in geojson['coordinates']]
    return geojson




def tile_z(input_gpkg_path, output_folder, tile_size=256, resolution=250000, origin_x = 0, origin_y = 0, epsg = "3857"):

    # convert tile size from pix to meters
    tile_size *= resolution

    # create output folder
    os.makedirs(output_folder, exist_ok=True)

    # input data bounding box
    src = fiona.open(input_gpkg_path)
    minx, miny, maxx, maxy = src.bounds

    # tiles range
    mintx = int((minx-origin_x)/tile_size)
    maxtx = int((maxx-origin_x)/tile_size) +1
    minty = int((miny-origin_y)/tile_size)
    maxty = int((maxy-origin_y)/tile_size) +1

    # load input data
    print("Load data from", input_gpkg_path)
    fs = load_features(input_gpkg_path, layer="linestring") + load_features(input_gpkg_path, layer="point")
    print(len(fs))

    # make spatial index and dictionary
    idx = index.Index()
    feature_dict = {}
    for i,f in enumerate(fs):
        idx.insert(i, f['geometry'].bounds)
        feature_dict[i] = f

    # handle tiles
    for ti in range(mintx, maxtx):
        for tj in range(minty, maxty):

            # tile bounds
            tile_minx = origin_x + ti * tile_size
            tile_maxx = origin_x + (ti + 1) * tile_size
            tile_miny = origin_y + tj * tile_size
            tile_maxy = origin_y + (tj + 1) * tile_size
            tile_bounds = (tile_minx, tile_miny, tile_maxx, tile_maxy)
            tile_bounding_box = box(tile_minx, tile_miny, tile_maxx, tile_maxy)

            # get intersecting features using index
            iids = list(idx.intersection(tile_bounds))

            # skip if empty
            if(len(iids)==0): continue

            # handle every feature
            geojson_dict = {"type":"FeatureCollection", "features": [], "crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:EPSG::"+epsg}}}

            for iid in iids:
                feature = feature_dict[iid]

                #get geometry
                geom = feature["geometry"]

                # intersect geometry
                geom = geom.intersection(tile_bounding_box)
                if geom.is_empty: continue

                # TODO move that to simplify ?

                # simplify
                #geom = geom.simplify(simplify_f * resolution)
                #if geom.is_empty: continue

                #
                if geom.geom_type == "GeometryCollection":
                    geom = extract_linear_components_as_lines(geom)

                # resolutionise coordinates
                #print(geom.geom_type)
                geom = resolutionise_tile(tile_minx, tile_miny, geom, resolution)
                if geom.is_empty: continue

                # to remove duplicate points of linear features
                #geom = geom.simplify(0)
                #if geom.is_empty: continue

                # linemerge
                #try: geom = linemerge(geom)
                #except: pass
                #if geom.is_empty: continue

                # to clean polygons
                # geom = geom.buffer(0)

                #make geojson geometry
                gjgeom = mapping(geom)

                #int geometry
                gjgeom = round_geojson_coordinates(gjgeom)

                #make geojson feature
                gjf = { "type":"Feature", "id":str(iid), "properties":{}, "geometry": gjgeom }

                # copy feature properties
                for prop in feature:
                    if(prop == "geometry"): continue
                    gjf["properties"][prop] = feature[prop]

                #add
                geojson_dict['features'].append(gjf)

            # no feature
            if len(geojson_dict['features'])==0: continue

            # output file
            output_file = os.path.join(output_folder, f"{ti}/{tj}.geojson")
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # save
            with open(output_file, 'w') as f:
                json.dump(geojson_dict, f, separators=(',', ':'))



# for several zoom levels
def tile(input_gpkg_path_fun, output_folder,z_min = 1, z_max = 10, tile_size = 256, resolution_0 = 250000, origin_x = 0, origin_y = 0, epsg = "3857"):

    # create output folder
    os.makedirs(output_folder, exist_ok=True)

    # save metadata.json file
    with open(os.path.join(output_folder, "metadata.json"), 'w') as json_file:
        #
        metadata = {
            "origin_x" : origin_x,
            "origin_y" : origin_y,
            "tile_size" : tile_size,
            "resolution_0" : resolution_0,
            "z_min" : z_min,
            "z_max" : z_max
        }
        json.dump(metadata, json_file, indent=3)

    # tile for all zoom levels
    for z in range(z_min, z_max+1):
        print("Tiling - zoom level", z)
        d = math.pow(2, z)
        tile_z(input_gpkg_path_fun(z), output_folder+str(z)+"/", tile_size, resolution_0 / d, origin_x, origin_y, epsg)



#
tile(lambda z: "/home/juju/geodata/GPS/traces_"+str(z)+".gpkg", "/home/juju/geodata/GPS/tiled/", z_min=3, z_max=15, origin_x=-9000000, origin_y=-6000000)
