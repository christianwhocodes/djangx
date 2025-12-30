from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

org_name = settings.ORG["name"]
admin.site.site_header = _(f"{org_name} Admin")
admin.site.site_title = _(f"{org_name} Admin Portal")
admin.site.index_title = _(f"Welcome to {org_name} Admin")
