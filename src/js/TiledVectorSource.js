

getTiledVectorSource = (url) => {

    var vectorSource = new ol.source.Vector();

    //tile cache
    vectorSource.cache = {}
    vectorSource.getCacheData = (z, x, y) => {
        if (!vectorSource.cache[z]) return
        if (!vectorSource.cache[z][x]) return
        return vectorSource.cache[z][x][y]
    }
    vectorSource.insertInCache = (z, x, y, data) => {
        if (!vectorSource.cache[z]) vectorSource.cache[z] = {}
        if (!vectorSource.cache[z][x]) vectorSource.cache[z][x] = {}
        vectorSource.cache[z][x][y] = data
    }


    (async () => {

        const metadata = await (await fetch(url + 'metadata.json')).json()
        //.catch(error => console.error('Error fetching the JSON data:', error));

        //read base metadata
        const r0 = metadata.resolution_0, ts0 = metadata.tile_size * r0,
            ox = metadata.origin_x, oy = metadata.origin_y,
            z_min = metadata.z_min, z_max = metadata.z_max

        //transform geojson geometry coordinate from tile CRS to map CRS
        function transformGeoJSONGeometryCoordinates(geometry, tile, ts, r) {
            function transformCoordinates(coordinates) {
                if (Array.isArray(coordinates[0])) return coordinates.map(transformCoordinates);
                else {
                    const x = coordinates[0], y = coordinates[1]
                    return [ox + tile.x * ts + x * r, oy + tile.y * ts + y * r];
                }
            }
            //if (geometry && geometry.coordinates)
            geometry.coordinates = transformCoordinates(geometry.coordinates);
        }


        vectorSource.update___ = () => {

            //get zoom level
            let z = Math.round(map.getView().getZoom())
            //console.log(z)
            if (z < z_min) z = z_min; else if (z > z_max) z = z_max

            //compute tile size and resolution
            const ddd = Math.pow(2, z)
            const ts = ts0 / ddd
            const r = r0 / ddd

            //clear
            vectorSource.clear();

            //get tiles within viewshed
            var bbox = map.getView().calculateExtent(map.getSize());
            var tiles = getTiles(bbox, ts);

            //handle each tile
            tiles.forEach(tile => {

                //try to retrieve from cache
                const features = vectorSource.getCacheData(z, tile.x, tile.y)

                if (features == "failed" || features == "loading") {
                    //do nothing
                } else if (features) {
                    //add cached features to layer
                    vectorSource.addFeatures(features);
                } else {
                    //mark as loading
                    vectorSource.insertInCache(z, tile.x, tile.y, "loading")

                    //launch request
                    fetch(url + z + "/" + tile.x + "/" + tile.y + ".geojson")
                        .then(response => response.json())
                        .then(geojson => {

                            //apply coordinates transformation to features
                            geojson.features.forEach(feature => transformGeoJSONGeometryCoordinates(feature.geometry, tile, ts, r));
                            geojson.features.forEach(feature => feature.id = Math.round(1e15 * Math.random()))

                            //transform into OL feature
                            var features = new ol.format.GeoJSON().readFeatures(geojson, { featureProjection: 'EPSG:3857' });

                            //store into cache
                            vectorSource.insertInCache(z, tile.x, tile.y, features)

                            //add features to layer
                            vectorSource.addFeatures(features);
                        })
                        .catch(error => {
                            vectorSource.insertInCache(z, tile.x, tile.y, "failed")
                            //console.error('Error fetching GeoJSON tile:', tile.x, tile.y, error)
                        });
                }
            });
        }

        //get tiles intersecting the viewshed
        function getTiles(bbox, ts) {

            const [xmin, ymin, xmax, ymax] = bbox;

            const
                xtmin = Math.floor((xmin - ox) / ts),
                ytmin = Math.floor((ymin - oy) / ts),
                xtmax = Math.floor((xmax - ox) / ts),
                ytmax = Math.floor((ymax - oy) / ts);

            var tiles = [];
            for (var xt = xtmin; xt <= xtmax; xt++)
                for (var yt = ytmin; yt <= ytmax; yt++)
                    tiles.push({ x: xt, y: yt });

            return tiles;
        }

        //trigger layer refresh on viewshed changes
        map.getView().on('change:center', vectorSource.update___);
        map.getView().on('change:resolution', vectorSource.update___);

        vectorSource.update___();

    })()

    return vectorSource
}


