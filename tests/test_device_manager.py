from __future__ import annotations

import sys
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest

from core.adb_handler import ADBHandler


@pytest.fixture(autouse=True)
def _fake_subprocess_module(monkeypatch: pytest.MonkeyPatch):
    fake = ModuleType("subprocess")
    fake.run = MagicMock(return_value=MagicMock(stdout="", stderr="", returncode=0))
    fake.Popen = MagicMock()
    monkeypatch.setitem(sys.modules, "subprocess", fake)
    return fake


@pytest.fixture
def adb_handler():
    handler = ADBHandler.__new__(ADBHandler)
    handler.device_manager = None
    handler.cache_ttl = 0
    handler.default_timeout = 10
    handler.retries = 0
    handler._property_cache = {}
    handler._generic_cache = {}
    handler._last_serial = None
    return handler
