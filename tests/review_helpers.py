from pathlib import Path
from typing import List, Optional


def collect_python_files(base_dirs: List[Path]) -> List[Path]:
    files: List[Path] = []
    for base in base_dirs:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if path.name in {
                "_version.py",
                "version.py",
                "conftest.py",
                "examples.py",
                "example_script.json",
            }:
                continue
            files.append(path)
    return files


def iter_source_lines(path: Path) -> Optional[List[str]]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None
