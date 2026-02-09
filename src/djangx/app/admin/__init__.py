"""Admin configuration."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ... import PACKAGE
from .contactinfo import *  # noqa: F403
from .org import *  # noqa: F403
from .socialurls import *  # noqa: F403

admin.site.site_header = _(f"{PACKAGE.display_name} Admin")
admin.site.site_title = _(f"{PACKAGE.display_name} Admin Portal")
admin.site.index_title = _(f"Welcome to {PACKAGE.display_name} Admin")
