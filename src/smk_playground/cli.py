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


if __name__ == "__main__":
    app()
