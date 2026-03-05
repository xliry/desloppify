"""Shared move helpers for scaffold-style language plugins."""

from __future__ import annotations

from desloppify.languages._framework import commands_base as commands_base_mod


def find_replacements(
    source_abs: str,
    dest_abs: str,
    graph: dict,
) -> dict[str, list[tuple[str, str]]]:
    """Default replacement mapping for scaffolded languages."""
    return commands_base_mod.scaffold_find_replacements(source_abs, dest_abs, graph)


def find_self_replacements(
    source_abs: str,
    dest_abs: str,
    graph: dict,
) -> list[tuple[str, str]]:
    """Default self-replacement mapping for scaffolded languages."""
    return commands_base_mod.scaffold_find_self_replacements(source_abs, dest_abs, graph)


def get_verify_hint() -> str:
    """Return the default post-move verification command."""
    return commands_base_mod.scaffold_verify_hint()

__all__ = ["find_replacements", "find_self_replacements", "get_verify_hint"]
