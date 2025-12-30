from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def contact_address() -> dict[str, str]:
    """
    Returns the complete contact address dictionary.

    Usage in template:
        {% contact_address as address %}
        {{ address.COUNTRY }}, {{ address.CITY }}
    """
    return settings.CONTACT["ADDRESS"]


@register.simple_tag
def contact_address_country() -> str:
    """Returns the contact address country."""
    return settings.CONTACT["ADDRESS"]["COUNTRY"]


@register.simple_tag
def contact_address_state() -> str:
    """Returns the contact address state."""
    return settings.CONTACT["ADDRESS"]["STATE"]


@register.simple_tag
def contact_address_city() -> str:
    """Returns the contact address city."""
    return settings.CONTACT["ADDRESS"]["CITY"]


@register.simple_tag
def contact_address_street() -> str:
    """Returns the contact address street."""
    return settings.CONTACT["ADDRESS"]["STREET"]


@register.simple_tag
def contact_email() -> dict[str, str | list[str]]:
    """
    Returns the complete contact email dictionary.

    Usage in template:
        {% contact_email as emails %}
        {{ emails.PRIMARY }}
        {% for email in emails.ADDITIONAL %}
            {{ email }}
        {% endfor %}
    """
    return settings.CONTACT["EMAIL"]


@register.simple_tag
def contact_email_primary() -> str:
    """Returns the primary contact email."""
    return settings.CONTACT["EMAIL"]["PRIMARY"]


@register.simple_tag
def contact_email_additional() -> list[str]:
    """Returns the list of additional contact emails."""
    return settings.CONTACT["EMAIL"]["ADDITIONAL"]


@register.simple_tag
def contact_phone() -> dict[str, str | list[str]]:
    """
    Returns the complete contact phone dictionary.

    Usage in template:
        {% contact_phone as phones %}
        {{ phones.PRIMARY }}
        {% for phone in phones.ADDITIONAL %}
            {{ phone }}
        {% endfor %}
    """
    return settings.CONTACT["PHONE"]


@register.simple_tag
def contact_phone_primary() -> str:
    """Returns the primary contact phone number."""
    return settings.CONTACT["PHONE"]["PRIMARY"]


@register.simple_tag
def contact_phone_additional() -> list[str]:
    """Returns the list of additional contact phone numbers."""
    return settings.CONTACT["PHONE"]["ADDITIONAL"]
