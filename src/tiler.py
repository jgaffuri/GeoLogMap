import os
import fiona
from shapely.geometry import box, mapping #, shape, mapping
from shapely.ops import linemerge
import json
import math
from rtree import index


import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import loadFeatures


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




def tile_z(input_gpkg_path, output_folder, tile_size, resolution, origin_x = 0, origin_y = 0, simplify_f = 0, epsg = "3857"):

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
    fs = loadFeatures(input_gpkg_path)
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
                geom = geom.simplify(simplify_f * resolution)
                if geom.is_empty: continue

                # resolutionise coordinates
                geom = resolutionise_tile(tile_minx, tile_miny, geom, resolution)
                if geom.is_empty: continue

                # to remove duplicate points of linear features
                geom = geom.simplify(0)
                if geom.is_empty: continue

                # linemerge
                try: geom = linemerge(geom)
                except: pass
                if geom.is_empty: continue

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
def tile(input_gpkg_path_fun, output_folder,z_min = 1, z_max=10, tile_size_0 = 100000000, resolution_0 = 300000, origin_x = 0, origin_y = 0, epsg = "3857"):

    # create output folder
    os.makedirs(output_folder, exist_ok=True)

    # save metadata.json file
    with open(os.path.join(output_folder, "metadata.json"), 'w') as json_file:
        #
        metadata = {
            "origin_x" : origin_x,
            "origin_y" : origin_y,
            "tile_size_0" : tile_size_0,
            "resolution_0" : resolution_0
        }
        json.dump(metadata, json_file, indent=3)

    # tile for all zoom levels
    for z in range(z_min, z_max+1):
        print("Tiling - zoom level", z)
        d = math.pow(2, z)
        tile_z(input_gpkg_path_fun(z), output_folder+str(z)+"/", tile_size_0 / d, resolution_0 / d, -9000000, -6000000)



#
tile(lambda z: "/home/juju/geodata/GPS/traces.gpkg", "/home/juju/geodata/GPS/tiled/", 4, 15, 100000000, 300000, -9000000, -6000000)
