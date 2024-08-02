import fiona
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
        else: print("Unhandled property type for: ", prop_value)

        if prop_type:
            schema['properties'][prop_name] = prop_type

    return schema


def get_schema_from_dict_feature(f):
    geometry_type = mapping(f['geometry'])['type']
    
    properties = {}
    for key, value in f.items():
        if key == 'geometry':
            continue
        if isinstance(value, int):
            properties[key] = 'int'
        elif isinstance(value, float):
            properties[key] = 'float'
        elif isinstance(value, str):
            properties[key] = 'str'
        elif isinstance(value, bool):
            properties[key] = 'bool'
        else: print("Unhandled property type for: ", value)

    schema = {
        'geometry': geometry_type,
        'properties': properties
    }
    
    return schema