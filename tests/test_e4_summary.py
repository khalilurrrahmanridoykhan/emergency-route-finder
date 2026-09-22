"""path_modes and path_crosses_flood, tested against a small in-memory raster (no fixtures needed)."""
import json

import numpy as np
from rasterio.transform import from_origin
from summarize_e4 import FLOOD_CLASS, path_crosses_flood, path_modes


def make_path_file(tmp_path, coords):
    path_dir = tmp_path / "paths"
    path_dir.mkdir(exist_ok=True)
    name = f"p{len(list(path_dir.glob('*.geojson')))}.geojson"
    geojson = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords}, "properties": {}}
    ]}
    (path_dir / name).write_text(json.dumps(geojson))
    return name


def setup_module(module):
    import summarize_e4
    module._orig_paths = summarize_e4.PATHS


def teardown_module(module):
    import summarize_e4
    summarize_e4.PATHS = module._orig_paths


def test_path_modes_walking_then_motorized(tmp_path, monkeypatch):
    import summarize_e4
    monkeypatch.setattr(summarize_e4, "PATHS", tmp_path / "paths")
    transform = from_origin(0, 300, 100, 100)
    lc = np.array([[10, 10, 10], [204, 204, 204], [204, 204, 204]], dtype="uint16")  # row0=walk, row1-2=road
    coords = [(50, 250), (50, 150), (250, 50)]  # top row then lower rows
    name = make_path_file(tmp_path, coords)
    modes = path_modes(name, lc, transform)
    assert modes == ["WALKING", "MOTORIZED"]


def test_path_modes_empty_for_no_path_file():
    assert path_modes(None, np.zeros((2, 2)), from_origin(0, 2, 1, 1)) == []


def test_path_crosses_flood_true_only_when_a_vertex_is_on_class_301(tmp_path, monkeypatch):
    import summarize_e4
    monkeypatch.setattr(summarize_e4, "PATHS", tmp_path / "paths")
    transform = from_origin(0, 200, 100, 100)
    flooded = np.array([[10, 10], [FLOOD_CLASS, 10]], dtype="uint16")
    crossing = make_path_file(tmp_path, [(50, 50)])  # bottom-left cell = flooded
    dry = make_path_file(tmp_path, [(50, 150)])  # top-left cell = not flooded
    assert path_crosses_flood(crossing, flooded, transform) is True
    assert path_crosses_flood(dry, flooded, transform) is False
    assert path_crosses_flood(None, flooded, transform) is False
