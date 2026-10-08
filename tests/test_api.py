"""Focused API acceptance tests over the frozen processed artifacts."""

import pytest
from fastapi.testclient import TestClient

from smk_playground.api.app import app


def test_health_search_and_kms8892_detail():
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["catalog_rows"] > 0

        search = client.get("/api/artworks", params={"q": "KMS8892", "limit": 5}).json()
        assert search["total"] >= 1
        match = next(item for item in search["items"] if item["object_number"] == "KMS8892")

        detail = client.get(f"/api/artworks/{match['smk_entity_id']}")
        assert detail.status_code == 200
        payload = detail.json()
        assert payload["weighted_palette"]
        assert sum(item["weight"] for item in payload["weighted_palette"]) == pytest.approx(1.0)
        assert payload["sonification"]["weighted_color"]["available"]


def test_not_found_and_profile_validation():
    with TestClient(app) as client:
        assert client.get("/api/artworks/not-an-id").status_code == 404
        response = client.get("/api/artworks/not-an-id/similar", params={"profile": "invented"})
        assert response.status_code == 400
