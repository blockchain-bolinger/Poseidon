from __future__ import annotations

from pathlib import Path

import pytest

from core.app import AppContext


@pytest.fixture
def app_context(tmp_path: Path):
    config_path = tmp_path / "config.json"
    return AppContext(config_path=config_path)


def test_default_config_returns_expected_shape(app_context: AppContext):
    config = app_context._defaults()
    assert config["version"] == "5.0-dev"
    assert config["language"] == "de"
    assert "global" in config
    assert "devices" in config


def test_load_config_creates_defaults_when_missing(app_context: AppContext):
    config = app_context.load_config()
    assert config["version"] == "5.0-dev"
    assert config["language"] == "de"


def test_load_config_preserves_devices(app_context: AppContext, tmp_path: Path):
    tmp_path.joinpath("config.json").write_text(
        '{"version":"5.0-dev","language":"de","global":{"backup_path":"./backups"},"devices":{"serial":{"name":"Pixel"}}}',
        encoding="utf-8",
    )
    config = app_context.load_config()
    assert config["devices"] == {"serial": {"name": "Pixel"}}


def test_ensure_runtime_dirs_creates_target_directories(app_context: AppContext, tmp_path: Path):
    app_context.config = app_context._defaults()
    app_context.config["global"]["backup_path"] = str(tmp_path / "backups")
    app_context.config["global"]["screenshot_path"] = str(tmp_path / "screenshots")
    app_context.config["global"]["log_path"] = str(tmp_path / "logs")
    app_context.ensure_runtime_dirs()
    assert (tmp_path / "backups").exists()
    assert (tmp_path / "screenshots").exists()
    assert (tmp_path / "logs").exists()
    assert (tmp_path / "plugins").exists()
