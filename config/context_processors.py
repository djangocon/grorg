from __future__ import annotations

from config import __version__


def version(request) -> dict:
    return {
        "APP_VERSION": __version__,
    }
