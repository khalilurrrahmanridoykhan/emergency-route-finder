"""Download the public inputs for the analysis area into data/cache/ (not committed).

OSM roads (Overpass), WorldPop 2020 population, ESA WorldCover land cover and
Copernicus DEM (Microsoft Planetary Computer STAC, no account needed).
Run: .venv/bin/python scripts/fetch_inputs.py
"""
import io
import json
import shutil
import time
import zipfile
from pathlib import Path

import geopandas as gpd
import planetary_computer
import rasterio
import requests
from grid import BBOX_WGS84
from pystac_client import Client
from rasterio.merge import merge

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
UA = "emergency-route-finder/0.1 (github.com/khalilurrrahmanridoykhan)"
OVERPASS = "https://overpass-api.de/api/interpreter"
WORLDPOP = (
    "https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/"
    "2020/BSGM/BGD/bgd_ppp_2020_constrained.tif"
)
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"


def overpass(query):
    """POST an Overpass query, retrying a few times because the public servers are often busy."""
    for attempt in range(4):
        r = requests.post(OVERPASS, data={"data": query}, headers={"User-Agent": UA}, timeout=600)
        if r.status_code == 200:
            return r.json()
        time.sleep(30 * (attempt + 1))
    r.raise_for_status()


def tiles(bbox, nx=3, ny=2):
    west, south, east, north = bbox
    xs = [west + (east - west) * i / nx for i in range(nx + 1)]
    ys = [south + (north - south) * j / ny for j in range(ny + 1)]
    return [(xs[i], ys[j], xs[i + 1], ys[j + 1]) for i in range(nx) for j in range(ny)]


def fetch_roads():
    """All OSM highway ways in the analysis area, fetched in tiles and merged by way id."""
    out = CACHE / "osm_roads_wide.json"
    if out.exists():
        return out
    ways = {}
    for w, s, e, n in tiles(BBOX_WGS84):
        data = overpass(f'[out:json][timeout:300];way["highway"]({s},{w},{n},{e});out geom tags;')
        for element in data["elements"]:
            ways[element["id"]] = element
        print(f"  roads tile ({w:.2f},{s:.2f},{e:.2f},{n:.2f}): {len(data['elements'])} ways")
    out.write_text(json.dumps({"elements": list(ways.values())}))
    return out


def fetch_facilities():
    """OSM hospital, clinic and doctors features in the analysis area, saved as a frozen snapshot.

    The snapshot lives in data/raw/ and is committed, because Overpass results change over time.
    """
    out = ROOT / "data" / "raw" / "health_facilities_osm_extended.geojson"
    if out.exists():
        return out
    w, s, e, n = BBOX_WGS84
    query = (
        f"[out:json][timeout:300];("
        f'nwr["amenity"~"hospital|clinic|doctors"]({s},{w},{n},{e});'
        f'nwr["healthcare"~"hospital|clinic|centre"]({s},{w},{n},{e});'
        f");out center tags;"
    )
    features = []
    for element in overpass(query)["elements"]:
        centre = element.get("center") or {"lat": element.get("lat"), "lon": element.get("lon")}
        tags = element.get("tags", {})
        props = {"osm_type": element["type"], "osm_id": element["id"]}
        keep = ("amenity", "healthcare", "name", "name:en", "name:bn", "operator")
        props.update({k: tags[k] for k in keep if k in tags})
        features.append({"type": "Feature", "properties": props,
                         "geometry": {"type": "Point", "coordinates": [centre["lon"], centre["lat"]]}})
    features.sort(key=lambda f: f["properties"]["osm_id"])
    collection = {"type": "FeatureCollection", "features": features}
    out.write_text(json.dumps(collection, ensure_ascii=False, indent=1))
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


def fetch_admin3():
    """Upazila (ADM3) boundaries with official P-codes from HDX cod-ab-bgd, clipped to the wide box."""
    out = CACHE / "bgd_adm3_wide.geojson"
    if out.exists():
        return out
    api = "https://data.humdata.org/api/3/action/package_show?id=cod-ab-bgd"
    package = requests.get(api, headers={"User-Agent": UA}, timeout=60).json()["result"]
    url = next(r["url"] for r in package["resources"] if r["format"] == "SHP")
    blob = requests.get(url, headers={"User-Agent": UA}, timeout=600).content
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".shp") and "admin3" in n.lower())
        z.extractall(CACHE / "hdx_shp_tmp")
    layer = gpd.read_file(CACHE / "hdx_shp_tmp" / name).to_crs("EPSG:4326")
    wide = layer.cx[BBOX_WGS84[0] : BBOX_WGS84[2], BBOX_WGS84[1] : BBOX_WGS84[3]]
    keep = ["adm3_name", "adm3_pcode", "adm2_name", "adm2_pcode", "adm1_name", "adm1_pcode", "geometry"]
    wide[keep].to_file(out, driver="GeoJSON")
    shutil.rmtree(CACHE / "hdx_shp_tmp")
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
    facilities = fetch_facilities()
    print("facilities", len(json.loads(facilities.read_text())["features"]), "features")
    print("worldpop", fetch_worldpop().stat().st_size, "bytes")
    print("admin3", fetch_admin3().stat().st_size, "bytes")
    fetch_stac_mosaic(
        "esa-worldcover",
        "map",
        "worldcover_wide_4326.tif",
        query={"esa_worldcover:product_version": {"eq": "2.0.0"}},
        datetime="2021-01-01/2021-12-31",
    )
    fetch_stac_mosaic("cop-dem-glo-30", "data", "dem_wide_4326.tif")


if __name__ == "__main__":
    main()
