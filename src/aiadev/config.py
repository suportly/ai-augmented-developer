"""Project-level configuration resolution for the aiadev framework.

Currently exposes one helper — ``resolve_terse_mode`` — that honours the
precedence mandated by spec 0009 (token-economy-terse-mode):

    AIADEV_TERSE env var  >  .claude/settings.json key aiadev.terseMode  >  default off
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

Source = Literal["default", "settings", "env"]

_SETTINGS_KEY = "aiadev.terseMode"
_ENV_VAR = "AIADEV_TERSE"
_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off", ""}


def resolve_terse_mode(settings_path: Path | None = None) -> tuple[bool, Source]:
    """Return ``(enabled, source)`` where ``source`` names which layer decided.

    ``source`` is ``"env"`` whenever ``AIADEV_TERSE`` is set (even to a
    falsy value — an explicit ``AIADEV_TERSE=0`` must beat a settings-level
    opt-in). ``"settings"`` only reports when the settings file positively
    enables terse-mode; a settings value of ``False`` collapses to the
    ``"default"`` source so the echo line stays honest about why the flag
    is off.
    """

    env = os.environ.get(_ENV_VAR)
    if env is not None:
        lowered = env.strip().lower()
        if lowered in _TRUTHY:
            return True, "env"
        if lowered in _FALSY:
            return False, "env"
        raise ValueError(
            f"Unrecognised {_ENV_VAR} value {env!r}; expected one of "
            f"{sorted(_TRUTHY | _FALSY)}"
        )

    if settings_path is not None and settings_path.exists():
        try:
            payload = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{settings_path} is not valid JSON: {exc.msg}"
            ) from exc

        raw = payload.get(_SETTINGS_KEY)
        if raw is not None:
            if not isinstance(raw, bool):
                raise ValueError(
                    f"{_SETTINGS_KEY} must be a JSON boolean; got {raw!r}"
                )
            if raw:
                return True, "settings"

    return False, "default"
