from __future__ import annotations

from pathlib import Path

import pytest

from core.app import AppContext
from core.device_manager import DeviceManager
from core.plugin_base import PluginBase
from utils.cli_safety import is_safe_device_input


def test_load_config_deepcopies_nested_defaults(tmp_path: Path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"global": {"monitor_stream_max_duration_s": 999}}',
        encoding="utf-8",
    )
    ctx = AppContext(config_path=config_path)
    first = ctx.load_config()
    assert first["global"]["monitor_stream_max_duration_s"] == 999
    assert first["devices"] == {}

    ctx_other = AppContext(config_path=config_path)
    second = ctx_other.load_config()
    second["global"]["monitor_stream_max_duration_s"] = 1
    second["devices"]["serial"] = {"name": "Pixel"}

    assert first["global"]["monitor_stream_max_duration_s"] == 999
    assert first["devices"] == {}
    assert ctx.config["global"]["monitor_stream_max_duration_s"] == 999
    assert ctx.config["devices"] == {}


def test_device_manager_wires_adb_through_constructor():
    adb_stub = object()
    dm = DeviceManager(adb=adb_stub)
    assert dm._adb is adb_stub
    assert dm._adb != object()


@pytest.mark.parametrize(
    "value,expected",
    [
        ("com.example.app", True),
        ("Post123", True),
        ("serial-01", True),
        ("path/to/pkg", True),
        ("", False),
        ("foo bar", False),
        ("rm -rf /", False),
        ("'; echo bad", False),
        ("$(whoami)", False),
    ],
)
def test_cli_safety_parametrized(value, expected):
    assert is_safe_device_input(value) is expected
