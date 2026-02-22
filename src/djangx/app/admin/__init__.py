"""Admin configuration."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ... import PACKAGE
from .contactinfo import *
from .org import *
from .socialurls import *

admin.site.site_header = _(f"{PACKAGE.display_name} Admin")
admin.site.site_title = _(f"{PACKAGE.display_name} Admin Portal")
admin.site.index_title = _(f"Welcome to {PACKAGE.display_name} Admin")
