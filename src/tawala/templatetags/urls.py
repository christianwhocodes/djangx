from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def home_url() -> str:
    """Returns the home URL."""
    return settings.URLS["home"]
