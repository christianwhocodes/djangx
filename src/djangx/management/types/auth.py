from typing import TypedDict

__all__: list[str] = ["PasswordValidatorDict"]


class PasswordValidatorDict(TypedDict):
    """Type definition for password validator configuration."""

    NAME: str
