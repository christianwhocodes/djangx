"""Preset enums."""

from enum import StrEnum

__all__: list[str] = ["PresetEnum"]


class PresetEnum(StrEnum):
    """Available project presets."""

    DEFAULT = "default"
    VERCEL = "vercel"
