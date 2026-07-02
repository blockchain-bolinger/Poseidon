from __future__ import annotations

import json

from plugins.report_builder import ReportBuilder


def test_report_builder_renders_markdown_and_json(tmp_path):
    builder = ReportBuilder("Demo Report")
    builder.add_metadata("Gerät", "SERIAL-1")
    builder.add_table("Facts", [("Model", "X"), ("SDK", 33)], headers=("Key", "Value"))
    builder.add_bullets("Notes", ["alpha", "beta"])
    builder.add_code("Snapshot", "line1\nline2")
    builder.add_text("Summary", "done")

    md_path, json_path = builder.write_bundle(tmp_path / "demo_report")

    md = md_path.read_text(encoding="utf-8")
    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert md_path.name == "demo_report.md"
    assert json_path.name == "demo_report.json"
    assert "# Demo Report" in md
    assert "| Key | Value |" in md
    assert "- **Gerät:** `SERIAL-1`" in md
    assert data["title"] == "Demo Report"
    assert data["metadata"][0]["value"] == "SERIAL-1"
    assert data["sections"][0]["kind"] == "table"
