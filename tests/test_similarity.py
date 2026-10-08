"""Focused invariants for exact similarity."""

import pytest

from smk_playground.similarity.engine import SimilarityEngine, compare

PROFILE = {
    "name": "test",
    "required_features": ["centroid_l", "centroid_a", "centroid_b", "spread"],
    "components": [
        {"name": "centroid", "fields": ["centroid_l", "centroid_a", "centroid_b"],
         "metric": "euclidean", "scale": 0.5, "weight": 0.8},
        {"name": "spread", "fields": ["spread"], "metric": "absolute",
         "scale": 1.0, "weight": 0.15},
        {"name": "hue", "fields": ["hue"], "metric": "absolute",
         "scale": 1.0, "weight": 0.05},
    ],
}


def row(entity_id, l, spread, hue=0.5, geometry=0.2):
    return {"smk_entity_id": entity_id, "object_number": entity_id, "centroid_l": l,
            "centroid_a": 0.0, "centroid_b": 0.0, "spread": spread, "hue": hue,
            "geometry": geometry, "quality_flags": []}


def test_self_distance_and_contribution_sum():
    item = row("a", 0.5, 0.2)
    result = compare(item, item, PROFILE)
    assert result["total_distance"] == 0.0
    assert sum(part["contribution"] for part in result["components"].values()) == 0.0


def test_symmetry_and_optional_component_renormalization():
    left, right = row("a", 0.5, 0.2, None), row("b", 0.6, 0.4, 0.8)
    forward, backward = compare(left, right, PROFILE), compare(right, left, PROFILE)
    assert forward["total_distance"] == pytest.approx(backward["total_distance"])
    assert forward["active_components"] == ["centroid", "spread"]
    assert forward["active_weight_sum"] == pytest.approx(0.95)
    assert sum(part["contribution"] for part in forward["components"].values()) == pytest.approx(forward["total_distance"])


def test_required_feature_and_geometry_eligibility():
    missing = row("a", 0.5, None)
    assert compare(missing, row("b", 0.6, 0.2), PROFILE) is None
    geometry_profile = {"name": "geometry", "required_features": ["geometry"],
                        "components": [{"name": "geometry", "fields": ["geometry"],
                                        "metric": "absolute", "scale": 1.0, "weight": 1.0}]}
    assert compare(row("a", 0.5, 0.2, geometry=None), row("b", 0.6, 0.2), geometry_profile) is None


def test_exact_topk_stable_tie_breaking_and_achromatic_eligibility():
    engine = SimilarityEngine.__new__(SimilarityEngine)
    engine.rows = [row("q", 0.5, 0.2, None), row("b", 0.6, 0.2), row("a", 0.4, 0.2), row("z", 0.9, 0.9)]
    engine.by_id = {item["smk_entity_id"]: item for item in engine.rows}
    engine.by_object_number = {item["object_number"]: [item] for item in engine.rows}
    engine.titles = {}
    engine.profiles = {"color-similarity-v1": PROFILE}
    first = engine.search_row(engine.rows[0], "color", 2)
    second = engine.search_row(engine.rows[0], "color", 2)
    assert [item["smk_entity_id"] for item in first] == ["a", "b"]
    assert first == second


def test_object_number_ambiguity_requires_entity_id():
    engine = SimilarityEngine.__new__(SimilarityEngine)
    engine.by_id = {"a": row("a", 0.1, 0.1), "b": row("b", 0.2, 0.2)}
    engine.by_object_number = {"shared": [engine.by_id["a"], engine.by_id["b"]]}
    with pytest.raises(ValueError, match="Ambiguous"):
        engine.resolve(object_number="shared")
    assert engine.resolve(smk_entity_id="b")["smk_entity_id"] == "b"
