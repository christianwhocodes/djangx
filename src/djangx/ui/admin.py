from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .. import PKG_DISPLAY_NAME
from .settings import ORG

_ORG_NAME: str = ORG.name or PKG_DISPLAY_NAME

admin.site.site_header = _(f"{_ORG_NAME} Admin")
admin.site.site_title = _(f"{_ORG_NAME} Admin Portal")
admin.site.index_title = _(f"Welcome to {_ORG_NAME} Admin")
