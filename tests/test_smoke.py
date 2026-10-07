from typer.testing import CliRunner

from smk_playground.cli import app


def test_status_command() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "smk playground pipeline skeleton is ready" in result.stdout.lower()
    assert "smk_all_da.json" in result.stdout
    assert "smk_all_en.json" in result.stdout
