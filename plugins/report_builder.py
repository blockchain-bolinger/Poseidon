from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass
class ReportSection:
    title: str
    kind: str
    content: Any
    language: str = ""


@dataclass
class ReportBuilder:
    title: str
    metadata: list[tuple[str, str]] = field(default_factory=list)
    sections: list[ReportSection] = field(default_factory=list)

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata.append((str(key), self._stringify(value)))

    def add_table(self, title: str, rows: Iterable[Sequence[Any]], headers: Sequence[str]) -> None:
        self.sections.append(
            ReportSection(
                title=title,
                kind="table",
                content={
                    "headers": [str(header) for header in headers],
                    "rows": [[self._stringify(cell) for cell in row] for row in rows],
                },
            )
        )

    def add_bullets(self, title: str, items: Iterable[Any]) -> None:
        self.sections.append(
            ReportSection(
                title=title,
                kind="bullets",
                content=[self._stringify(item) for item in items],
            )
        )

    def add_code(self, title: str, content: Any, language: str = "") -> None:
        self.sections.append(
            ReportSection(
                title=title,
                kind="code",
                content=self._stringify(content),
                language=language,
            )
        )

    def add_text(self, title: str, content: Any) -> None:
        self.sections.append(
            ReportSection(
                title=title,
                kind="text",
                content=self._stringify(content),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "metadata": [{"key": key, "value": value} for key, value in self.metadata],
            "sections": [
                {
                    "title": section.title,
                    "kind": section.kind,
                    "language": section.language,
                    "content": section.content,
                }
                for section in self.sections
            ],
        }

    def render_markdown(self) -> str:
        lines: list[str] = [f"# {self.title}", ""]
        for key, value in self.metadata:
            lines.append(f"- **{self._escape_md(key)}:** `{self._escape_inline(value)}`")
        if self.metadata:
            lines.append("")
        for section in self.sections:
            lines.extend([f"## {section.title}", ""])
            if section.kind == "table":
                headers = section.content["headers"]
                rows = section.content["rows"]
                lines.append(self._render_table(headers, rows))
                lines.append("")
            elif section.kind == "bullets":
                for item in section.content:
                    lines.append(f"- {item}")
                lines.append("")
            elif section.kind == "code":
                lang = section.language or ""
                lines.append(f"```{lang}".rstrip())
                lines.append(section.content or "(keine Ausgabe)")
                lines.append("```")
                lines.append("")
            else:
                lines.append(section.content or "(keine Ausgabe)")
                lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def render_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"

    def write_markdown(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render_markdown(), encoding="utf-8")
        return path

    def write_json(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render_json(), encoding="utf-8")
        return path

    def write_bundle(self, base_path: Path) -> tuple[Path, Path]:
        md_path = base_path.with_suffix(".md")
        json_path = base_path.with_suffix(".json")
        return self.write_markdown(md_path), self.write_json(json_path)

    @staticmethod
    def _stringify(value: Any) -> str:
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _escape_md(value: str) -> str:
        return value.replace("|", "\\|")

    @staticmethod
    def _escape_inline(value: str) -> str:
        return value.replace("`", "\\`").replace("|", "\\|")

    @staticmethod
    def _render_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
        def cell(text: str) -> str:
            return text.replace("|", "\\|").replace("`", "\\`")

        header_line = "| " + " | ".join(cell(header) for header in headers) + " |"
        separator = "| " + " | ".join("---" for _ in headers) + " |"
        row_lines = ["| " + " | ".join(cell(cell_value) for cell_value in row) + " |" for row in rows]
        return "\n".join([header_line, separator, *row_lines])
