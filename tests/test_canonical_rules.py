from smk_playground.canonical.rules import (
    corpus_membership,
    dimension_slots,
    image_bundle_complete,
    normalize_dimension_observations,
    resolve_image_bundle,
    resolve_smk_entity_id,
    rights_semantic,
    visual_number,
)


def complete_bundle(image_id: str = "image") -> dict:
    return {
        "has_image": True,
        "image_iiif_id": image_id,
        "image_iiif_info": f"{image_id}/info.json",
        "image_width": 100,
        "image_height": 200,
        "image_thumbnail": "thumb",
        "image_native": "native",
        "image_mime_type": "image/tiff",
        "image_cropped": False,
        "image_orientation": "portrait",
        "image_hq": True,
    }


def test_da_en_pairing_uses_smk_id_only() -> None:
    assert resolve_smk_entity_id("117_object", "117_object") == "117_object"
    assert resolve_smk_entity_id(None, "118_object") == "118_object"
    try:
        resolve_smk_entity_id("117_object", "118_object")
    except ValueError:
        pass
    else:
        raise AssertionError("different SMK ids must not be paired")


def test_image_bundle_is_atomic() -> None:
    da = complete_bundle("da")
    en = complete_bundle("en")
    canonical, provenance, status = resolve_image_bundle(da, en)
    assert canonical is None
    assert provenance == "conflict"
    assert status == "IMAGE_BUNDLE_CONFLICT"

    canonical, provenance, status = resolve_image_bundle(da, {"has_image": False})
    assert canonical == da
    assert provenance == "da"
    assert status == "IMAGE_BUNDLE_SINGLE_SOURCE"
    assert image_bundle_complete(canonical)


def test_dimension_aliases_convert_to_cm_and_conflicts_stay_null() -> None:
    da = {"dimensions": [{"part": "Netto", "type": "højde", "unit": "millimeter", "value": "100"}]}
    en = {"dimensions": [{"part": "netto", "type": "height", "unit": "cm", "value": "11"}]}
    observations = normalize_dimension_observations(da, "da", "da-id")
    observations += normalize_dimension_observations(en, "en", "en-id")
    slots, conflicts, candidates = dimension_slots(observations)
    assert slots["net_height_cm"] is None
    assert conflicts == ["net_height_cm"]
    assert len(candidates) == 2


def test_rights_semantics_are_language_independent() -> None:
    assert rights_semantic("https://creativecommons.org/publicdomain/mark/1.0/") == "PDM"
    assert rights_semantic("https://www.smk.dk/section/brug-af-museets-materiale/") == "SMK_RESTRICTED_POLICY"
    assert rights_semantic("https://www.smk.dk/en/section/use-of-smk-material/") == "SMK_RESTRICTED_POLICY"


def test_infinity_colortemp_is_missing_with_explicit_status() -> None:
    assert visual_number({"colortemp": "Infinity"}, "colortemp") == (None, "malformed_text")


def test_corpus_rule_returns_machine_readable_reasons() -> None:
    row = {
        "quality_flags": [], "public_domain": True, "rights_semantic": "PDM",
        "image_bundle_status": "IMAGE_BUNDLE_OK", "image_bundle_complete": True,
        "colors": ["#ffffff"],
    }
    assert corpus_membership(row) == (True, [])
    row["colors"] = None
    row["image_bundle_complete"] = False
    assert corpus_membership(row) == (False, ["NO_USABLE_IMAGE", "NO_COLORS"])


def test_rules_are_deterministic() -> None:
    bundle = complete_bundle()
    assert resolve_image_bundle(bundle, dict(bundle)) == resolve_image_bundle(bundle, dict(bundle))
