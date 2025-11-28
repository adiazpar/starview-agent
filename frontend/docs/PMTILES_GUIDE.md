# PMTiles + Cloudflare R2 Guide

Guide for serving light pollution raster tiles using PMTiles format hosted on Cloudflare R2.

## Why PMTiles + R2?

| Approach | Storage Cost | Request Cost | Maintenance |
|----------|--------------|--------------|-------------|
| **PMTiles + R2** | $0.015/GB/mo | Free egress | None |
| Self-hosted GDAL server | Server cost | Included | High |
| Mapbox Tilesets | Free (<20GB) | $0.10-0.25/1K | None |

**For 12GB of light pollution data at scale, R2 is the most cost-effective option.**

---

## Step 1: Convert GeoTIFF to PMTiles

### Option A: GDAL + pmtiles CLI (Recommended for large files)

```bash
# 1. Convert GeoTIFF to MBTiles
gdal_translate light_pollution.tif light_pollution.mbtiles -of MBTILES

# 2. Generate zoom levels (adjust numbers based on your needs)
gdaladdo -r average light_pollution.mbtiles 2 4 8 16

# 3. Convert MBTiles to PMTiles
# Download pmtiles CLI from: https://github.com/protomaps/go-pmtiles/releases
pmtiles convert light_pollution.mbtiles light_pollution.pmtiles
```

### Option B: rio-pmtiles (Python)

```bash
pip install rio-pmtiles

# If single-band, convert to RGB first
gdal_translate -expand rgb light_pollution.tif light_pollution_rgb.tif

# Convert to PMTiles
rio pmtiles light_pollution_rgb.tif light_pollution.pmtiles --format PNG
```

---

## Step 2: Upload to Cloudflare R2

```bash
# Install wrangler if needed
npm install -g wrangler

# Create bucket (or use existing starview-media bucket)
wrangler r2 bucket create starview-tiles

# Upload PMTiles file
wrangler r2 object put starview-tiles/light_pollution.pmtiles --file=light_pollution.pmtiles
```

---

## Step 3: Configure CORS on R2

Create `cors_rules.json`:

```json
[
  {
    "AllowedOrigins": ["https://starview.app", "http://localhost:5173"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["range", "if-match"],
    "ExposeHeaders": ["etag"],
    "MaxAgeSeconds": 3000
  }
]
```

Apply it:

```bash
wrangler r2 bucket cors set starview-tiles --file cors_rules.json
```

---

## Step 4: Make Bucket Accessible

### Option A: Public R2 URL (Simplest)

Enable public access in R2 dashboard. Your PMTiles URL becomes:

```
https://pub-xxxxx.r2.dev/light_pollution.pmtiles
```

### Option B: Cloudflare Worker (More control)

Clone and deploy the [Protomaps Cloudflare Worker](https://github.com/protomaps/PMTiles/tree/main/serverless/cloudflare) for custom routing/caching.

---

## Step 5: Use in Mapbox GL JS

### Install the library

```bash
npm install mapbox-pmtiles
```

### React Component Example

```javascript
import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import { PmTilesSource } from 'mapbox-pmtiles';

// Register the custom source type (do this once)
mapboxgl.Style.setSourceType(PmTilesSource.SOURCE_TYPE, PmTilesSource);

function MapWithLightPollution() {
  const mapContainer = useRef(null);
  const map = useRef(null);

  useEffect(() => {
    if (map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [-98.5, 39.8],
      zoom: 4
    });

    map.current.on('load', async () => {
      const PMTILES_URL = 'https://pub-xxxxx.r2.dev/light_pollution.pmtiles';

      // Get metadata from PMTiles header
      const header = await PmTilesSource.getHeader(PMTILES_URL);

      // Add PMTiles source
      map.current.addSource('light-pollution', {
        type: PmTilesSource.SOURCE_TYPE,
        url: PMTILES_URL,
        minzoom: header.minZoom,
        maxzoom: header.maxZoom,
      });

      // Add raster layer
      map.current.addLayer({
        id: 'light-pollution-layer',
        type: 'raster',
        source: 'light-pollution',
        paint: {
          'raster-opacity': 0.7
        }
      });
    });

    return () => map.current?.remove();
  }, []);

  return <div ref={mapContainer} style={{ width: '100%', height: '500px' }} />;
}

export default MapWithLightPollution;
```

---

## Cost Estimates

### Storage (Cloudflare R2)

| Data Size | Monthly Cost |
|-----------|--------------|
| 12 GB | $0.18 |
| 50 GB | $0.75 |
| 100 GB | $1.50 |

### Requests (R2 Class A operations)

- First 1 million requests/month: Free
- Additional: $4.50 per million requests
- **Egress: Always free**

### Example: 100K monthly active users

| Component | Cost |
|-----------|------|
| Storage (12GB) | $0.18 |
| Requests (~2M) | ~$4.50 |
| **Total** | **~$5/month** |

---

## Alternative: Cloud Optimized GeoTIFF (COG)

If you need to preserve the original GeoTIFF format, you can use COG instead:

```bash
# Convert to Cloud Optimized GeoTIFF
gdal_translate input.tif output_cog.tif -of COG -co COMPRESS=LZW
```

Then use [maplibre-cog-protocol](https://github.com/geomatico/maplibre-cog-protocol) to load directly in MapLibre GL JS.

---

## Resources

- [PMTiles Documentation](https://docs.protomaps.com/pmtiles/)
- [go-pmtiles CLI Releases](https://github.com/protomaps/go-pmtiles/releases)
- [mapbox-pmtiles Library](https://github.com/am2222/mapbox-pmtiles)
- [Protomaps Cloudflare Worker](https://github.com/protomaps/PMTiles/tree/main/serverless/cloudflare)
- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [GDAL MBTiles Driver](https://gdal.org/drivers/raster/mbtiles.html)
