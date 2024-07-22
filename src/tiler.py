import os
import fiona
from shapely.geometry import box, shape, mapping
from shapely.ops import transform
from shapely import wkt
import geopandas as gpd
import json



def round_coords(geometry, precision=3):
    if geometry.is_empty:
        return geometry

    def _round_coords(coords):
        return tuple(round(coord, precision) for coord in coords)

    if geometry.geom_type == 'Point':
        return type(geometry)(*map(_round_coords, [geometry.coords[0]]))
    elif geometry.geom_type in ['LineString', 'LinearRing']:
        return type(geometry)(list(map(_round_coords, geometry.coords)))
    elif geometry.geom_type == 'Polygon':
        exterior = list(map(_round_coords, geometry.exterior.coords))
        interiors = [list(map(_round_coords, ring.coords)) for ring in geometry.interiors]
        return type(geometry)(exterior, interiors)
    elif geometry.geom_type == 'MultiPoint':
        return type(geometry)([type(geometry.geoms[0])(list(map(_round_coords, geom.coords))) for geom in geometry.geoms])
    elif geometry.geom_type == 'MultiLineString':
        return type(geometry)([type(geometry.geoms[0])(list(map(_round_coords, geom.coords))) for geom in geometry.geoms])
    elif geometry.geom_type == 'MultiPolygon':
        return type(geometry)([
            type(geometry.geoms[0])(
                list(map(_round_coords, geom.exterior.coords)),
                [list(map(_round_coords, ring.coords)) for ring in geom.interiors]
            )
            for geom in geometry.geoms
        ])
    else:
        raise ValueError("Unhandled geometry type: {}".format(geometry.geom_type))






def tile_geopackage(input_gpkg_path, output_folder, tile_size):
    # create output folder
    os.makedirs(output_folder, exist_ok=True)

    # Open the input GeoPackage file
    with fiona.open(input_gpkg_path) as src:
        # data bounding box
        minx, miny, maxx, maxy = src.bounds

        # tile numbers
        nbx = int((maxx - minx) / tile_size) + 1
        nby = int((maxy - miny) / tile_size) + 1

        # load into a GeoDataFrame
        gdf = gpd.read_file(input_gpkg_path)

        for i in range(nbx):
            for j in range(nby):
                # bounds of the current tile
                tile_minx = minx + i * tile_size
                tile_miny = miny + j * tile_size
                tile_maxx = minx + (i + 1) * tile_size
                tile_maxy = miny + (j + 1) * tile_size
                tile_bounds = box(tile_minx, tile_miny, tile_maxx, tile_maxy)

                # clip input to tile bounds
                clipped_gdf = gdf[gdf.intersects(tile_bounds)].copy()
                clipped_gdf['geometry'] = clipped_gdf['geometry'].intersection(tile_bounds)

                # skip if empty
                if(len(clipped_gdf)==0): continue

                # Round the coordinates of each geometry
                clipped_gdf['geometry'] = clipped_gdf['geometry'].apply(lambda geom: round_coords(geom, precision=3))

                # output file
                output_file = os.path.join(output_folder, f"{i}/{j}.geojson")
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # save
                clipped_gdf.to_file(output_file, driver="GeoJSON")




#
tile_geopackage("/home/juju/geodata/GPS/traces_3857.gpkg", "/home/juju/geodata/GPS/tiles_100km/", 100000)
