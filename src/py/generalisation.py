from shapely.ops import linemerge
import math

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import load_features, save_features_to_gpkg



def resolutionise(geometry, resolution):
    if geometry.is_empty:
        return geometry

#np.round(coords).astype(int)
    def _reso(x):
        return resolution * round(x/resolution)

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





def simplify_traces(input_gpkg_path, output_gpkg_path, resolution, out_epsg = "3857", iterations=5):

    # load input data
    print("Load data from", input_gpkg_path)
    fs = load_features(input_gpkg_path)
    print(len(fs))

    fs_out = []
    for f in fs:
        geom = f["geometry"]

        #simplify lines
        for i in range(iterations):
            geom = geom.simplify(resolution)
            geom = resolutionise(geom, resolution)
            try: geom = linemerge(geom)
            except: pass
            if geom.is_empty: break

        if geom.is_empty: continue

        #check point
        if(geom.length <= resolution):
            geom = geom.centroid
            #print(geom)

        f['geometry'] = geom
        fs_out.append(f)

    print("save as GPKG", len(fs_out))
    save_features_to_gpkg(fs_out, output_gpkg_path, out_epsg)


def simplify_traces_z(input_gpkg_path, output_gpkg_path, z_min = 1, z_max = 10, resolution_0 = 250000, iterations=5, out_epsg = "3857"):
    for z in range(z_min, z_max+1):
        print("Generalising - zoom level", z)
        d = math.pow(2, z)
        resolution = resolution_0 / d
        simplify_traces(input_gpkg_path, output_gpkg_path+str(z)+".gpkg", resolution, iterations=iterations, out_epsg = out_epsg)












def simplify_traces_segments(input_gpkg_path, output_gpkg_path, resolution, out_epsg = "3857"):

    # load input data
    print("Load data from", input_gpkg_path)
    fs = load_features(input_gpkg_path)
    print(len(fs))

    fs_out = []
    for f in fs:
        geom = f["geometry"]

        geom = resolutionise(geom, resolution)

        if geom.is_empty: continue

        #check point
        if(geom.length == 0): continue

        f['geometry'] = geom
        fs_out.append(f)

    print("save as GPKG", len(fs_out))
    save_features_to_gpkg(fs_out, output_gpkg_path, out_epsg)





def simplify_traces_segments_z(input_gpkg_path, output_gpkg_path, z_min = 1, z_max = 10, resolution_0 = 250000, out_epsg = "3857"):
    for z in range(z_min, z_max+1):
        print("Generalising - zoom level", z)
        d = math.pow(2, z)
        resolution = resolution_0 / d
        #print(resolution)
        simplify_traces_segments(input_gpkg_path, output_gpkg_path+str(z)+".gpkg", resolution, out_epsg = out_epsg)



