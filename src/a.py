
#fake server
ogr2ogr -f GeoJSON data.json yourfile.gpkg
tippecanoe -e assets/test/ -Z 0 -z 18 assets/bat_mars.geojson


# check client
# OL https://openlayers.org/workshop/en/vectortile/
# leaflet https://www.npmjs.com/package/leaflet-vector-tile-layer

# Make dummy application - with example
# Test features

# make gps data vector tiles 
# Load GPS traces from folder

#MB tiling: https://github.com/mapbox/tippecanoe or TileMill or gdal - specs: https://github.com/mapbox/mbtiles-spec
# then read it from leaflet with Leaflet.TileLayer.MBTiles

