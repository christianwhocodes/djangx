"""Installed apps, middleware, and template settings."""

from pathlib import Path
from typing import NotRequired, TypeAlias, TypedDict

from ...enums import TemplateContextProcessorEnum
from ...mappings import APP_TEMPLATE_CONTEXT_PROCESSOR_MAP
from ..base import BaseConf, ConfField
from .installed_apps import INSTALLED_APPS


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


_TemplatesDict: TypeAlias = list[_TemplateDict]


class _TemplateContextProcessorsConf(BaseConf):
    """Context processors settings."""

    extend = ConfField(
        type=list,
        env="CONTEXT_PROCESSORS_EXTEND",
        toml="context-processors.extend",
        default=[],
    )
    remove = ConfField(
        type=list,
        env="CONTEXT_PROCESSORS_REMOVE",
        toml="context-processors.remove",
        default=[],
    )


_TEMPLATE_CONTEXT_PROCESSORS_CONF = _TemplateContextProcessorsConf()


def _get_template_context_processors(installed_apps: list[str]) -> list[str]:
    """Build the final context processors list based on installed apps."""
    # contrib context processors in recommended order
    contrib_context_processors: list[str] = [
        TemplateContextProcessorEnum.DEBUG,  # Debug info (only in DEBUG mode)
        TemplateContextProcessorEnum.REQUEST,  # Adds request object to context
        TemplateContextProcessorEnum.AUTH,  # Adds user and perms to context
        TemplateContextProcessorEnum.MESSAGES,  # Adds messages to context
        TemplateContextProcessorEnum.CSP,  # Content Security Policy
    ]

    # Collect context processors that should be removed based on missing apps
    context_processors_to_remove: set[str] = set(_TEMPLATE_CONTEXT_PROCESSORS_CONF.remove)
    for app, processor_list in APP_TEMPLATE_CONTEXT_PROCESSOR_MAP.items():
        if app not in installed_apps:
            context_processors_to_remove.update(processor_list)

    # Filter out context processors whose apps are not installed or explicitly removed
    contrib_context_processors: list[str] = [
        cp for cp in contrib_context_processors if cp not in context_processors_to_remove
    ]

    # Add custom context processors at the end
    all_context_processors: list[str] = (
        _TEMPLATE_CONTEXT_PROCESSORS_CONF.extend + contrib_context_processors
    )

    # Remove duplicates while preserving order
    return list(dict.fromkeys(all_context_processors))


TEMPLATES: _TemplatesDict = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": _get_template_context_processors(INSTALLED_APPS),
        },
    },
]


__all__: list[str] = ["TEMPLATES"]
