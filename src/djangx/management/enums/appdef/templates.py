"""App, context processor, and middleware enums."""

from enum import StrEnum

from .... import PACKAGE


class TemplateContextProcessorEnum(StrEnum):
    """Template context processors."""

    DEBUG = "django.template.context_processors.debug"
    REQUEST = "django.template.context_processors.request"
    AUTH = "django.contrib.auth.context_processors.auth"
    MESSAGES = "django.contrib.messages.context_processors.messages"
    CSP = "django.template.context_processors.csp"
    TAILWINDCSS = f"{PACKAGE.name}.management.context_processors.tailwindcss"


__all__: list[str] = ["TemplateContextProcessorEnum"]
