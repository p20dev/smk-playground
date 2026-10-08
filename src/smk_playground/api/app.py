"""FastAPI application serving the API and built React frontend."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from smk_playground.api.catalog import Catalog


def repository_root() -> Path:
    configured = os.environ.get("SMK_ROOT")
    return Path(configured).resolve() if configured else Path.cwd().resolve()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.catalog = Catalog(repository_root())
    yield


app = FastAPI(title="SMK Playground API", version="1.0.0", lifespan=lifespan)


def catalog() -> Catalog:
    return app.state.catalog


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "catalog_rows": len(catalog().rows)}


@app.get("/api/stats")
def stats() -> dict[str, Any]:
    return catalog().stats()


@app.get("/api/artworks")
def artworks(
    q: str = "", limit: int = Query(24, ge=1, le=100), offset: int = Query(0, ge=0),
    classification: str | None = None, has_physical: bool | None = None,
    chromatic: bool | None = None,
) -> dict[str, Any]:
    return catalog().search(q, limit, offset, classification, has_physical, chromatic)


@app.get("/api/artworks/random")
def random_artwork(seed: int | None = None) -> dict[str, Any]:
    return catalog().random(seed)


@app.get("/api/resolve/{object_number}")
def resolve_object_number(object_number: str) -> dict[str, Any]:
    matches = catalog().resolve(object_number)
    if not matches:
        raise HTTPException(404, "Object number not found in corpus")
    return {"object_number": object_number, "ambiguous": len(matches) > 1, "items": matches}


@app.get("/api/artworks/{entity_id}/similar")
def similar_artworks(entity_id: str, profile: str = "color",
                     limit: int = Query(10, ge=1, le=50)) -> dict[str, Any]:
    if profile not in {"color", "visual", "geometry", "weighted-color"}:
        raise HTTPException(400, "Unknown similarity profile")
    try:
        return catalog().similar(entity_id, profile, limit)
    except KeyError:
        raise HTTPException(404, "Artwork not found") from None
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@app.get("/api/artworks/{entity_id}")
def artwork(entity_id: str) -> dict[str, Any]:
    try:
        return catalog().artwork(entity_id)
    except KeyError:
        raise HTTPException(404, "Artwork not found") from None


frontend = repository_root() / "web" / "dist"
if frontend.exists():
    app.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend_route(full_path: str) -> FileResponse:
        candidate = frontend / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(frontend / "index.html")
