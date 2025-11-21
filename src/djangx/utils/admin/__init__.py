"""
Django admin site customizations.
"""

from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext_lazy as _


def configure_admin_site():
    """Configure global admin site settings."""
    site_name = getattr(settings, "SITE_NAME", "").strip()
    admin.site.site_header = _(f"{site_name} Admin")
    admin.site.site_title = _(f"{site_name} Admin Portal")
    admin.site.index_title = _(f"Welcome to {site_name} Admin")


# configure_admin_site()
