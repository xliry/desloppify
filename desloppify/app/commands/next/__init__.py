"""Next command package."""

from importlib import import_module

__all__ = ["cmd_next"]


def __getattr__(name: str):
    if name == "cmd_next":
        return import_module(".cmd", __name__).cmd_next
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
