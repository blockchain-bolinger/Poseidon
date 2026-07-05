from __future__ import annotations

from pathlib import Path

import pytest

from core.adb_handler import ADBHandler


def test_device_manager_runtime_wires_adb(tmp_path: Path):
    from core.app import AppContext

    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"version":"5.0-dev"}',
        encoding="utf-8",
    )
    ctx = AppContext(config_path=config_path)
    config = ctx.init_runtime()
    assert ctx.device_manager._adb is ctx.adb
    assert ctx.adb.device_manager is ctx.device_manager
