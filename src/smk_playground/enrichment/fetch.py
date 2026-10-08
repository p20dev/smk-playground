"""Polite, resumable enrichment retrieval for the frozen corpus."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any

import pyarrow.parquet as pq

ENDPOINT = "https://enrichment.api.smk.dk/api/enrichment/{object_number}"
USER_AGENT = "smk-playground/0.1 enrichment-research"
STATE_VERSION = "1.0.0"


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _safe_key(object_number: str) -> str:
    return hashlib.sha256(object_number.encode("utf-8")).hexdigest()


def corpus_targets(root: Path) -> tuple[list[str], dict[str, list[str]]]:
    path = root / "data" / "processed" / "smk-public-visual-v1.parquet"
    rows = pq.read_table(path, columns=["smk_entity_id", "object_number"]).to_pylist()
    mapping: dict[str, list[str]] = {}
    for row in rows:
        number = row["object_number"]
        if not number:
            raise ValueError(f"Corpus entity lacks object_number: {row['smk_entity_id']}")
        mapping.setdefault(number, []).append(row["smk_entity_id"])
    return sorted(mapping), {key: sorted(value) for key, value in mapping.items()}


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"state_version": STATE_VERSION, "records": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(path: Path, state: dict[str, Any]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _fetch_one(object_number: str, cache_dir: Path, delay: float, retries: int) -> dict[str, Any]:
    endpoint = ENDPOINT.format(object_number=urllib.parse.quote(object_number, safe=""))
    outcome: dict[str, Any] | None = None
    for attempt in range(retries + 1):
        if delay:
            time.sleep(delay)
        requested_at = _timestamp()
        try:
            request = urllib.request.Request(endpoint, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                status_code = response.status
            parsed = json.loads(body)
            outcome = {
                "object_number": object_number, "requested_at_utc": requested_at,
                "response_at_utc": _timestamp(), "endpoint": endpoint,
                "http_status": status_code, "outcome": "success",
                "attempt": attempt + 1, "response_json": parsed,
            }
            break
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            category = "not_found" if error.code == 404 else "http_failure"
            outcome = {
                "object_number": object_number, "requested_at_utc": requested_at,
                "response_at_utc": _timestamp(), "endpoint": endpoint,
                "http_status": error.code, "outcome": category,
                "attempt": attempt + 1, "response_body": body,
            }
            if error.code < 500:
                break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            outcome = {
                "object_number": object_number, "requested_at_utc": requested_at,
                "response_at_utc": _timestamp(), "endpoint": endpoint,
                "http_status": None, "outcome": "transport_failure",
                "attempt": attempt + 1, "error": repr(error),
            }
        if attempt < retries:
            time.sleep(0.5 * (2 ** attempt))
    assert outcome is not None
    stamp = outcome["response_at_utc"].replace(":", "").replace("-", "")
    record_dir = cache_dir / _safe_key(object_number)
    record_dir.mkdir(parents=True, exist_ok=True)
    path = record_dir / f"{stamp}.json"
    path.write_text(json.dumps(outcome, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    outcome["cache_path"] = path.as_posix()
    return outcome


def fetch(
    root: Path,
    *,
    limit: int | None = None,
    resume: bool = True,
    refresh: bool = False,
    concurrency: int = 2,
    delay: float = 0.2,
    retries: int = 2,
) -> dict[str, Any]:
    if concurrency < 1 or concurrency > 16:
        raise ValueError("concurrency must be between 1 and 16")
    targets, entity_mapping = corpus_targets(root)
    cache_dir = root / "data" / "raw" / "enrichment"
    cache_dir.mkdir(parents=True, exist_ok=True)
    state_path = cache_dir / "fetch-state-v1.json"
    state = _load_state(state_path)
    state["corpus_entity_count"] = sum(len(value) for value in entity_mapping.values())
    state["unique_object_number_count"] = len(targets)
    state["duplicate_object_number_groups"] = sum(len(value) > 1 for value in entity_mapping.values())
    state["entity_mapping"] = entity_mapping
    records = state.setdefault("records", {})
    selected = []
    for object_number in targets:
        prior = records.get(object_number)
        if resume and not refresh and prior and prior.get("outcome") == "success":
            continue
        selected.append(object_number)
    if limit is not None:
        selected = selected[:limit]
    lock = Lock()
    completed = 0
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(_fetch_one, number, cache_dir, delay, retries): number
            for number in selected
        }
        for future in as_completed(futures):
            result = future.result()
            with lock:
                records[result["object_number"]] = {
                    key: result.get(key) for key in (
                        "outcome", "http_status", "response_at_utc", "attempt", "cache_path"
                    )
                }
                completed += 1
                if completed % 25 == 0 or completed == len(selected):
                    state["updated_at_utc"] = _timestamp()
                    _save_state(state_path, state)
    state["updated_at_utc"] = _timestamp()
    _save_state(state_path, state)
    return status(root) | {"fetched_this_run": completed}


def status(root: Path) -> dict[str, Any]:
    targets, mapping = corpus_targets(root)
    state_path = root / "data" / "raw" / "enrichment" / "fetch-state-v1.json"
    state = _load_state(state_path)
    counts: dict[str, int] = {}
    for record in state.get("records", {}).values():
        outcome = record.get("outcome", "unknown")
        counts[outcome] = counts.get(outcome, 0) + 1
    return {
        "corpus_entities": sum(len(value) for value in mapping.values()),
        "unique_object_numbers": len(targets),
        "duplicate_object_number_groups": sum(len(value) > 1 for value in mapping.values()),
        "cached_records": len(state.get("records", {})), "outcomes": dict(sorted(counts.items())),
        "remaining": len(targets) - sum(
            record.get("outcome") == "success" for record in state.get("records", {}).values()
        ),
    }


def cached_record(root: Path, object_number: str) -> dict[str, Any]:
    state = _load_state(root / "data" / "raw" / "enrichment" / "fetch-state-v1.json")
    record = state.get("records", {}).get(object_number)
    if not record:
        raise ValueError(f"No cached enrichment response for {object_number}")
    path = Path(record["cache_path"])
    if not path.is_absolute():
        path = root / path
    return json.loads(path.read_text(encoding="utf-8"))
