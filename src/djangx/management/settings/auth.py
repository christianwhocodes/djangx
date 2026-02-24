"""Authentication and password validation settings."""

# ==============================================================================
# Authentication & Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators
# ==============================================================================
from typing import TypedDict, cast

__all__: list[str] = ["AUTH_PASSWORD_VALIDATORS"]


class _PasswordValidatorDict(TypedDict):
    """Password validator entry."""

    NAME: str


AUTH_PASSWORD_VALIDATORS: list[_PasswordValidatorDict] = cast(
    list[_PasswordValidatorDict],
    [
        {"NAME": f"django.contrib.auth.password_validation.{validator}"}
        for validator in [
            "UserAttributeSimilarityValidator",
            "MinimumLengthValidator",
            "CommonPasswordValidator",
            "NumericPasswordValidator",
        ]
    ],
)
