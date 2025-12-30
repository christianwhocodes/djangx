from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.conf import settings

app_name = settings.APP["NAME"]
admin.site.site_header = _(f"{app_name} Admin")
admin.site.site_title = _(f"{app_name} Admin Portal")
admin.site.index_title = _(f"Welcome to {app_name} Admin")
