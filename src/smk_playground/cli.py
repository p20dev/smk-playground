"""Command-line entrypoint for the SMK Playground pipeline."""

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


if __name__ == "__main__":
    app()
