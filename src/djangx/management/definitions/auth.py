"""Authentication type definitions."""

from typing import TypedDict

__all__: list[str] = ["PasswordValidatorDict"]


class PasswordValidatorDict(TypedDict):
    """Password validator entry."""

    NAME: str
