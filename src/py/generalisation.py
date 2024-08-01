import math
from shapely.ops import linemerge

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import loadFeatures



def resolutionise(geometry, resolution):
    if geometry.is_empty:
        return geometry

#np.round(coords).astype(int)
    def _reso(x):
        return resolution * math.round(x/resolution)

    def _resos(coords):
        return tuple([_reso(coords[0]), _reso(coords[1])])

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





def simplify_traces(input_gpkg_path, output_gpkg_path, resolution):

    # load input data
    print("Load data from", input_gpkg_path)
    fs = loadFeatures(input_gpkg_path)
    print(len(fs))

    for f in fs:
        geom = f["geometry"]

        # Douglas-Peucker simplification
        geom = geom.simplify(resolution)

        #
        geom = resolutionise(geom, resolution)

        # linemerge
        #try:
        geom = linemerge(geom)
        #except: pass
        #if geom.is_empty: continue


resolution = 1000
simplify_traces("/home/juju/geodata/GPS/traces.gpkg", "/home/juju/geodata/GPS/traces_"+str(resolution)+".gpkg", resolution)
