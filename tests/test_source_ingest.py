import json
from pathlib import Path

import pyarrow.parquet as pq

from smk_playground.ingest.milestone1 import ingest_source
from smk_playground.ingest.source import (
    iter_source_records,
    normalize_dimension_axis,
    parse_strict_number,
    source_row_id,
)

FIXTURE = Path(__file__).parent / "fixtures" / "source_array.json"


def test_streaming_parser_preserves_duplicates() -> None:
    records = list(iter_source_records(FIXTURE))
    assert [record["object_number"] for record in records] == ["A1", "A1"]


def test_source_row_id_is_deterministic_and_not_positional() -> None:
    record = {"id": "117_object", "object_number": "A1"}
    assert source_row_id("da", record) == "smk:da:117_object"
    assert source_row_id("da", record) == source_row_id("da", dict(reversed(record.items())))
    assert source_row_id("en", record) != source_row_id("da", record)


def test_dimension_vocabulary_mapping_is_explicit() -> None:
    assert normalize_dimension_axis("højde") == "height"
    assert normalize_dimension_axis("width") == "width"
    assert normalize_dimension_axis("omkreds") is None


def test_malformed_numeric_handling_is_not_silent() -> None:
    assert parse_strict_number("12.5") == (12.5, "numeric_text")
    assert parse_strict_number("12,5") == (None, "malformed_text")
    assert parse_strict_number(None) == (None, "missing")


def test_streaming_parser_preserves_large_json_integers(tmp_path: Path) -> None:
    source = tmp_path / "large-number.json"
    source.write_text('[{"id":"x","colortemp":2673963600000000000000000000}]')
    record = next(iter_source_records(source))
    assert record["colortemp"] == 2673963600000000000000000000


def test_parquet_round_trip_preserves_complete_records_and_duplicates(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    processed = tmp_path / "data" / "processed"
    raw.mkdir(parents=True)
    processed.mkdir(parents=True)
    source_path = raw / "fixture.json"
    source_path.write_bytes(FIXTURE.read_bytes())
    manifest = {
        "manifest_version": "test",
        "sources": [{
            "language": "da", "path": "data/raw/fixture.json", "sha256": "fixture",
            "record_count": 2,
        }],
    }

    state = ingest_source(tmp_path, "da", manifest, batch_size=1)
    rows = pq.read_table(tmp_path / "data" / "interim" / "source_da.parquet").to_pylist()

    assert state.object_counts["A1"] == 2
    assert len(rows) == 2
    assert json.loads(rows[0]["source_record_json"])["dimensions"][0]["value"] == "10"
    assert rows[0]["source_row_id"] != rows[1]["source_row_id"]
