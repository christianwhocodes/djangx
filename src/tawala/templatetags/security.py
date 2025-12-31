from django.conf import settings
from django.template import Library

register = Library()


@register.simple_tag
def is_debug_mode() -> bool:
    """Returns True if DEBUG mode is enabled."""
    return bool(settings.SECURITY["debug"])


@register.simple_tag
def security_setting(key: str) -> str | bool | list[str] | int | None:
    """
    Get a value from the SECURITY dictionary.

    Usage: {% security_setting 'secure_ssl_redirect' %}
    """
    return settings.SECURITY.get(key)


@register.filter
def mask_secret(value: str | None, visible_chars: int = 4) -> str:
    """
    Mask a secret value, showing only the last N characters.

    This is useful for displaying sensitive information (like API keys, tokens,
    or secret keys) in admin panels, logs, or debug pages without exposing the
    full value.

    Examples:
        {{ "sk-1234567890abcdef"|mask_secret:4 }}
        Output: "************cdef"

        {{ user.api_token|mask_secret:6 }}
        Output: "*************token_suffix"

    Common use cases:
    - Showing partial credit card numbers: **** **** **** 1234
    - Displaying API keys in user dashboards: ****************a7f3
    - Debug pages showing config without exposing secrets
    - Audit logs that need to reference keys without revealing them

    Usage: {{ secret_value|mask_secret:4 }}
    """
    if not value:
        return ""

    value_str = str(value)
    if len(value_str) <= visible_chars:
        return "*" * len(value_str)

    return "*" * (len(value_str) - visible_chars) + value_str[-visible_chars:]
