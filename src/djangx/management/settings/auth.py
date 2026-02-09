"""Authentication and password validation settings."""

# ==============================================================================
# Authentication & Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators
# ==============================================================================
from typing import cast

from ..types import PasswordValidatorDict

__all__: list[str] = ["AUTH_PASSWORD_VALIDATORS"]


AUTH_PASSWORD_VALIDATORS: list[PasswordValidatorDict] = cast(
    list[PasswordValidatorDict],
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
