import fiona
from fiona.crs import from_epsg
from shapely.geometry import shape, mapping
from rtree import index


#load features from a file, as a list of features - each feature is a simple dictionnary
def loadFeatures(file, bbox=None, layer=None):
    features = []
    gpkg = fiona.open(file, 'r')
    data = list(gpkg.items(bbox=bbox,layer=layer))
    for d in data:
        d = d[1]
        f = { "geometry": shape(d['geometry']) }
        properties = d['properties']
        for key, value in properties.items(): f[key] = value
        features.append(f)
    return features


#remove all properties of the feature/dictionnary, except the geometry
def keepOnlyGeometry(feature):
    for attribute in list(feature.keys()):
        if attribute != 'geometry':
            #feature.pop(attribute)
            del feature[attribute]

def keep_attributes(feature, attributes_to_keep):
    for att in list(feature.keys()):
        if att in attributes_to_keep: continue
        del feature[att]

#make features spatial index
def spatialIndex(features):
    sindex = index.Index()
    for i,f in enumerate(features): sindex.insert(i, f['geometry'].bounds)
    return sindex




def get_schema_from_geojson_feature(feature):
    """
    Function to extract schema from a feature.

    Parameters:
    - feature: A GeoJSON-like dictionary representing a feature.

    Returns:
    - schema: A dictionary representing the schema derived from the feature.
    """
    schema = {
        'geometry': feature['geometry']['type'],
        'properties': {}
    }

    # Extract property names and types from the feature's properties
    for prop_name, prop_value in feature['properties'].items():
        prop_type = None
        if isinstance(prop_value, str):
            prop_type = 'str'
        elif isinstance(prop_value, int):
            prop_type = 'int'
        elif isinstance(prop_value, float):
            prop_type = 'float'
        elif isinstance(prop_value, bool):
            prop_type = 'bool'
        else: print("Unhandled property type for: ", prop_value)

        if prop_type:
            schema['properties'][prop_name] = prop_type

    return schema



def save_features_to_gpkg(fs, out_gpkg_file, crs_epsg="3035"):
    """
    Save a list of features as a GeoPackage file using Fiona.

    Parameters:
    - fs: List of dictionaries representing the features.
    - out_gpkg_file: The output file path for the GeoPackage.
    - crs_epsg: The EPSG code for the coordinate reference system (default is "3035").

    The function is generic to handle varying input feature structures.
    """

    # Determine the schema dynamically from the first feature
    first_feature = fs[0]
    schema = {
        'geometry': first_feature['geometry'].__class__.__name__,
        'properties': {k: type(v).__name__ for k, v in first_feature.items() if k != 'geometry'}
    }

    # Use Fiona to write the features to a GeoPackage
    with fiona.open(
        out_gpkg_file, 
        'w', 
        driver='GPKG',
        schema=schema,
        crs=from_epsg(crs_epsg)
    ) as layer:
        for feature in fs:
            geom = feature.pop('geometry')
            layer.write({
                'geometry': mapping(geom),
                'properties': feature
            })
    #TODO: use out.writerecords(fs_out) instead ?
