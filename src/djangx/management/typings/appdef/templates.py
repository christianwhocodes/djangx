"""Templates Type Definitions."""

from pathlib import Path
from typing import NotRequired, TypeAlias, TypedDict


class _TemplateOptionsDict(TypedDict):
    """Template OPTIONS dict."""

    context_processors: list[str]
    builtins: NotRequired[list[str]]
    libraries: NotRequired[dict[str, str]]


class _TemplateDict(TypedDict):
    """Single TEMPLATES entry."""

    BACKEND: str
    DIRS: list[Path]
    APP_DIRS: bool
    OPTIONS: _TemplateOptionsDict


TemplatesDict: TypeAlias = list[_TemplateDict]


__all__: list[str] = ["TemplatesDict"]
