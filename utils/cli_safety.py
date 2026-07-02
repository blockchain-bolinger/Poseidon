from __future__ import annotations

import re
from typing import Optional


_SAFE_CLI_INPUT_RE = re.compile(r"^[A-Za-z0-9_./:@()+-]{1,200}$")


def is_safe_device_input(value: str) -> bool:
    return bool(_SAFE_CLI_INPUT_RE.fullmatch(value))


def sanitize_device_input(name: str, value: str) -> Optional[str]:
    safe = value.strip()
    if not safe or not is_safe_device_input(safe):
        return None
    return safe
