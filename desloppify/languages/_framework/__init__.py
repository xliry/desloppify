"""Shared language-framework internals.

This package contains framework code used by all language plugins:
- config/runtime contracts
- plugin discovery/registration state
- shared detect-command factories
- shared issue factories and facade helpers
"""

from __future__ import annotations

from pathlib import Path

from .base.types import (
    BoundaryRule,
    DetectorPhase,
    FixerConfig,
    FixResult,
    LangConfig,
    LangValueSpec,
)


def make_lang_config(name: str, cfg_cls: type) -> LangConfig:
    from .resolution import make_lang_config as _make_lang_config

    return _make_lang_config(name, cfg_cls)


def get_lang(name: str, *, refresh_registry: bool = False) -> LangConfig:
    from .resolution import get_lang as _get_lang

    if not refresh_registry:
        return _get_lang(name)
    return _get_lang(name, refresh_registry=True)


def auto_detect_lang(
    project_root: Path,
    *,
    refresh_registry: bool = False,
) -> str | None:
    from .resolution import auto_detect_lang as _auto_detect_lang

    if not refresh_registry:
        return _auto_detect_lang(project_root)
    return _auto_detect_lang(project_root, refresh_registry=True)


def available_langs(*, refresh_registry: bool = False) -> list[str]:
    from .resolution import available_langs as _available_langs

    if not refresh_registry:
        return _available_langs()
    return _available_langs(refresh_registry=True)

__all__ = [
    "BoundaryRule",
    "DetectorPhase",
    "FixerConfig",
    "FixResult",
    "LangConfig",
    "LangValueSpec",
    "auto_detect_lang",
    "available_langs",
    "get_lang",
    "make_lang_config",
]
