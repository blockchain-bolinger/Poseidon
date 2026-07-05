from __future__ import annotations

import pytest

from utils.cli_safety import is_safe_device_input, sanitize_device_input


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
        ("a" * 300, False),
    ],
)
def test_is_safe_device_input(value, expected):
    assert is_safe_device_input(value) is expected


def test_sanitize_device_input_normalizes():
    assert sanitize_device_input("package", "  com.example.app  ") == "com.example.app"
    assert sanitize_device_input("package", "; rm -rf /") is None
    assert sanitize_device_input("package", "") is None
