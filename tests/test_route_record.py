"""path_modes, path_crosses_flood and build_route_record -- all pure, no Docker, no fixtures beyond
a small in-memory raster and a tiny points_result-style DataFrame."""
import json

import numpy as np
import pandas as pd
from rasterio.transform import from_origin
from route_record import FLOOD_CLASS, build_route_record, path_crosses_flood, path_modes


def make_path_file(path_dir, coords):
    path_dir.mkdir(exist_ok=True, parents=True)
    name = f"p{len(list(path_dir.glob('*.geojson')))}.geojson"
    geojson = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords}, "properties": {}}
    ]}
    (path_dir / name).write_text(json.dumps(geojson))
    return name


def test_path_modes_walking_then_motorized(tmp_path):
    paths_dir = tmp_path / "paths"
    transform = from_origin(0, 300, 100, 100)
    lc = np.array([[10, 10, 10], [204, 204, 204], [204, 204, 204]], dtype="uint16")  # row0=walk, row1-2=road
    coords = [(50, 250), (50, 150), (250, 50)]  # top row then lower rows
    name = make_path_file(paths_dir, coords)
    modes = path_modes(paths_dir, name, lc, transform)
    assert modes == ["WALKING", "MOTORIZED"]


def test_path_modes_empty_for_no_path_file(tmp_path):
    assert path_modes(tmp_path, None, np.zeros((2, 2)), from_origin(0, 2, 1, 1)) == []


def test_path_crosses_flood_true_only_when_a_vertex_is_on_class_301(tmp_path):
    paths_dir = tmp_path / "paths"
    transform = from_origin(0, 200, 100, 100)
    flooded = np.array([[10, 10], [FLOOD_CLASS, 10]], dtype="uint16")
    crossing = make_path_file(paths_dir, [(50, 50)])  # bottom-left cell = flooded
    dry = make_path_file(paths_dir, [(50, 150)])  # top-left cell = not flooded
    assert path_crosses_flood(paths_dir, crossing, flooded, transform) is True
    assert path_crosses_flood(paths_dir, dry, flooded, transform) is False
    assert path_crosses_flood(paths_dir, None, flooded, transform) is False


def test_build_route_record_assembles_both_seasons_and_kinds(tmp_path):
    paths_dir = tmp_path / "paths"
    transform = from_origin(0, 200, 100, 100)
    dry_lc = np.full((2, 2), 204, dtype="uint16")  # all road
    flood_lc = np.full((2, 2), 204, dtype="uint16")
    flood_lc[1, 0] = FLOOD_CLASS  # one flooded cell

    fac = pd.DataFrame({"name": {5: "Facility A", 9: "Facility B"}})

    primary_dry = make_path_file(paths_dir, [(50, 50), (60, 60)])  # not flooded cell
    primary_flood = make_path_file(paths_dir, [(10, 10), (20, 20)])  # row1,col0 -- the flooded cell
    backup_dry = make_path_file(paths_dir, [(50, 50), (70, 70)])

    res = pd.DataFrame([
        {"id": 1, "season": "dry", "kind": "primary", "facility_cat": 5, "minutes": 30,
         "path_file": primary_dry},
        {"id": 1, "season": "dry", "kind": "backup", "facility_cat": 9, "minutes": 50,
         "path_file": backup_dry},
        {"id": 1, "season": "flood0708", "kind": "primary", "facility_cat": 5, "minutes": 45,
         "path_file": primary_flood},
        {"id": 1, "season": "flood0708", "kind": "backup", "facility_cat": 9, "minutes": None,
         "path_file": None},
    ])
    point = pd.Series({"emergency_id": "snakebite", "lon": 91.0, "lat": 24.5})
    land_cover = {"dry": (dry_lc, transform), "flood0708": (flood_lc, transform)}

    record, features = build_route_record(1, point, res, fac, land_cover, {"snakebite": 120}, paths_dir)

    assert record["dry_primary_facility_name"] == "Facility A"
    assert record["dry_primary_minutes"] == 30
    assert record["dry_primary_within_target"]
    assert record["flood0708_primary_minutes"] == 45
    assert record["dry_backup_facility_name"] == "Facility B"
    assert record["flood0708_backup_minutes"] is None
    assert "the flood-season path crosses flooded ground" in record["warnings"]
    assert len(features) == 3  # dry primary, dry backup, flood primary (flood backup has no path)
