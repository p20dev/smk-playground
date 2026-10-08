"""Command-line entrypoint for the SMK Playground pipeline."""

import json
from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True, help="SMK visual-feature pipeline")


@app.command()
def status() -> None:
    """Show expected source paths and repository readiness."""
    expected = [
        Path("data/raw/smk_all_da.json"),
        Path("data/raw/smk_all_en.json"),
    ]
    typer.echo("SMK Playground pipeline skeleton is ready.")
    for path in expected:
        typer.echo(f"{'FOUND' if path.exists() else 'MISSING'}  {path}")


@app.command("milestone1")
def milestone1(root: Path | None = None) -> None:
    """Build manifest-bound source Parquets and Milestone 1 audits."""
    from smk_playground.ingest.milestone1 import run

    summary = run((root or Path.cwd()).resolve())
    typer.echo(f"Milestone 1 complete: {summary['source_rows']}")


@app.command("milestone2")
def milestone2(root: Path | None = None) -> None:
    """Build canonical SMK entities and freeze smk-public-visual-v1."""
    from smk_playground.canonical.milestone2 import run

    summary = run((root or Path.cwd()).resolve())
    typer.echo(f"Milestone 2 complete: {summary['canonical_entity_count']} entities")


@app.command("milestone3")
def milestone3(root: Path | None = None) -> None:
    """Build deterministic per-artwork visual features for the frozen corpus."""
    from smk_playground.features.milestone3 import run

    summary = run((root or Path.cwd()).resolve())
    typer.echo(f"Milestone 3 complete: {summary['feature_rows']} feature rows")


@app.command("milestone4")
def milestone4(root: Path | None = None) -> None:
    """Build corpus-relative normalized features and candidate feature families."""
    from smk_playground.normalize.milestone4 import run

    summary = run((root or Path.cwd()).resolve())
    typer.echo(f"Milestone 4 complete: {summary['row_count']} normalized rows")


@app.command("milestone5")
def milestone5(root: Path | None = None) -> None:
    """Build exact deterministic similarity profiles and diagnostics."""
    from smk_playground.similarity.milestone5 import run

    summary = run((root or Path.cwd()).resolve())
    typer.echo(f"Milestone 5 complete: {summary['eligible_counts']}")


@app.command("similar")
def similar(
    object_number: str | None = typer.Argument(None, help="SMK object number"),
    smk_entity_id: str | None = typer.Option(None, "--id", help="Canonical SMK entity ID"),
    profile: str = typer.Option("color", help="color, visual, or geometry"),
    limit: int = typer.Option(10, min=1, max=100),
    include_self: bool = typer.Option(False, help="Include the query entity for debugging"),
    root: Path | None = None,
) -> None:
    """Run an exact similarity query over the frozen corpus."""
    from smk_playground.similarity.engine import SimilarityEngine

    try:
        query, results = SimilarityEngine((root or Path.cwd()).resolve()).search(
            profile_name=profile, limit=limit, smk_entity_id=smk_entity_id,
            object_number=object_number, include_self=include_self,
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps({
        "query": {"smk_entity_id": query["smk_entity_id"],
                  "object_number": query["object_number"]},
        "profile": profile, "results": results,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
