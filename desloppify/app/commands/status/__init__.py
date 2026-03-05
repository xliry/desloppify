"""Status command package."""

from importlib import import_module

__all__ = ["cmd_status"]


def __getattr__(name: str):
    if name == "cmd_status":
        return import_module(".cmd", __name__).cmd_status
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
