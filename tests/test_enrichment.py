"""Focused enrichment palette and transport tests."""

import math
from pathlib import Path

import pytest

from smk_playground.enrichment import fetch as fetch_module
from smk_playground.enrichment.milestone6 import compare_weighted
from smk_playground.enrichment.weighted import (
    palette_transport_distance,
    parse_weighted_palette,
    weighted_features,
)


def palette(raw):
    return parse_weighted_palette(raw)[0]


def test_weighted_parser_and_invalid_tokens():
    rows, audit = parse_weighted_palette("#FF0000 #00ff00 #ff0000 bad")
    assert [row["hex"] for row in rows] == ["#ff0000", "#00ff00"]
    assert [row["token_count"] for row in rows] == [2, 1]
    assert math.fsum(row["weight"] for row in rows) == pytest.approx(1.0)
    assert audit == {"status": "partial_invalid", "token_count": 4,
                     "valid_token_count": 3, "invalid_tokens": ["bad"],
                     "unique_color_count": 2}
    assert parse_weighted_palette(None)[1]["status"] == "missing"


def test_weighted_feature_entropy_effective_size_and_dominant():
    features = weighted_features(palette("#ff0000 #ff0000 #ff0000 #000000"))
    expected_entropy = -(0.75 * math.log(0.75) + 0.25 * math.log(0.25))
    assert features["palette_entropy"] == pytest.approx(expected_entropy)
    assert features["effective_palette_size"] == pytest.approx(math.exp(expected_entropy))
    assert features["dominant_color_weight"] == 0.75
    assert features["dominant_color_hex"] == "#ff0000"
    assert features["centroid_l"] is not None


def test_transport_invariants_and_order():
    first = palette("#ff0000 #ff0000 #0000ff")
    reordered = list(reversed(first))
    assert palette_transport_distance(first, first) == pytest.approx(0.0, abs=1e-12)
    assert palette_transport_distance(first, reordered) == pytest.approx(0.0, abs=1e-12)
    other = palette("#ff0000 #0000ff #0000ff")
    forward = palette_transport_distance(first, other)
    assert forward > 0
    assert forward == pytest.approx(palette_transport_distance(other, first))
    assert forward == pytest.approx(palette_transport_distance(first, other))


def test_one_color_transport_is_oklab_distance():
    red, blue = palette("#ff0000"), palette("#0000ff")
    expected = math.sqrt(sum(
        (red[0][field] - blue[0][field]) ** 2
        for field in ("oklab_l", "oklab_a", "oklab_b")
    ))
    assert palette_transport_distance(red, blue) == pytest.approx(expected)


def test_weighted_similarity_symmetry_and_contributions():
    left_palette = palette("#ff0000 #ff0000 #0000ff")
    right_palette = palette("#ff0000 #0000ff #0000ff")
    left = weighted_features(left_palette) | {
        "palette_spread_robust_01": 0.2, "chroma_stddev_robust_01": 0.3,
        "dominant_color_weight_robust_01": 0.5,
    }
    right = weighted_features(right_palette) | {
        "palette_spread_robust_01": 0.4, "chroma_stddev_robust_01": 0.2,
        "dominant_color_weight_robust_01": 0.5,
    }
    weights = {"weighted_centroid_oklab": 0.3, "palette_transport_distance_oklab": 0.4,
               "weighted_palette_spread": 0.12, "weighted_chroma_stddev": 0.08,
               "weighted_hue_concentration": 0.05, "dominant_color_weight": 0.05}
    profile = {"weights": weights, "scales": {key: 1.0 for key in weights}}
    forward = compare_weighted(left, right, left_palette, right_palette, profile)
    backward = compare_weighted(right, left, right_palette, left_palette, profile)
    assert forward["total_distance"] == pytest.approx(backward["total_distance"])
    assert sum(item["contribution"] for item in forward["components"].values()) == pytest.approx(
        forward["total_distance"]
    )


def test_fetch_resume_skips_successful_cache(tmp_path, monkeypatch):
    root = Path(tmp_path)
    monkeypatch.setattr(fetch_module, "corpus_targets", lambda unused: (["A", "B"], {"A": ["1"], "B": ["2"]}))
    calls = []

    def fake_fetch(number, cache_dir, delay, retries):
        calls.append(number)
        path = cache_dir / f"{number}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
        return {"object_number": number, "outcome": "success", "http_status": 200,
                "response_at_utc": "x", "attempt": 1, "cache_path": path.as_posix()}

    monkeypatch.setattr(fetch_module, "_fetch_one", fake_fetch)
    fetch_module.fetch(root, concurrency=1)
    fetch_module.fetch(root, concurrency=1)
    assert calls == ["A", "B"]
