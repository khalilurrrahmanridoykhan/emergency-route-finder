"""Download the public inputs for the wider area into data/cache/ (not committed).

OSM roads (Overpass), WorldPop 2020 population, ESA WorldCover land cover and
Copernicus DEM (Microsoft Planetary Computer STAC, no account needed).
Run: .venv/bin/python scripts/fetch_inputs.py
"""
import json
from pathlib import Path

import planetary_computer
import rasterio
import requests
from grid import BBOX_WGS84
from pystac_client import Client
from rasterio.merge import merge

CACHE = Path(__file__).resolve().parent.parent / "data" / "cache"
UA = "emergency-route-finder/0.1 (github.com/khalilurrrahmanridoykhan)"
OVERPASS = "https://overpass-api.de/api/interpreter"
WORLDPOP = (
    "https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/"
    "2020/BSGM/BGD/bgd_ppp_2020_constrained.tif"
)
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"


def fetch_roads():
    out = CACHE / "osm_roads_wide.json"
    if out.exists():
        return out
    s, w, n, e = BBOX_WGS84[1], BBOX_WGS84[0], BBOX_WGS84[3], BBOX_WGS84[2]
    query = f'[out:json][timeout:240];way["highway"]({s},{w},{n},{e});out geom tags;'
    r = requests.post(OVERPASS, data={"data": query}, headers={"User-Agent": UA}, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)
    return out


def fetch_worldpop():
    out = CACHE / "bgd_ppp_2020_constrained.tif"
    if out.exists():
        return out
    with requests.get(WORLDPOP, headers={"User-Agent": UA}, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    return out


def fetch_stac_mosaic(collection, asset, out_name, **search):
    """Mosaic the items of a Planetary Computer collection over BBOX_WGS84 (EPSG:4326)."""
    out = CACHE / out_name
    if out.exists():
        return out
    catalog = Client.open(STAC, modifier=planetary_computer.sign_inplace)
    items = list(catalog.search(collections=[collection], bbox=BBOX_WGS84, **search).items())
    if not items:
        raise RuntimeError(f"no {collection} items found")
    sources = [rasterio.open(item.assets[asset].href) for item in items]
    try:
        mosaic, transform = merge(sources, bounds=BBOX_WGS84)
        profile = sources[0].profile | {
            "height": mosaic.shape[1], "width": mosaic.shape[2], "transform": transform,
            "compress": "deflate", "tiled": True,
        }
    finally:
        for src in sources:
            src.close()
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(mosaic)
    print(f"{collection}: {len(items)} items -> {out.name} {mosaic.shape}")
    return out


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    roads = fetch_roads()
    print("roads", roads.stat().st_size, "bytes,", len(json.loads(roads.read_text())["elements"]), "ways")
    print("worldpop", fetch_worldpop().stat().st_size, "bytes")
    fetch_stac_mosaic("esa-worldcover", "map", "worldcover_wide_4326.tif", query={"esa_worldcover:product_version": {"eq": "2.0.0"}}, datetime="2021-01-01/2021-12-31")
    fetch_stac_mosaic("cop-dem-glo-30", "data", "dem_wide_4326.tif")


if __name__ == "__main__":
    main()
