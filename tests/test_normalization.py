import json
import math

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from smk_playground.normalize.milestone4 import (
    FAMILIES,
    build_profile,
    hue_xy,
    log_aspect_ratio,
    midrank_percentiles,
    robust_01,
    robust_z,
)


def test_robust_01_and_clipping():
    assert robust_01(5.0, 0.0, 10.0) == 0.5
    assert robust_01(-1.0, 0.0, 10.0) == 0.0
    assert robust_01(11.0, 0.0, 10.0) == 1.0
    assert robust_01(0.4, 0.2, 0.8, natural=True) == 0.4
    assert robust_01(None, 0.0, 1.0) is None
    assert robust_01(1.0, 1.0, 1.0) is None


def test_midrank_percentile_ties_and_nulls():
    assert midrank_percentiles([1.0, 2.0, 2.0, 4.0, None]) == [0.0, 0.5, 0.5, 1.0, None]
    assert midrank_percentiles([7.0]) == [0.5]


def test_robust_z_and_zero_mad():
    assert robust_z(2.4826, 1.0, 1.0) == pytest.approx(1.0)
    assert robust_z(None, 1.0, 1.0) is None
    assert robust_z(1.0, 1.0, 0.0) is None


def test_log_aspect_and_circular_hue():
    assert log_aspect_ratio(20.0, 10.0) == math.log(2.0)
    assert log_aspect_ratio(None, 10.0) is None
    assert log_aspect_ratio(0.0, 10.0) is None
    x, y = hue_xy(90.0)
    assert abs(x) < 1e-12 and y == 1.0
    assert hue_xy(None) == (None, None)


def test_family_order_is_explicit():
    assert FAMILIES["color_core_v1"][:3] == ("centroid_l", "centroid_a", "centroid_b")
    assert FAMILIES["geometry_v1"][-1] == "log_net_aspect_ratio_robust_01"


def test_profile_generation_and_parquet_are_deterministic(tmp_path):
    profile_a = build_profile("abc", "2026-01-01T00:00:00Z", 2, "1.0.0", "1.0.0", [])
    profile_b = build_profile("abc", "2026-01-01T00:00:00Z", 2, "1.0.0", "1.0.0", [])
    assert json.dumps(profile_a, sort_keys=True) == json.dumps(profile_b, sort_keys=True)
    table = pa.table({"id": ["a", "b"], "value": [1.0, None]})
    first, second = tmp_path / "a.parquet", tmp_path / "b.parquet"
    pq.write_table(table, first, compression="zstd", version="2.6")
    pq.write_table(table, second, compression="zstd", version="2.6")
    assert first.read_bytes() == second.read_bytes()
